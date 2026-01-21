from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import openai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.openai_client import OpenAIClient
from app.telegram import TelegramClient, extract_message, parse_user_message

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OWNER_TELEGRAM_ID = os.getenv("OWNER_TELEGRAM_ID", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")
IMAGE_VIBE = os.getenv("IMAGE_VIBE", "clean").lower()

if not TELEGRAM_BOT_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN is not set")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set")
if not OWNER_TELEGRAM_ID:
    logger.warning("OWNER_TELEGRAM_ID is not set")

logger.info("OpenAI SDK version: %s", openai.__version__)

telegram_client = TelegramClient(TELEGRAM_BOT_TOKEN)
openai_client = OpenAIClient(OPENAI_API_KEY)


def _owner_id() -> Optional[int]:
    try:
        return int(OWNER_TELEGRAM_ID)
    except (TypeError, ValueError):
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    if PUBLIC_BASE_URL:
        webhook_url = f"{PUBLIC_BASE_URL.rstrip('/')}/telegram/webhook"
        try:
            response = await telegram_client.set_webhook(webhook_url)
            logger.info("Webhook setup response: %s", response)
        except Exception as exc:
            logger.error("Failed to set webhook: %s", exc)
    else:
        logger.warning("PUBLIC_BASE_URL not set; webhook not configured")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/debug/chat-id")
async def debug_chat_id() -> dict:
    return {
        "instruction": (
            "Send any message to the Telegram bot, then check Railway logs for "
            "TELEGRAM DEBUG — chat_id=..."
        )
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    payload = await request.json()
    raw_message = payload.get("message") or payload.get("edited_message")
    if not raw_message or not isinstance(raw_message, dict):
        return JSONResponse({"status": "ignored"})
    chat = raw_message.get("chat", {})
    from_user = raw_message.get("from", {})
    chat_id = chat.get("id")
    user_id = from_user.get("id")
    username = from_user.get("username") or "unknown"
    chat_type = chat.get("type")
    logger.warning(
        "TELEGRAM DEBUG — chat_id=%s user_id=%s username=%s chat_type=%s",
        chat_id,
        user_id,
        username,
        chat_type,
    )
    message = extract_message(payload)
    if not message:
        return JSONResponse({"status": "ignored"})
    logger.info("Incoming message id=%s from=%s", message.message_id, message.from_user_id)

    owner_id = _owner_id()
    if owner_id is None:
        logger.warning("OWNER_TELEGRAM_ID not set — running in open debug mode")
        await telegram_client.send_message(
            message.chat_id,
            "Debug mode: check Railway logs to get your chat_id, then set OWNER_TELEGRAM_ID",
        )
        return JSONResponse({"status": "debug"})

    if message.chat_type != "private":
        logger.info("Ignoring non-private chat type=%s", message.chat_type)
        return JSONResponse({"status": "ignored"})

    if message.from_user_id != owner_id:
        await telegram_client.send_message(message.chat_id, "Not authorized.")
        return JSONResponse({"status": "unauthorized"})

    prompt, lyrics = parse_user_message(message.text)
    if len(prompt) < 10 or len(lyrics) < 50:
        usage = "Send PROMPT and LYRICS. Example:\nPROMPT: ...\nLYRICS: ..."
        await telegram_client.send_message(message.chat_id, usage)
        return JSONResponse({"status": "invalid"})

    try:
        title = openai_client.generate_title(prompt, lyrics)
    except Exception as exc:
        logger.error("Title generation failed: %s", exc)
        await telegram_client.send_message(message.chat_id, "Failed to generate title. Try again.")
        return JSONResponse({"status": "error"})

    logger.info("Generated title: %s", title)
    await telegram_client.send_message(message.chat_id, title)

    try:
        image_bytes = openai_client.generate_thumbnail(title=title, vibe=IMAGE_VIBE)
        await telegram_client.send_photo(message.chat_id, image_bytes, caption=title)
        logger.info("Thumbnail sent")
    except Exception as exc:
        logger.error("Image generation failed: %s", exc)
        await telegram_client.send_message(
            message.chat_id, f"Title: {title}\nImage generation failed. Try again."
        )

    return JSONResponse({"status": "ok"})

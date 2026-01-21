from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramMessage:
    chat_id: int
    message_id: int
    chat_type: str
    text: str
    from_user_id: int


class TelegramClient:
    def __init__(self, token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def send_message(self, chat_id: int, text: str) -> None:
        payload = {"chat_id": chat_id, "text": text}
        await self._post("/sendMessage", data=payload)

    async def send_photo(self, chat_id: int, photo_bytes: bytes, caption: Optional[str] = None) -> None:
        data = {"chat_id": str(chat_id)}
        if caption:
            data["caption"] = caption
        files = {"photo": ("thumbnail.jpg", photo_bytes, "image/jpeg")}
        await self._post("/sendPhoto", data=data, files=files)

    async def set_webhook(self, url: str) -> dict:
        payload = {"url": url}
        return await self._post("/setWebhook", data=payload)

    async def _post(self, path: str, data: dict, files: Optional[dict] = None) -> dict:
        retries = 3
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.base_url}{path}", data=data, files=files)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                logger.warning("Telegram request failed (attempt %s/%s): %s", attempt, retries, exc)
                if attempt == retries:
                    raise
        return {}


def parse_user_message(text: str) -> Tuple[str, str]:
    prompt_marker = re.search(r"PROMPT:\s*", text, flags=re.IGNORECASE)
    lyrics_marker = re.search(r"LYRICS:\s*", text, flags=re.IGNORECASE)
    if prompt_marker and lyrics_marker:
        prompt_start = prompt_marker.end()
        lyrics_start = lyrics_marker.end()
        if lyrics_start < prompt_start:
            prompt_start, lyrics_start = lyrics_start, prompt_start
        prompt = text[prompt_start:lyrics_marker.start()].strip()
        lyrics = text[lyrics_start:].strip()
        return prompt, lyrics
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    prompt = lines[0]
    lyrics = "\n".join(lines[1:]).strip()
    return prompt, lyrics


def extract_message(payload: dict) -> Optional[TelegramMessage]:
    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return None
    chat = message.get("chat", {})
    from_user = message.get("from", {})
    text = message.get("text") or ""
    if not chat or not from_user:
        return None
    return TelegramMessage(
        chat_id=chat.get("id"),
        message_id=message.get("message_id"),
        chat_type=chat.get("type", ""),
        text=text,
        from_user_id=from_user.get("id"),
    )

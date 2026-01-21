from __future__ import annotations

import base64
import json
import logging
import re
import string
from typing import Any

import httpx
from openai import OpenAI

from app.prompts import build_image_prompt

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str) -> None:
        self.client = OpenAI(api_key=api_key)

    def generate_title(self, prompt: str, lyrics: str) -> str:
        system_message = (
            "You are a music branding assistant. "
            "Return JSON only with fields: title, language, reason_short. "
            "Title must be 1-2 words, no punctuation, no quotes."
        )
        user_message = (
            f"Song prompt: {prompt}\n\nLyrics:\n{lyrics}\n\n"
            "Respond with JSON only."
        )
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        title = self._extract_title_from_json(content)
        return self._sanitize_title(title)

    def generate_thumbnail(self, title: str, vibe: str) -> bytes:
        prompt = build_image_prompt(title=title, vibe=vibe)
        final_prompt = f"{prompt.prompt}\n\nNEGATIVE PROMPT: {prompt.negative_prompt}"
        response = self.client.images.generate(
            model="gpt-image-1",
            prompt=final_prompt,
            size="1792x1024",
            response_format="b64_json",
        )
        data = response.data[0]
        if getattr(data, "b64_json", None):
            return base64.b64decode(data.b64_json)
        if getattr(data, "url", None):
            return self._download_image(data.url)
        raise ValueError("OpenAI image response missing data")

    def _download_image(self, url: str) -> bytes:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content

    def _extract_title_from_json(self, content: str) -> str:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from OpenAI response; content=%s", content)
            return content
        if isinstance(data, dict):
            return str(data.get("title", ""))
        return ""

    def _sanitize_title(self, title: str) -> str:
        cleaned = title.strip()
        cleaned = re.sub(r"[\"\'“”‘’]", "", cleaned)
        cleaned = cleaned.translate(str.maketrans("", "", string.punctuation))
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return "Untitled"
        words = cleaned.split(" ")
        if len(words) <= 2:
            return cleaned
        ranked = sorted(
            ((len(word), index, word) for index, word in enumerate(words)),
            key=lambda item: (-item[0], item[1]),
        )
        chosen = sorted(ranked[:2], key=lambda item: item[1])
        return " ".join(word for _, _, word in chosen)

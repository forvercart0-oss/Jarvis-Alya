"""Gemini image generation provider (via Gemini API)."""

from __future__ import annotations

import httpx
import logging
import os
from typing import Any, Optional

from generation.image.provider import ImageGenerationProvider
from config.settings import get_settings

logger = logging.getLogger("jarvis.generation.image.gemini")


class GeminiImageProvider(ImageGenerationProvider):
    name = "gemini"
    tier = "paid"

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._api_key = getattr(self.settings, "gemini_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        self._base = "https://generativelanguage.googleapis.com/v1beta"
        self._model = getattr(self.settings, "gemini_model", "gemini-2.0-flash") or "gemini-2.0-flash"

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def generate(self, prompt: str, **kwargs) -> dict:
        if not self._api_key:
            return {"success": False, "error": "Gemini API key not configured."}
        url = f"{self._base}/models/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT"],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {
                        "success": True,
                        "provider": self.name,
                        "data": data,
                        "text": text,
                        "urls": [],
                    }
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            logger.warning("Gemini image generation error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def edit(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        return {"success": False, "error": "Image editing not supported by Gemini text provider."}

    async def image_to_image(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        return {"success": False, "error": "Image-to-image not supported by Gemini text provider."}

    async def health_check(self) -> dict:
        if not self._api_key:
            return {"status": "not_configured", "provider": self.name, "tier": self.tier}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._base}/models?key={self._api_key}")
                if resp.status_code == 200:
                    return {"status": "online", "provider": self.name, "tier": self.tier}
                return {"status": "error", "provider": self.name, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"status": "offline", "provider": self.name, "error": str(exc)}

    async def list_models(self) -> list[str]:
        return [self._model]

"""Pixazo image generation provider.

Pixazo offers free-tier image generation.
"""

from __future__ import annotations

import httpx
import logging
import os
from typing import Any, Optional

from generation.image.provider import ImageGenerationProvider
from config.settings import get_settings

logger = logging.getLogger("jarvis.generation.image.pixazo")


class PixazoImageProvider(ImageGenerationProvider):
    name = "pixazo"
    tier = "free"

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._api_key = getattr(self.settings, "pixazo_api_key", "") or os.environ.get("PIXAZO_API_KEY", "")
        self._base = "https://api.pixazo.ai/v1"

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def generate(self, prompt: str, **kwargs) -> dict:
        if not self._api_key:
            return {"success": False, "error": "Pixazo API key not configured."}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "prompt": prompt,
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 1024),
            "num_images": kwargs.get("count", 1),
            "negative_prompt": kwargs.get("negative_prompt", ""),
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base}/images/generate", json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "success": True,
                        "provider": self.name,
                        "data": data,
                        "urls": [item.get("url") for item in data.get("images", []) if item.get("url")],
                    }
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            logger.warning("Pixazo image generation error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def edit(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        if not self._api_key:
            return {"success": False, "error": "Pixazo API key not configured."}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        files = {"image": ("input.png", image_data, "image/png")}
        data = {"prompt": prompt}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base}/images/edit", files=files, data=data, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {"success": True, "provider": self.name, "data": data}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            logger.warning("Pixazo image edit error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def image_to_image(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        return await self.edit(image_data, prompt, **kwargs)

    async def health_check(self) -> dict:
        if not self._api_key:
            return {"status": "not_configured", "provider": self.name, "tier": self.tier}
        return {"status": "online", "provider": self.name, "tier": self.tier}

    async def list_models(self) -> list[str]:
        return ["pixazo-free", "pixazo-pro"]

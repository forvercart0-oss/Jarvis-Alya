"""Puter image generation provider.

Puter offers free-tier image generation via its user-pays architecture.
No developer API key is required for basic usage.
"""

from __future__ import annotations

import httpx
import logging

from generation.image.provider import ImageGenerationProvider
from config.settings import get_settings

logger = logging.getLogger("jarvis.generation.image.puter")


class PuterImageProvider(ImageGenerationProvider):
    name = "puter"
    tier = "free"

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._base = "https://api.puter.com/v1"
        self._api_key = getattr(self.settings, "puter_api_key", "") or ""

    def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, **kwargs) -> dict:
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": kwargs.get("count", 1),
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base}/ai/image/generation", json=payload)
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
            logger.warning("Puter image generation error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def edit(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        return {"success": False, "error": "Image editing not supported by Puter provider."}

    async def image_to_image(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        return {"success": False, "error": "Image-to-image not supported by Puter provider."}

    async def health_check(self) -> dict:
        return {"status": "online", "provider": self.name, "tier": self.tier}

    async def list_models(self) -> list[str]:
        return ["puter-image-1"]

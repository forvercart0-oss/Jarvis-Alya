"""fal.ai video generation provider."""

from __future__ import annotations

import httpx
import logging
import os
from typing import Any, Optional

from generation.video.provider import VideoGenerationProvider
from config.settings import get_settings

logger = logging.getLogger("jarvis.generation.video.fal")


class FalVideoProvider(VideoGenerationProvider):
    name = "fal.ai"
    tier = "paid"

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._api_key = getattr(self.settings, "fal_api_key", "") or os.environ.get("FAL_API_KEY", "")
        self._base = "https://fal.run"

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def generate(self, prompt: str, **kwargs) -> dict:
        if not self._api_key:
            return {"success": False, "error": "fal.ai API key not configured."}
        headers = {"Authorization": f"Key {self._api_key}"}
        payload = {
            "prompt": prompt,
            "duration": kwargs.get("duration", 5),
            "resolution": kwargs.get("resolution", "720p"),
            "aspect_ratio": kwargs.get("aspect_ratio", "16:9"),
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base}/fal-ai/stable-video", json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {"success": True, "provider": self.name, "data": data, "job_id": data.get("job_id")}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            logger.warning("fal.ai video generation error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def image_to_video(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        if not self._api_key:
            return {"success": False, "error": "fal.ai API key not configured."}
        headers = {"Authorization": f"Key {self._api_key}"}
        files = {"image": ("input.png", image_data, "image/png")}
        data = {"prompt": prompt, "duration": kwargs.get("duration", 5)}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base}/fal-ai/image-to-video", files=files, data=data, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {"success": True, "provider": self.name, "data": data, "job_id": data.get("job_id")}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            logger.warning("fal.ai image-to-video error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def get_status(self, job_id: str) -> dict:
        if not self._api_key:
            return {"success": False, "error": "fal.ai API key not configured."}
        headers = {"Authorization": f"Key {self._api_key}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self._base}/fal-ai/stable-video/{job_id}", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {"success": True, "data": data, "status": data.get("status", "unknown")}
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def download(self, job_id: str, dest_path: str) -> dict:
        status = await self.get_status(job_id)
        if not status.get("success"):
            return status
        url = status.get("data", {}).get("video_url")
        if not url:
            return {"success": False, "error": "No video URL available."}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    with open(dest_path, "wb") as f:
                        f.write(resp.content)
                    return {"success": True, "path": dest_path}
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def cancel(self, job_id: str) -> dict:
        if not self._api_key:
            return {"success": False, "error": "fal.ai API key not configured."}
        headers = {"Authorization": f"Key {self._api_key}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{self._base}/fal-ai/stable-video/{job_id}/cancel", headers=headers)
                return {"success": resp.status_code == 200, "data": resp.json() if resp.status_code == 200 else {}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def health_check(self) -> dict:
        if not self._api_key:
            return {"status": "not_configured", "provider": self.name, "tier": self.tier}
        return {"status": "online", "provider": self.name, "tier": self.tier}

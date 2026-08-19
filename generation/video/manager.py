"""Video generation manager."""

from __future__ import annotations

import logging

from generation.video.provider import VideoGenerationProvider
from generation.video.fal_provider import FalVideoProvider
from generation.video.magic_hour_provider import MagicHourVideoProvider
from config.settings import get_settings

logger = logging.getLogger("jarvis.generation.video")


class VideoGenerationManager:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._providers: dict[str, VideoGenerationProvider] = {}
        self._register_providers()

    def _register_providers(self):
        candidates = {
            "fal": FalVideoProvider,
            "magic_hour": MagicHourVideoProvider,
        }
        for key, cls in candidates.items():
            try:
                provider = cls(self.settings)
                if provider.is_available():
                    self._providers[key] = provider
            except Exception as exc:
                logger.warning("Video provider %s registration failed: %s", key, exc)

    def is_available(self) -> bool:
        return bool(self._providers)

    def available_providers(self) -> list[str]:
        return list(self._providers.keys())

    def _select(self, preferred: str | None = None) -> VideoGenerationProvider | None:
        if preferred and preferred in self._providers:
            return self._providers[preferred]
        for provider in self._providers.values():
            if provider.is_available():
                return provider
        return None

    async def generate(self, prompt: str, provider: str | None = None, **kwargs) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No video generation provider available."}
        try:
            return await selected.generate(prompt, **kwargs)
        except Exception as exc:
            logger.warning("Video generation failed (%s): %s", selected.name, exc)
            return {"success": False, "error": str(exc)}

    async def image_to_video(self, image_data: bytes, prompt: str, provider: str | None = None, **kwargs) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No video generation provider available."}
        try:
            return await selected.image_to_video(image_data, prompt, **kwargs)
        except Exception as exc:
            logger.warning("Image-to-video failed (%s): %s", selected.name, exc)
            return {"success": False, "error": str(exc)}

    async def get_status(self, job_id: str, provider: str | None = None) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No video generation provider available."}
        try:
            return await selected.get_status(job_id)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def download(self, job_id: str, dest_path: str, provider: str | None = None) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No video generation provider available."}
        try:
            return await selected.download(job_id, dest_path)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def cancel(self, job_id: str, provider: str | None = None) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No video generation provider available."}
        try:
            return await selected.cancel(job_id)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def health(self) -> dict:
        results = {}
        for key, provider in self._providers.items():
            try:
                results[key] = await provider.health_check()
            except Exception as exc:
                results[key] = {"status": "offline", "error": str(exc)}
        return results

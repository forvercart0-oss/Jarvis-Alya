"""Image generation manager."""

from __future__ import annotations

import logging

from generation.image.provider import ImageGenerationProvider
from generation.image.puter_provider import PuterImageProvider
from generation.image.pixazo_provider import PixazoImageProvider
from generation.image.gemini_provider import GeminiImageProvider
from config.settings import get_settings

logger = logging.getLogger("jarvis.generation.image")


class ImageGenerationManager:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._providers: dict[str, ImageGenerationProvider] = {}
        self._active: str | None = None
        self._register_providers()

    def _register_providers(self):
        candidates = {
            "puter": PuterImageProvider,
            "pixazo": PixazoImageProvider,
            "gemini": GeminiImageProvider,
        }
        for key, cls in candidates.items():
            try:
                provider = cls(self.settings)
                if provider.is_available():
                    self._providers[key] = provider
            except Exception as exc:
                logger.warning("Image provider %s registration failed: %s", key, exc)

    def is_available(self) -> bool:
        return bool(self._providers)

    def available_providers(self) -> list[str]:
        return list(self._providers.keys())

    def _select(self, preferred: str | None = None) -> ImageGenerationProvider | None:
        if preferred and preferred in self._providers:
            return self._providers[preferred]
        for provider in self._providers.values():
            if provider.is_available():
                return provider
        return None

    async def generate(self, prompt: str, provider: str | None = None, **kwargs) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No image generation provider available."}
        try:
            return await selected.generate(prompt, **kwargs)
        except Exception as exc:
            logger.warning("Image generation failed (%s): %s", selected.name, exc)
            return {"success": False, "error": str(exc)}

    async def edit(self, image_data: bytes, prompt: str, provider: str | None = None, **kwargs) -> dict:
        selected = self._select(provider)
        if not selected:
            return {"success": False, "error": "No image generation provider available."}
        try:
            return await selected.edit(image_data, prompt, **kwargs)
        except Exception as exc:
            logger.warning("Image edit failed (%s): %s", selected.name, exc)
            return {"success": False, "error": str(exc)}

    async def health(self) -> dict:
        results = {}
        for key, provider in self._providers.items():
            try:
                results[key] = await provider.health_check()
            except Exception as exc:
                results[key] = {"status": "offline", "error": str(exc)}
        return results

    async def list_models(self, provider: str | None = None) -> dict:
        if provider and provider in self._providers:
            return {provider: await self._providers[provider].list_models()}
        out = {}
        for key, prov in self._providers.items():
            try:
                out[key] = await prov.list_models()
            except Exception:
                out[key] = []
        return out

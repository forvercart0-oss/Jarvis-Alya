"""Image generation provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ImageGenerationProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> dict:
        pass

    @abstractmethod
    async def edit(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        pass

    @abstractmethod
    async def image_to_image(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def tier(self) -> str:
        pass

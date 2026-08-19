"""Video generation provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VideoGenerationProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> dict:
        pass

    @abstractmethod
    async def image_to_video(self, image_data: bytes, prompt: str, **kwargs) -> dict:
        pass

    @abstractmethod
    async def get_status(self, job_id: str) -> dict:
        pass

    @abstractmethod
    async def download(self, job_id: str, dest_path: str) -> dict:
        pass

    @abstractmethod
    async def cancel(self, job_id: str) -> dict:
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def tier(self) -> str:
        pass

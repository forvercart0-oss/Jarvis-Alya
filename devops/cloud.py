"""Cloud provider abstraction for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.cloud")


class CloudProvider:
    def __init__(self, name: str):
        self.name = name
        self._available = False

    async def deploy(self, service: str, image: str) -> dict[str, Any]:
        return {"success": False, "error": f"{self.name} deployment not configured"}

    async def status(self, service: str) -> dict[str, Any]:
        return {"success": False, "error": f"{self.name} status not configured"}

    async def logs(self, service: str, tail: int = 100) -> dict[str, Any]:
        return {"success": False, "error": f"{self.name} logs not configured"}


class CloudManager:
    def __init__(self):
        self._providers: dict[str, CloudProvider] = {}

    def register(self, provider: CloudProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> CloudProvider | None:
        return self._providers.get(name)

    def detect_available(self) -> list[str]:
        import shutil
        available = []
        if shutil.which("aws"):
            available.append("aws")
        if shutil.which("gcloud"):
            available.append("gcp")
        if shutil.which("az"):
            available.append("azure")
        if shutil.which("doctl"):
            available.append("digitalocean")
        return available


cloud_manager = CloudManager()

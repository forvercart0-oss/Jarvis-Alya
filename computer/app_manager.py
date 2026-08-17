"""Application manager for JARVIS Phase 19."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.computer.apps")


class ApplicationManager:
    def __init__(self, provider: Any | None = None):
        self._provider = provider
        self._cache: dict[str, Any] = {}
        self._cache_ttl: float = 300.0

    async def launch(self, app: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.launch_application(app)

    async def close(self, app: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.close_application(app)

    async def is_running(self, app: str) -> bool:
        if not self._provider:
            return False
        result = await self._provider.list_windows()
        if isinstance(result, dict):
            windows = result.get("windows", [])
            lower = app.lower()
            return any(lower in str(w).lower() for w in windows)
        return False

    async def list_installed(self) -> list[dict[str, Any]]:
        return []

    async def discover(self) -> list[dict[str, Any]]:
        return []

    async def get_info(self, app: str) -> dict[str, Any]:
        return {"name": app, "installed": False, "running": False}


app_manager = ApplicationManager()

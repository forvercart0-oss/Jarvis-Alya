"""Window manager for JARVIS Phase 19."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.computer.windows")


class WindowManager:
    def __init__(self, provider: Any | None = None):
        self._provider = provider

    async def list(self) -> list[dict[str, Any]]:
        if not self._provider:
            return []
        result = await self._provider.list_windows()
        if isinstance(result, dict):
            return result.get("windows", [])
        return []

    async def active(self) -> dict[str, Any]:
        if not self._provider:
            return {}
        info = await self._provider.get_active_window()
        if hasattr(info, "to_dict"):
            return info.to_dict()
        return info if isinstance(info, dict) else {}

    async def focus(self, window_id: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.focus_window(window_id)

    async def minimize(self, window_id: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.minimize_window(window_id)

    async def maximize(self, window_id: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.maximize_window(window_id)

    async def restore(self, window_id: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.restore_window(window_id)

    async def close(self, window_id: str) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.close_window(window_id)

    async def move(self, window_id: str, x: int, y: int) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.move_window(window_id, x, y)

    async def resize(self, window_id: str, width: int, height: int) -> dict[str, Any]:
        if not self._provider:
            return {"success": False, "error": "No provider"}
        return await self._provider.resize_window(window_id, width, height)

    async def find_by_title(self, title: str) -> dict[str, Any] | None:
        windows = await self.list()
        lower = title.lower()
        for w in windows:
            if isinstance(w, dict):
                if lower in w.get("title", "").lower() or lower in w.get("application", "").lower():
                    return w
        return None

    async def find_by_app(self, app: str) -> dict[str, Any] | None:
        windows = await self.list()
        lower = app.lower()
        for w in windows:
            if isinstance(w, dict):
                if lower in w.get("application", "").lower():
                    return w
        return None


window_manager = WindowManager()

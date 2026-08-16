"""Computer control manager for JARVIS Phase 3."""

from __future__ import annotations

import logging
from typing import Any

from computer.platform import CURRENT_PLATFORM, detect_platform
from computer.safety import ComputerSafety

logger = logging.getLogger("jarvis.computer.manager")


class ComputerManager:
    def __init__(self):
        self._platform = detect_platform()
        self._safety = ComputerSafety()
        self._available = True

    @property
    def platform(self) -> str:
        return self._platform

    @property
    def available(self) -> bool:
        return self._available

    async def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._safety.is_allowed(action):
            return {"success": False, "error": "Action not permitted by safety policy."}
        if self._safety.requires_confirmation(action):
            return {"success": False, "confirmation_required": True, "action": action, "arguments": arguments}

        handler = getattr(self, f"_handle_{action}", None)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        return await handler(arguments)

    async def _handle_open_application(self, args: dict[str, Any]) -> dict[str, Any]:
        app = args.get("app", "")
        if not app:
            return {"success": False, "error": "Application name required"}
        return self._run_platform("open_application", app)

    async def _handle_type_text(self, args: dict[str, Any]) -> dict[str, Any]:
        text = args.get("text", "")
        if not text:
            return {"success": False, "error": "Text required"}
        return self._run_platform("type_text", text)

    async def _handle_take_screenshot(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "/tmp/jarvis_screenshot.png")
        return self._run_platform("take_screenshot", path)

    async def _handle_set_volume(self, args: dict[str, Any]) -> dict[str, Any]:
        level = args.get("level", 50)
        return self._run_platform("set_volume", level)

    def _run_platform(self, action: str, *args: Any) -> dict[str, Any]:
        module = {"linux": "computer.linux", "windows": "computer.windows", "macos": "computer.macos"}.get(self._platform)
        if not module:
            return {"success": False, "error": f"Platform {self._platform} not supported"}
        import importlib
        mod = importlib.import_module(module)
        handler = getattr(mod, action, None)
        if not handler:
            return {"success": False, "error": f"Action {action} not implemented for {self._platform}"}
        return handler(*args)

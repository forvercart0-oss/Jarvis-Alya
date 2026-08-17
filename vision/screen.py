"""Screen capture provider abstraction for JARVIS Phase 17."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.screen")


@dataclass
class WindowInfo:
    title: str
    app: str
    pid: int = 0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    is_active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreenInfo:
    width: int = 0
    height: int = 0
    monitors: list[dict[str, Any]] = field(default_factory=list)
    backend: str = ""


class ScreenCaptureProvider(ABC):
    """Abstract screen capture provider."""

    name: str = "base"

    @abstractmethod
    async def capture_screen(self, mode: str = "full", window: str | None = None, region: str | None = None, monitor: int | None = None, output_path: str | None = None) -> dict[str, Any]:
        """Capture screen and return image path/data."""

    @abstractmethod
    async def list_windows(self) -> dict[str, Any]:
        """List available windows."""

    @abstractmethod
    async def get_active_window(self) -> WindowInfo:
        """Get active window info."""

    @abstractmethod
    async def get_screen_info(self) -> ScreenInfo:
        """Get screen dimensions and monitor info."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check if screen capture is available."""


class SystemScreenCaptureProvider(ScreenCaptureProvider):
    """Wraps the existing system platform for screen capture."""

    name = "system"

    def __init__(self):
        from system import get_platform
        self._platform = get_platform()

    async def capture_screen(self, mode: str = "full", window: str | None = None, region: str | None = None, monitor: int | None = None, output_path: str | None = None) -> dict[str, Any]:
        if output_path is None:
            import tempfile
            fd, output_path = tempfile.mkstemp(suffix=".png")
            import os
            os.close(fd)
        return await self._platform.screenshot(output_path, region=region or "")

    async def list_windows(self) -> dict[str, Any]:
        if hasattr(self._platform, "list_windows"):
            return await self._platform.list_windows()
        return {"success": False, "error": "list_windows not supported on this platform"}

    async def get_active_window(self) -> WindowInfo:
        if hasattr(self._platform, "get_active_window"):
            data = await self._platform.get_active_window()
            if data.get("success") or data.get("app") or data.get("title"):
                return WindowInfo(
                    title=data.get("title", ""),
                    app=data.get("app", ""),
                    x=data.get("x", 0),
                    y=data.get("y", 0),
                    width=data.get("width", 0),
                    height=data.get("height", 0),
                    is_active=True,
                    metadata=data,
                )
        return WindowInfo(title="", app="")

    async def get_screen_info(self) -> ScreenInfo:
        if hasattr(self._platform, "get_screen_info"):
            data = await self._platform.get_screen_info()
            return ScreenInfo(
                width=data.get("width", 0),
                height=data.get("height", 0),
                backend=data.get("backend", ""),
            )
        return ScreenInfo()

    async def health_check(self) -> dict[str, Any]:
        try:
            info = await self.get_screen_info()
            return {"status": "online", "screen": f"{info.width}x{info.height}", "backend": info.backend}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}


_screen_provider: SystemScreenCaptureProvider | None = None


def get_screen_provider() -> ScreenCaptureProvider:
    global _screen_provider
    if _screen_provider is None:
        _screen_provider = SystemScreenCaptureProvider()
    return _screen_provider

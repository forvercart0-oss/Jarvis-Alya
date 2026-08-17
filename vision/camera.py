"""Camera utilities for JARVIS Phase 14."""

from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any

logger = logging.getLogger("jarvis.vision.camera")


class CameraManager:
    def __init__(self):
        self._active: bool = False
        self._stream: Any = None

    @property
    def active(self) -> bool:
        return self._active

    async def start(self) -> dict[str, Any]:
        self._active = True
        return {"success": True, "status": "camera_active"}

    async def stop(self) -> dict[str, Any]:
        self._active = False
        if self._stream:
            with suppress(Exception):
                self._stream.release()
            self._stream = None
        return {"success": True, "status": "camera_stopped"}

    async def capture(self) -> dict[str, Any]:
        if not self._active:
            return {"success": False, "error": "Camera is not active."}
        return {"success": False, "error": "Camera capture not implemented in this environment."}

    def status(self) -> dict[str, Any]:
        return {"active": self._active, "stream": self._stream is not None}

"""Hand gesture detection module.

Uses local computer vision where possible.
Never uploads camera frames to third-party servers unless explicitly configured.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("jarvis.gesture")


class GestureDetector:
    """Base gesture detector.

    Real implementation uses MediaPipe or similar local landmarks.
    """

    def __init__(self, settings):
        self.settings = settings
        self._active = False
        self._backend = "none"

    def is_available(self) -> bool:
        return False

    async def start(self, on_gesture) -> bool:
        self._active = True
        return True

    async def stop(self) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

"""Platform detection for JARVIS Phase 3."""

from __future__ import annotations

import platform
import sys
from typing import Literal

Platform = Literal["linux", "windows", "macos", "unknown"]


def detect_platform() -> Platform:
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    return "unknown"


CURRENT_PLATFORM = detect_platform()

"""Computer control module for JARVIS Phase 3."""

from __future__ import annotations

from computer.manager import ComputerManager
from computer.platform import CURRENT_PLATFORM, detect_platform
from computer.safety import ComputerSafety

__all__ = [
    "ComputerManager",
    "ComputerSafety",
    "CURRENT_PLATFORM",
    "detect_platform",
]

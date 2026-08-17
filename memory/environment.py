"""Environment profile for JARVIS Phase 21."""

from __future__ import annotations

import logging
import os
import platform
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.memory.environment")


@dataclass
class EnvironmentProfile:
    os: str = ""
    architecture: str = ""
    python_version: str = ""
    node_version: str = ""
    gpu_available: bool = False
    ram_gb: float = 0.0
    available_tools: list[str] = field(default_factory=list)
    configured_providers: list[str] = field(default_factory=list)
    display_server: str = ""
    desktop_environment: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "os": self.os,
            "architecture": self.architecture,
            "python_version": self.python_version,
            "node_version": self.node_version,
            "gpu_available": self.gpu_available,
            "ram_gb": self.ram_gb,
            "available_tools": self.available_tools,
            "configured_providers": self.configured_providers,
            "display_server": self.display_server,
            "desktop_environment": self.desktop_environment,
            "metadata": self.metadata,
        }


class EnvironmentProfiler:
    def __init__(self):
        self._profile: EnvironmentProfile | None = None
        self._cache_ttl: float = 3600.0
        self._last_update: float = 0.0

    async def get_profile(self) -> EnvironmentProfile:
        now = time.time()
        if self._profile and (now - self._last_update) < self._cache_ttl:
            return self._profile
        profile = EnvironmentProfile()
        try:
            profile.os = platform.system()
            profile.architecture = platform.machine()
            profile.python_version = platform.python_version()
            profile.display_server = os.environ.get("XDG_SESSION_TYPE", "")
            profile.desktop_environment = os.environ.get("XDG_CURRENT_DESKTOP", "")
        except Exception:
            pass
        self._profile = profile
        self._last_update = now
        return profile

    def detect_display_server(self) -> str:
        return os.environ.get("XDG_SESSION_TYPE", "unknown")

    def detect_desktop_environment(self) -> str:
        return os.environ.get("XDG_CURRENT_DESKTOP", "unknown")


environment_profiler = EnvironmentProfiler()

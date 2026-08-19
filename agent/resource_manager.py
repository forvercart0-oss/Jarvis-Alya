"""Resource Manager for JARVIS Phase 23.

Monitors system resources and adapts concurrency based on
available CPU, RAM, and GPU.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger("jarvis.agent.resources")


@dataclass
class SystemResources:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_available_mb: int = 0
    gpu_available: bool = False
    active_processes: int = 0
    load_avg: tuple[float, float, float] = (0.0, 0.0, 0.0)


class ResourceManager:
    """Monitors system resources and recommends concurrency limits."""

    def __init__(self):
        self._max_agents: int = 3
        self._min_ram_mb_per_agent: int = 256
        self._resource_cache: SystemResources | None = None
        self._cache_ttl: float = 5.0
        self._last_update: float = 0.0

    def get_resources(self) -> SystemResources:
        now = time.time()
        if self._resource_cache and (now - self._last_update) < self._cache_ttl:
            return self._resource_cache

        try:
            if HAS_PSUTIL:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                load = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
                resources = SystemResources(
                    cpu_percent=cpu,
                    ram_percent=mem.percent,
                    ram_available_mb=mem.available // (1024 * 1024),
                    gpu_available=False,
                    active_processes=len(psutil.pids()),
                    load_avg=load,
                )
            else:
                resources = SystemResources()
        except Exception:
            resources = SystemResources()

        self._resource_cache = resources
        self._last_update = now
        return resources

    def get_max_parallel_agents(self) -> int:
        resources = self.get_resources()
        if resources.ram_available_mb < 512:
            return 1
        if resources.cpu_percent > 80:
            return 1
        if resources.ram_percent > 80:
            return 2
        return min(self._max_agents, max(1, resources.ram_available_mb // self._min_ram_mb_per_agent))

    def can_spawn_agent(self, estimated_ram_mb: int = 256) -> bool:
        resources = self.get_resources()
        return resources.ram_available_mb >= estimated_ram_mb

    def update_settings(self, max_agents: int = 3, min_ram_mb_per_agent: int = 256) -> None:
        self._max_agents = max(1, max_agents)
        self._min_ram_mb_per_agent = max(64, min_ram_mb_per_agent)


resource_manager = ResourceManager()

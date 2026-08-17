"""Memory cache for frequently accessed memories."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("jarvis.memory.cache")


class MemoryCache:
    """Simple TTL cache for frequently accessed memories."""

    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 200):
        self._ttl = ttl_seconds
        self._max = max_size
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict | None:
        entry = self._cache.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self._ttl),
        }
        self._evict()

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    def _evict(self) -> None:
        if len(self._cache) <= self._max:
            return
        expired = [k for k, v in self._cache.items() if time.time() > v["expires_at"]]
        for k in expired:
            del self._cache[k]
        if len(self._cache) > self._max:
            oldest = sorted(self._cache.items(), key=lambda kv: kv[1]["expires_at"])[: len(self._cache) - self._max]
            for k, _ in oldest:
                del self._cache[k]

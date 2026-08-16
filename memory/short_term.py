"""Short-term memory: conversation context and recent interactions."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("jarvis.memory.short_term")


class ShortTermMemory:
    """Manages short-term conversation context with TTL."""

    def __init__(self, ttl_seconds: float = 3600.0, max_items: int = 100):
        self._ttl = ttl_seconds
        self._max = max_items
        self._context: dict[str, dict[str, Any]] = {}

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._context[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self._ttl),
        }
        self._evict()

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._context.get(key)
        if not entry:
            return default
        if time.time() > entry["expires_at"]:
            del self._context[key]
            return default
        return entry["value"]

    def get_all(self) -> dict[str, Any]:
        now = time.time()
        return {k: v["value"] for k, v in self._context.items() if v["expires_at"] > now}

    def delete(self, key: str) -> None:
        self._context.pop(key, None)

    def clear(self) -> None:
        self._context.clear()

    def _evict(self) -> None:
        if len(self._context) <= self._max:
            return
        expired = [k for k, v in self._context.items() if time.time() > v["expires_at"]]
        for k in expired:
            del self._context[k]
        if len(self._context) > self._max:
            oldest = sorted(self._context.items(), key=lambda kv: kv[1]["expires_at"])[: len(self._context) - self._max]
            for k, _ in oldest:
                del self._context[k]

"""User preferences memory."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.preferences")


class PreferencesMemory:
    """Manage user preferences as a view over long-term memory."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def set(self, key: str, value: str, profile: str = "jarvis") -> dict:
        return self._memory.store.remember(
            value,
            category="preferences",
            key_override=key,
            confidence=1.0,
            source="explicit_user",
            profile=profile,
        )

    def get(self, key: str, profile: str = "jarvis") -> str | None:
        results = self._memory.store.recall(key, category="preferences", profile=profile, limit=1)
        if results:
            return results[0].get("value")
        return None

    def get_all(self, profile: str = "jarvis") -> list[dict]:
        return self._memory.store.recall(category="preferences", profile=profile, limit=100)

    def delete(self, key: str, profile: str = "jarvis") -> bool:
        results = self._memory.store.recall(key, category="preferences", profile=profile, limit=1)
        if results:
            return self._memory.store.delete_memory_by_id(results[0]["id"])
        return False

    def clear(self, profile: str = "jarvis") -> int:
        results = self._memory.store.recall(category="preferences", profile=profile, limit=1000)
        count = 0
        for row in results:
            if self._memory.store.delete_memory_by_id(row["id"]):
                count += 1
        return count

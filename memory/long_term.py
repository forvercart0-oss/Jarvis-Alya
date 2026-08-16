"""Long-term memory: persistent preferences and facts with confidence tracking."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.long_term")


class LongTermMemory:
    """Manages long-term memories via MemoryManager."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def remember(
        self,
        key: str,
        value: str = "",
        category: str = "general",
        confidence: float = 1.0,
        source: str = "explicit_user",
        project: str = "",
        profile: str = "jarvis",
        expires_at: str | None = None,
    ) -> dict:
        from memory.secret_filter import contains_secret
        content = value if value else key
        if contains_secret(content):
            raise ValueError("Refusing to store secret material in long-term memory.")
        return self._memory.store.remember(
            content,
            category=category,
            key_override=key if value else "",
            confidence=confidence,
            source=source,
            project=project,
            profile=profile,
            expires_at=expires_at,
        )

    def recall(
        self,
        query: str = "",
        category: str | None = None,
        project: str | None = None,
        profile: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> list[dict]:
        return self._memory.store.recall(
            query=query,
            category=category,
            project=project,
            profile=profile,
            min_confidence=min_confidence,
            limit=limit,
        )

    def forget(self, query: str) -> int:
        return self._memory.store.forget(query)

    def forget_by_id(self, memory_id: str) -> bool:
        return self._memory.store.delete_memory_by_id(memory_id)

    def update(
        self,
        memory_id: str,
        value: str,
        confidence: float | None = None,
        source: str | None = None,
    ) -> bool:
        return self._memory.store.update_memory(memory_id, value, confidence=confidence, source=source)

    def get_by_id(self, memory_id: str) -> dict | None:
        return self._memory.store.get_memory_by_id(memory_id)

    def clear_all(self) -> int:
        return self._memory.store.clear_all_memories()

    def get_stats(self) -> dict:
        return self._memory.store.get_memory_stats()

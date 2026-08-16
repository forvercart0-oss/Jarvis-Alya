"""Task memory: store and retrieve task-related context."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.tasks")


class TaskMemory:
    """Manage task-specific memory entries."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def remember(self, task_id: str, content: str, category: str = "tasks", confidence: float = 1.0, source: str = "task", profile: str = "jarvis") -> dict:
        return self._memory.store.remember(
            content,
            category=category,
            key_override=task_id,
            confidence=confidence,
            source=source,
            project=task_id,
            profile=profile,
        )

    def recall(self, task_id: str = "", query: str = "", limit: int = 50) -> list[dict]:
        return self._memory.store.recall(query=query, category="tasks", project=task_id or None, limit=limit)

    def forget(self, task_id: str, query: str = "") -> int:
        return self._memory.store.forget(query)

    def clear(self, task_id: str) -> int:
        results = self._memory.store.recall(category="tasks", project=task_id, limit=1000)
        count = 0
        for row in results:
            if self._memory.store.delete_memory_by_id(row["id"]):
                count += 1
        return count

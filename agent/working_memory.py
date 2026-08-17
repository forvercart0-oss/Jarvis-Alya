"""Working memory for JARVIS Phase 23.

Maintains temporary task-scoped memory during goal execution.
Separate from long-term user memory.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.agent.working_memory")


@dataclass
class WorkingMemoryEntry:
    key: str
    value: Any
    entry_type: str = "context"
    task_id: str = ""
    goal_id: str = ""
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    ttl_seconds: float = 3600.0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    def touch(self) -> None:
        self.accessed_at = time.time()


class WorkingMemory:
    """Task-scoped working memory."""

    def __init__(self):
        self._entries: dict[str, WorkingMemoryEntry] = {}
        self._goal_context: dict[str, dict[str, Any]] = {}

    def set(self, key: str, value: Any, entry_type: str = "context", goal_id: str = "", task_id: str = "", ttl_seconds: float = 3600.0) -> None:
        entry_id = f"{goal_id}:{task_id}:{key}" if goal_id else key
        self._entries[entry_id] = WorkingMemoryEntry(
            key=key, value=value, entry_type=entry_type, task_id=task_id, goal_id=goal_id, ttl_seconds=ttl_seconds,
        )
        if goal_id:
            self._goal_context.setdefault(goal_id, {})[key] = value

    def get(self, key: str, goal_id: str = "", task_id: str = "") -> Any | None:
        entry_id = f"{goal_id}:{task_id}:{key}" if goal_id else key
        entry = self._entries.get(entry_id)
        if entry and not entry.is_expired():
            entry.touch()
            return entry.value
        if entry:
            del self._entries[entry_id]
        return None

    def get_goal_context(self, goal_id: str) -> dict[str, Any]:
        return dict(self._goal_context.get(goal_id, {}))

    def set_goal_context(self, goal_id: str, context: dict[str, Any]) -> None:
        self._goal_context[goal_id] = dict(context)

    def clear_goal(self, goal_id: str) -> int:
        to_remove = [eid for eid, e in self._entries.items() if e.goal_id == goal_id]
        for eid in to_remove:
            del self._entries[eid]
        self._goal_context.pop(goal_id, None)
        return len(to_remove)

    def cleanup_expired(self) -> int:
        expired = [eid for eid, e in self._entries.items() if e.is_expired()]
        for eid in expired:
            del self._entries[eid]
        return len(expired)

    def summary(self) -> dict[str, Any]:
        return {
            "entries": len(self._entries),
            "goals": len(self._goal_context),
            "expired": sum(1 for e in self._entries.values() if e.is_expired()),
        }


working_memory = WorkingMemory()

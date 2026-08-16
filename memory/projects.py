"""Project memory: store and retrieve project-specific context."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.projects")


class ProjectMemory:
    """Manage project-specific memory entries."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def remember(self, project: str, content: str, category: str = "projects", confidence: float = 1.0, source: str = "explicit_user", profile: str = "jarvis") -> dict:
        return self._memory.store.remember(
            content,
            category=category,
            key_override=project,
            confidence=confidence,
            source=source,
            project=project,
            profile=profile,
        )

    def recall(self, project: str, query: str = "", limit: int = 50) -> list[dict]:
        return self._memory.store.recall(query=query, category="projects", project=project, limit=limit)

    def forget(self, project: str, query: str = "") -> int:
        return self._memory.store.forget(query)

    def clear(self, project: str) -> int:
        results = self._memory.store.recall(category="projects", project=project, limit=1000)
        count = 0
        for row in results:
            if self._memory.store.delete_memory_by_id(row["id"]):
                count += 1
        return count

    def list_projects(self) -> list[str]:
        import sqlite3
        with sqlite3.connect(self._memory.store.db_path) as conn:
            rows = conn.execute("SELECT DISTINCT project FROM memories WHERE category = 'projects' AND project != ''").fetchall()
            return [row[0] for row in rows if row[0]]

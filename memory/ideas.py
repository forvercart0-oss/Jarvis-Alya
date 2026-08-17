"""Ideas memory system for JARVIS Phase 29."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.ideas")


class IdeasSystem:
    """Manage user ideas and project concepts."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def create_idea(self, title: str, description: str = "", tags: list[str] | None = None, status: str = "idea", project: str = "", profile: str = "jarvis") -> dict:
        return self._memory.store.add_idea(
            title=title,
            description=description,
            tags=tags or [],
            status=status,
            project=project,
            profile=profile,
        )

    def get_ideas(self, status: str | None = None, project: str | None = None, profile: str | None = None, limit: int = 50) -> list[dict]:
        return self._memory.store.get_ideas(status=status, project=project, profile=profile, limit=limit)

    def update_idea(self, idea_id: str, updates: dict) -> dict | None:
        return self._memory.store.update_idea(idea_id, updates)

    def delete_idea(self, idea_id: str) -> bool:
        return self._memory.store.delete_idea(idea_id)

    def get_idea_by_id(self, idea_id: str) -> dict | None:
        return self._memory.store.get_idea(idea_id)

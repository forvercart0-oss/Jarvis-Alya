"""Error memory system for JARVIS Phase 29."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.errors")


class ErrorMemory:
    """Store and retrieve recurring technical problems and their resolutions."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def record_error(self, error_signature: str, resolution: str, category: str = "other", project: str = "", profile: str = "jarvis", confidence: float = 1.0) -> dict:
        return self._memory.store.add_error_memory(
            error_signature=error_signature,
            resolution=resolution,
            category=category,
            project=project,
            profile=profile,
            confidence=confidence,
        )

    def find_resolution(self, error_signature: str, limit: int = 5) -> list[dict]:
        return self._memory.store.search_error_memories(error_signature, limit=limit)

    def get_errors(self, project: str | None = None, category: str | None = None, profile: str | None = None, limit: int = 50) -> list[dict]:
        return self._memory.store.get_error_memories(project=project, category=category, profile=profile, limit=limit)

    def delete_error(self, error_id: str) -> bool:
        return self._memory.store.delete_error_memory(error_id)

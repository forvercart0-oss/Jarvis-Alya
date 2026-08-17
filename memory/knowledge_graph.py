"""Lightweight knowledge graph for JARVIS Phase 12."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.knowledge_graph")


class KnowledgeGraph:
    def __init__(self, store: Any):
        self._store = store

    def link(self, source_id: str, target_id: str, relation: str = "related_to") -> bool:
        source = self._store.get_memory_by_id(source_id)
        target = self._store.get_memory_by_id(target_id)
        if not source or not target:
            return False
        related = source.get("related_ids") or []
        if target_id not in related:
            related.append(target_id)
        self._store.update_memory_fields(source_id, {"related_ids": related})
        return True

    def related(self, memory_id: str, limit: int = 10) -> list[dict]:
        return self._store.get_related_memories(memory_id, limit=limit)

    def neighbors(self, memory_id: str, relation: str = "related_to") -> list[dict]:
        return self._store.get_related_memories(memory_id, limit=20)

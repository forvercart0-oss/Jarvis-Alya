"""Semantic memory search enhancements."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.semantic")


class SemanticMemory:
    """Enhanced semantic search over memory store."""

    def __init__(self, memory_manager: Any, vector_index: Any | None = None):
        self._memory = memory_manager
        self._vector = vector_index

    def search(self, query: str, limit: int = 5, min_score: float = 0.0) -> list[dict]:
        results = self._memory.recall(query, limit=limit)
        if self._vector is not None and self._vector.available():
            try:
                vector_hits = self._vector.search(query, limit=limit)
                seen = {r["id"] for r in results}
                for hit in vector_hits:
                    if hit["id"] in seen:
                        continue
                    row = self._memory.store.get_memory_by_id(hit["id"])
                    if row:
                        row = dict(row)
                        row["semantic_score"] = hit.get("score")
                        results.append(row)
                        seen.add(hit["id"])
            except Exception as exc:
                logger.warning("Semantic search failed: %s", exc)
        return results[:limit]

    def is_available(self) -> bool:
        return self._vector is not None and self._vector.available()

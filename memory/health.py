"""Memory health and diagnostics for JARVIS Phase 12."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.health")


class MemoryHealth:
    def __init__(self, store: Any):
        self._store = store

    def check(self) -> dict:
        return self._store.get_health()

    def summary(self) -> dict:
        stats = self._store.get_memory_stats()
        health = self.check()
        return {
            "total_memories": health.get("total_memories", 0),
            "storage_bytes": health.get("storage_bytes", 0),
            "duplicates": health.get("duplicates", 0),
            "contradictions": health.get("contradictions", 0),
            "low_confidence": health.get("low_confidence", 0),
            "vector_enabled": health.get("vector_enabled", False),
            "categories": self._get_category_counts(),
        }

    def _get_category_counts(self) -> dict[str, int]:
        try:
            import sqlite3
            with sqlite3.connect(self._store.db_path) as conn:
                rows = conn.execute("SELECT category, COUNT(*) as count FROM memories GROUP BY category").fetchall()
                return {row[0]: row[1] for row in rows}
        except Exception:
            return {}

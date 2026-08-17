"""Contradiction detection for JARVIS Phase 12."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.contradictions")


class ContradictionDetector:
    def __init__(self, store: Any):
        self._store = store

    def find(self) -> list[dict]:
        return self._store.detect_contradictions()

    def resolve(self, contradiction: dict, keep_id: str) -> dict | None:
        memory_ids = contradiction.get("memory_ids", [])
        for mid in memory_ids:
            if mid != keep_id:
                self._store.delete_memory_by_id(mid)
        return self._store.get_memory_by_id(keep_id)

"""Duplicate memory detection and merging for JARVIS Phase 12."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.duplicates")


class DuplicateDetector:
    def __init__(self, store: Any):
        self._store = store

    def find(self, threshold: float = 0.85) -> list[dict]:
        return self._store.detect_duplicates(threshold=threshold)

    def merge(self, primary_id: str, secondary_id: str) -> dict | None:
        primary = self._store.get_memory_by_id(primary_id)
        secondary = self._store.get_memory_by_id(secondary_id)
        if not primary or not secondary:
            return None
        merged_tags = list(set((primary.get("tags") or []) + (secondary.get("tags") or [])))
        merged_related = list(set((primary.get("related_ids") or []) + (secondary.get("related_ids") or []) + [secondary_id]))
        merged_confidence = max(float(primary.get("confidence") or 0.0), float(secondary.get("confidence") or 0.0))
        merged_importance = max(float(primary.get("importance") or 0.5), float(secondary.get("importance") or 0.5))
        updates = {
            "tags": merged_tags,
            "related_ids": merged_related,
            "confidence": merged_confidence,
            "importance": merged_importance,
        }
        updated = self._store.update_memory_fields(primary_id, updates)
        self._store.delete_memory_by_id(secondary_id)
        return updated

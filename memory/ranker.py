"""Memory ranking engine for JARVIS Phase 12."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("jarvis.memory.ranker")


class MemoryRanker:
    def __init__(self, store: Any):
        self._store = store

    def rank(self, memories: list[dict], query: str = "") -> list[dict]:
        now = datetime.utcnow().timestamp()
        scored = []
        query_lower = query.lower()
        query_tokens = set(query_lower.split()) if query_lower else set()
        for mem in memories:
            score = 0.0
            confidence = float(mem.get("confidence") or 0.0)
            importance = float(mem.get("importance") or 0.5)
            access_count = int(mem.get("access_count") or 0)
            decay = float(mem.get("decay_factor") or 1.0)
            text = (mem.get("value") or mem.get("key") or "").lower()
            if query_tokens:
                overlap = len(query_tokens & set(text.split()))
                score += min(overlap / max(len(query_tokens), 1), 1.0) * 0.4
            score += confidence * 0.2
            score += importance * 0.2
            score += min(access_count / 10.0, 1.0) * 0.1
            try:
                created = datetime.fromisoformat(mem.get("created_at", "")).timestamp()
                age_hours = (now - created) / 3600.0
                recency = max(0.0, 1.0 - (age_hours / (24.0 * 30)))
                score += recency * 0.1
            except Exception:
                score += 0.05
            score *= decay
            mem["_score"] = round(score, 4)
            scored.append(mem)
        scored.sort(key=lambda m: m.get("_score", 0.0), reverse=True)
        return scored

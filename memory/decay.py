"""Memory decay scheduler for JARVIS Phase 12."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.decay")


class MemoryDecay:
    def __init__(self, store: Any):
        self._store = store

    def apply(self, decay_rate: float = 0.01) -> int:
        return self._store.apply_decay(decay_rate=decay_rate)

    def boosted(self, memory_id: str, boost: float = 0.2) -> None:
        mem = self._store.get_memory_by_id(memory_id)
        if not mem:
            return
        current = float(mem.get("decay_factor", 1.0) or 1.0)
        new_decay = min(1.0, current + boost)
        self._store.update_memory_fields(memory_id, {"decay_factor": new_decay})

"""Memory backup, export, and import for JARVIS Phase 12."""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from typing import Any

logger = logging.getLogger("jarvis.memory.backup")


class MemoryBackup:
    def __init__(self, store: Any):
        self._store = store

    def export(self, category: str | None = None, project: str | None = None, profile: str | None = None) -> dict:
        data = self._store.export_memories(category=category, project=project, profile=profile)
        data["exported_at"] = datetime.now(UTC).isoformat()
        data["version"] = "12.0"
        return data

    def import_(self, data: dict, mode: str = "merge") -> dict:
        return self._store.import_memories(data, mode=mode)

    def create_backup(self) -> dict:
        data = self.export()
        data["backup_type"] = "full"
        data["backup_created_at"] = datetime.now(UTC).isoformat()
        return data

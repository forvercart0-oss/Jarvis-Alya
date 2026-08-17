"""Memory schema migration system for JARVIS Phase 29."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.migrator")


class MemoryMigrator:
    """Detect and migrate older memory schemas."""

    def __init__(self, store: Any):
        self._store = store

    def migrate(self) -> dict:
        result = {
            "migrated": False,
            "version": 0,
            "changes": [],
        }
        try:
            version = self._get_current_version()
            if version < 1:
                self._apply_v1()
                result["migrated"] = True
                result["version"] = 1
                result["changes"].append("Initial schema version")
            return result
        except Exception as exc:
            logger.warning("Memory migration failed: %s", exc)
            return result

    def _get_current_version(self) -> int:
        try:
            import sqlite3
            with sqlite3.connect(self._store.db_path) as conn:
                row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
                return row[0] if row and row[0] is not None else 0
        except Exception:
            return 0

    def _apply_v1(self) -> None:
        try:
            import sqlite3
            with sqlite3.connect(self._store.db_path) as conn:
                conn.execute("INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)", (1, __import__("datetime").datetime.utcnow().isoformat()))
                conn.commit()
        except Exception as exc:
            logger.warning("Migration v1 failed: %s", exc)

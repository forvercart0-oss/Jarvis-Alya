"""Memory audit log for JARVIS Phase 16."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Any

logger = logging.getLogger("jarvis.memory.audit")


class MemoryAuditLog:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_audit_log (
                    audit_id TEXT PRIMARY KEY,
                    event TEXT NOT NULL,
                    memory_id TEXT,
                    category TEXT,
                    memory_type TEXT,
                    project TEXT,
                    profile TEXT,
                    detail TEXT NOT NULL DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_audit_timestamp ON memory_audit_log(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_audit_event ON memory_audit_log(event)")
            conn.commit()

    def log(self, event: str, memory_id: str | None = None, category: str | None = None, memory_type: str | None = None, project: str | None = None, profile: str | None = None, detail: dict | None = None) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO memory_audit_log (audit_id, event, memory_id, category, memory_type, project, profile, detail, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        __import__("uuid").uuid4().hex[:12],
                        event,
                        memory_id,
                        category,
                        memory_type,
                        project,
                        profile,
                        __import__("json").dumps(detail or {}),
                        datetime.utcnow().isoformat(),
                    ),
                )
                conn.commit()
        except Exception as exc:
            logger.debug("Memory audit log failed: %s", exc)

    def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM memory_audit_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            logger.debug("Memory audit fetch failed: %s", exc)
            return []

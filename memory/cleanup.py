"""Memory cleanup and retention management."""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any

logger = logging.getLogger("jarvis.memory.cleanup")


class MemoryCleanup:
    """Clean up expired and temporary memory data."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def cleanup_expired_memories(self) -> int:
        now = datetime.now(UTC).isoformat()
        import sqlite3
        with sqlite3.connect(self._memory.store.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?",
                (now,),
            )
            conn.commit()
            count = cursor.rowcount
        return count

    def cleanup_old_temporary_data(self, max_age_hours: int = 24) -> dict:
        cutoff = datetime.now(UTC).timestamp() - (max_age_hours * 3600)
        results: dict[str, int] = {}
        import sqlite3
        with sqlite3.connect(self._memory.store.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM conversation_summaries WHERE created_at < ?",
                (datetime.fromtimestamp(cutoff, tz=UTC).isoformat(),),
            )
            results["summaries"] = cursor.rowcount
            cursor = conn.execute(
                "DELETE FROM memory_feedback WHERE created_at < ?",
                (datetime.fromtimestamp(cutoff, tz=UTC).isoformat(),),
            )
            results["feedback"] = cursor.rowcount
            conn.commit()
        return results

    def enforce_retention(self, task_history_days: int = 30, conversation_summary_days: int = 30) -> dict:
        cutoff_tasks = datetime.now(UTC).timestamp() - (task_history_days * 86400)
        cutoff_summaries = datetime.now(UTC).timestamp() - (conversation_summary_days * 86400)
        results: dict[str, int] = {}
        import sqlite3
        with sqlite3.connect(self._memory.store.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM tasks WHERE updated_at < ? AND status IN ('completed', 'failed', 'cancelled')",
                (datetime.fromtimestamp(cutoff_tasks, tz=UTC).isoformat(),),
            )
            results["tasks"] = cursor.rowcount
            cursor = conn.execute(
                "DELETE FROM conversation_summaries WHERE created_at < ?",
                (datetime.fromtimestamp(cutoff_summaries, tz=UTC).isoformat(),),
            )
            results["summaries"] = cursor.rowcount
            conn.commit()
        return results

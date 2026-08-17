"""Smart notifications for JARVIS Phase 11."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("jarvis.workflows.notifications")


class SmartNotifier:
    def __init__(self, ws_broadcast: Any | None = None):
        self._broadcast = ws_broadcast
        self._recent: dict[str, list[dict]] = defaultdict(list)
        self._group_window_seconds = 60

    async def notify(self, title: str, message: str, level: str = "info", group_key: str | None = None) -> None:
        timestamp = datetime.utcnow().isoformat()
        entry = {"title": title, "message": message, "level": level, "timestamp": timestamp}

        if group_key:
            self._recent[group_key].append(entry)
            recent = self._recent[group_key]
            if len(recent) > 1:
                entry = self._group_recent(recent, group_key)
            self._recent[group_key] = []

        if self._broadcast:
            try:
                await self._broadcast("notification_created", entry)
            except Exception:
                pass

    def _group_recent(self, recent: list[dict], group_key: str) -> dict:
        count = len(recent)
        latest = recent[-1]
        return {
            "title": latest["title"],
            "message": f"{count} occurrences. Latest: {latest['message']}",
            "level": latest["level"],
            "grouped": True,
            "count": count,
            "timestamp": latest["timestamp"],
        }

    def cleanup(self) -> None:
        self._recent.clear()

"""Reminders system."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("jarvis.memory.reminders")


class ReminderManager:
    """Manage reminders via SQLiteMemory."""

    def __init__(self, memory_manager: Any, notification_callback: Any | None = None):
        self._memory = memory_manager
        self._notify = notification_callback

    def create(self, title: str, description: str = "", due_at: str = "", repeat: str = "once") -> dict:
        reminder = self._memory.store.add_reminder(title, description, due_at, repeat)
        return reminder

    def get(self, enabled: bool | None = None) -> list[dict]:
        return self._memory.store.get_reminders(enabled)

    def update(self, reminder_id: str, updates: dict) -> bool:
        return self._memory.store.update_reminder(reminder_id, updates)

    def delete(self, reminder_id: str) -> bool:
        return self._memory.store.delete_reminder(reminder_id)

    async def check_due(self) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        reminders = self._memory.store.get_reminders(enabled=True)
        due = [r for r in reminders if r.get("due_at", "") <= now and not r.get("notified")]
        for reminder in due:
            self._memory.store.update_reminder(reminder["id"], {"notified": 1})
            if self._notify:
                try:
                    await self._notify(reminder)
                except Exception as exc:
                    logger.warning("Reminder notification failed: %s", exc)
        return due

"""Scheduled messages for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.communications.scheduler")


class ScheduledMessageManager:
    def __init__(self):
        self._scheduled: dict[str, Any] = {}

    def schedule(self, message: Any) -> None:
        self._scheduled[message.schedule_id] = message
        logger.info("Message scheduled: %s at %s", message.schedule_id, message.schedule_time)

    def cancel(self, schedule_id: str) -> bool:
        message = self._scheduled.get(schedule_id)
        if message:
            message.status = "cancelled"
            return True
        return False

    def get(self, schedule_id: str) -> Any | None:
        return self._scheduled.get(schedule_id)

    def list_pending(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._scheduled.values() if m.status == "pending"]

    def list_all(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._scheduled.values()]


scheduled_message_manager = ScheduledMessageManager()

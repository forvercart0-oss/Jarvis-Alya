import logging
from collections import deque
from datetime import datetime
from typing import Any, Optional

from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.notifications")


class NotificationService:
    """In-memory notification hub with WebSocket fan-out."""

    def __init__(self, max_history: int = 50):
        self._history: deque[dict] = deque(maxlen=max_history)
        self._counter = 0

    async def push(self, message: str, ntype: str = "info", data: Optional[dict] = None) -> dict:
        self._counter += 1
        notification = {
            "id": self._counter,
            "message": message,
            "type": ntype,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "data": data or {},
        }
        self._history.appendleft(notification)
        await ws_manager.broadcast("notification", notification)
        logger.info("Notification [%s]: %s", ntype, message)
        return notification

    def recent(self, limit: int = 20) -> list[dict]:
        return list(self._history)[:limit]

    def clear(self):
        self._history.clear()


notification_service = NotificationService()

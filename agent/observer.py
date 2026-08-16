"""Agent observer for JARVIS Phase 2."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("jarvis.agent.observer")


class AgentObserver:
    def __init__(self):
        self._events: list[dict[str, Any]] = []

    def record(self, event_type: str, data: dict[str, Any]) -> None:
        entry = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        self._events.append(entry)
        logger.debug("Agent event: %s", event_type)

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._events[-limit:]

    def clear(self) -> None:
        self._events = []


_observer: AgentObserver | None = None


def get_observer() -> AgentObserver:
    global _observer
    if _observer is None:
        _observer = AgentObserver()
    return _observer

"""Computer sessions for JARVIS Phase 10."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.computer.sessions")


@dataclass
class ComputerSession:
    session_id: str
    mode: str = "off"
    active_window: str = ""
    cursor: dict[str, Any] = field(default_factory=dict)
    monitors: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "active_window": self.active_window,
            "cursor": self.cursor,
            "monitors": self.monitors,
            "actions": self.actions[-50:],
            "tasks": self.tasks[-20:],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ComputerSessionManager:
    def __init__(self):
        self._sessions: dict[str, ComputerSession] = {}

    def create(self, session_id: str) -> ComputerSession:
        session = ComputerSession(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> ComputerSession | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def update(self, session_id: str, **kwargs: Any) -> ComputerSession | None:
        session = self._sessions.get(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
        return session

    def add_action(self, session_id: str, action: dict[str, Any]) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.actions.append(action)

    def add_task(self, session_id: str, task: dict[str, Any]) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.tasks.append(task)


_session_manager: ComputerSessionManager | None = None


def get_computer_session_manager() -> ComputerSessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = ComputerSessionManager()
    return _session_manager

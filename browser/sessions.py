"""Browser sessions for JARVIS Phase 3."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.sessions")


@dataclass
class BrowserSession:
    session_id: str
    url: str = ""
    title: str = ""
    tabs: list[dict[str, str]] = field(default_factory=list)
    active_tab_index: int = 0
    connected: bool = False
    error: str | None = None
    current_structure: list[dict[str, Any]] = field(default_factory=list)
    recent_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "url": self.url,
            "title": self.title,
            "tabs": self.tabs,
            "active_tab_index": self.active_tab_index,
            "connected": self.connected,
            "error": self.error,
            "current_structure": self.current_structure,
            "recent_actions": self.recent_actions[-10:],
        }


class BrowserSessionManager:
    def __init__(self):
        self._sessions: dict[str, BrowserSession] = {}

    def create(self, session_id: str) -> BrowserSession:
        session = BrowserSession(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> BrowserSession | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def update(self, session_id: str, **kwargs: Any) -> BrowserSession | None:
        session = self._sessions.get(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
        return session


_session_manager: BrowserSessionManager | None = None


def get_browser_session_manager() -> BrowserSessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = BrowserSessionManager()
    return _session_manager

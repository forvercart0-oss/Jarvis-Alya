"""Takeover mode for JARVIS Phase 19."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.computer.takeover")


class ComputerTakeover:
    def __init__(self):
        self._takeover_sessions: dict[str, bool] = {}

    def enable(self, session_id: str = "default") -> dict[str, Any]:
        self._takeover_sessions[session_id] = True
        logger.info("Computer takeover enabled for session %s", session_id)
        return {"success": True, "takeover": True, "session_id": session_id}

    def disable(self, session_id: str = "default") -> dict[str, Any]:
        self._takeover_sessions[session_id] = False
        logger.info("Computer takeover disabled for session %s", session_id)
        return {"success": True, "takeover": False, "session_id": session_id}

    def is_takeover(self, session_id: str = "default") -> bool:
        return self._takeover_sessions.get(session_id, False)

    def status(self, session_id: str = "default") -> dict[str, Any]:
        return {"takeover": self.is_takeover(session_id), "session_id": session_id}


computer_takeover = ComputerTakeover()

"""Agent state management for JARVIS Phase 2."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agent.models import AgentContext, AgentPlan, AgentState, AgentTask, TaskStatus

logger = logging.getLogger("jarvis.agent.state")


@dataclass
class AgentSession:
    session_id: str
    state: AgentState = AgentState.IDLE
    context: AgentContext | None = None
    plan: AgentPlan | None = None
    current_task_index: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "context": self.context.to_dict() if self.context else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "current_task_index": self.current_task_index,
            "history": self.history[-50:],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AgentStateManager:
    """Thread-safe agent session state manager."""

    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, context: AgentContext) -> AgentSession:
        session_id = str(uuid.uuid4())[:8]
        session = AgentSession(session_id=session_id, context=context)
        async with self._lock:
            self._sessions[session_id] = session
        logger.info("Created agent session %s", session_id)
        return session

    async def get_session(self, session_id: str) -> AgentSession | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def set_state(self, session_id: str, state: AgentState) -> None:
        session = await self.get_session(session_id)
        if session:
            session.state = state
            session.updated_at = datetime.utcnow()

    async def set_plan(self, session_id: str, plan: AgentPlan) -> None:
        session = await self.get_session(session_id)
        if session:
            session.plan = plan
            session.updated_at = datetime.utcnow()

    async def add_history(self, session_id: str, entry: dict[str, Any]) -> None:
        session = await self.get_session(session_id)
        if session:
            session.history.append(entry)
            session.updated_at = datetime.utcnow()

    async def cancel(self, session_id: str) -> bool:
        session = await self.get_session(session_id)
        if not session:
            return False
        session.state = AgentState.CANCELLED
        session.updated_at = datetime.utcnow()
        if session.plan:
            for task in session.plan.tasks:
                if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                    task.status = TaskStatus.CANCELLED
        return True

    async def cleanup(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)


_state_manager: AgentStateManager | None = None


def get_state_manager() -> AgentStateManager:
    global _state_manager
    if _state_manager is None:
        _state_manager = AgentStateManager()
    return _state_manager

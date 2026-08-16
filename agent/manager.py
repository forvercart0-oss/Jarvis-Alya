"""Agent manager for JARVIS Phase 2."""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from agent.context import AgentContextBuilder
from agent.executor import AgentExecutor
from agent.models import AgentPlan, AgentState
from agent.planner import AgentPlanner
from agent.state import get_state_manager

logger = logging.getLogger("jarvis.agent.manager")


class AgentManager:
    def __init__(
        self,
        tool_execute: Any,
        memory: Any | None = None,
        permission_manager: Any | None = None,
    ):
        self._tool_execute = tool_execute
        self._memory = memory
        self._permission_manager = permission_manager
        self._planner = AgentPlanner(memory=memory)
        self._executor = AgentExecutor(
            tool_execute=tool_execute,
            memory=memory,
            permission_manager=permission_manager,
        )
        self._context_builder = AgentContextBuilder(memory=memory)

    async def start_agent(self, user_request: str, project: str | None = None, project_root: str | None = None, persona: str = "jarvis") -> AsyncGenerator[dict[str, Any], None]:
        context = self._context_builder.build(user_request, project=project, project_root=project_root, persona=persona)
        session = await get_state_manager().create_session(context)
        await get_state_manager().set_state(session.session_id, AgentState.PLANNING)

        plan = self._planner.create_plan(context)
        await get_state_manager().set_plan(session.session_id, plan)

        yield {"event": "agent_started", "data": {"session_id": session.session_id, "context": context.to_dict()}}
        yield {"event": "agent_plan", "data": {"plan": plan.to_dict()}}
        yield {"event": "agent_state_changed", "data": {"state": AgentState.WAITING_APPROVAL.value}}

        async for ev in self._executor.execute_plan(session.session_id, plan):
            yield ev

    async def approve_plan(self, session_id: str) -> AsyncGenerator[dict[str, Any], None]:
        session = await get_state_manager().get_session(session_id)
        if not session or not session.plan:
            yield {"event": "agent_failed", "data": {"error": "Session or plan not found."}}
            return
        session.plan.approved = True
        await get_state_manager().set_state(session_id, AgentState.EXECUTING)
        yield {"event": "agent_state_changed", "data": {"state": AgentState.EXECUTING.value}}
        async for ev in self._executor.execute_plan(session_id, session.plan):
            yield ev

    async def cancel(self, session_id: str) -> dict[str, Any]:
        ok = await get_state_manager().cancel(session_id)
        return {"status": "cancelled" if ok else "not_found", "session_id": session_id}

    async def get_status(self, session_id: str) -> dict[str, Any] | None:
        session = await get_state_manager().get_session(session_id)
        return session.to_dict() if session else None


_agent_manager: AgentManager | None = None


def get_agent_manager(tool_execute: Any, memory: Any | None = None, permission_manager: Any | None = None) -> AgentManager:
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(tool_execute=tool_execute, memory=memory, permission_manager=permission_manager)
    return _agent_manager

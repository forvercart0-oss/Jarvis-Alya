"""Agent manager for JARVIS Phase 20."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from agent.checkpoint import AgentCheckpoint
from agent.context import AgentContextBuilder
from agent.executor import AgentExecutor
from agent.loop import AgentLoop
from agent.models import AgentState, AutonomyLevel
from agent.orchestrator import get_orchestrator
from agent.permissions import AgentPermissions
from agent.planner import AgentPlanner
from agent.state import get_state_manager
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.agent.manager")


class AgentManager:
    def __init__(
        self,
        tool_execute: Any,
        memory: Any | None = None,
        permission_manager: Any | None = None,
        ai_service: Any | None = None,
    ):
        self._tool_execute = tool_execute
        self._memory = memory
        self._permission_manager = permission_manager
        self._ai_service = ai_service
        self._planner = AgentPlanner(memory=memory, ai_service=ai_service)
        self._executor = AgentExecutor(
            tool_execute=tool_execute,
            memory=memory,
            permission_manager=permission_manager,
            ai_service=ai_service,
        )
        self._context_builder = AgentContextBuilder(memory=memory)
        self._permissions = AgentPermissions()
        self._active_loops: dict[str, AgentLoop] = {}

    def get_permissions(self) -> AgentPermissions:
        return self._permissions

    def update_permissions(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if hasattr(self._permissions, key):
                setattr(self._permissions, key, value)

    async def start_agent(
        self,
        user_request: str,
        project: str | None = None,
        project_root: str | None = None,
        persona: str = "jarvis",
        autonomy_level: str = "assisted",
        dry_run: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        context = self._context_builder.build(
            user_request, project=project, project_root=project_root, persona=persona
        )
        context.autonomy_level = AutonomyLevel(autonomy_level)
        context.metadata["dry_run"] = dry_run
        session = await get_state_manager().create_session(context)
        await get_state_manager().set_state(session.session_id, AgentState.PLANNING)

        plan = self._planner.create_plan(context)
        await get_state_manager().set_plan(session.session_id, plan)

        checkpoint = None
        if project_root:
            checkpoint = AgentCheckpoint(project_root)
            cp = checkpoint.create(f"Before: {user_request[:50]}")
            if cp.get("success"):
                session.history.append({"type": "checkpoint", "data": cp})

        await ws_manager.broadcast("agent_started", {"session_id": session.session_id, "context": context.to_dict()})
        yield {"event": "agent_started", "data": {"session_id": session.session_id, "context": context.to_dict()}}
        yield {"event": "agent_plan", "data": {"plan": plan.to_dict()}}

        auto_execute = self._permissions.auto_execute or context.autonomy_level == AutonomyLevel.AUTONOMOUS
        if not auto_execute:
            await get_state_manager().set_state(session.session_id, AgentState.WAITING_FOR_PERMISSION)
            yield {"event": "agent_state_changed", "data": {"state": AgentState.WAITING_FOR_PERMISSION.value}}
            return

        await get_state_manager().set_state(session.session_id, AgentState.EXECUTING)
        yield {"event": "agent_state_changed", "data": {"state": AgentState.EXECUTING.value}}
        loop = AgentLoop(
            tool_execute=self._tool_execute,
            ai_provider=self._ai_service,
            max_retries=self._permissions.max_retries,
            on_event=ws_manager.broadcast,
        )
        self._active_loops[session.session_id] = loop
        async for ev in loop.run(session.session_id, plan):
            yield ev
        self._active_loops.pop(session.session_id, None)

    async def start_orchestrated(
        self,
        user_request: str,
        project: str | None = None,
        project_root: str | None = None,
        persona: str = "jarvis",
        autonomy_level: str = "assisted",
        dry_run: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        orchestrator = get_orchestrator(
            tool_execute=self._tool_execute,
            memory=self._memory,
            permission_manager=self._permission_manager,
            ai_service=self._ai_service,
        )
        yield {"event": "orchestrator_started", "data": {"request": user_request}}
        result = await orchestrator.orchestrate(user_request, autonomy_level=autonomy_level)
        yield {"event": "orchestrator_completed", "data": {"result": result}}

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
        loop = self._active_loops.get(session_id)
        if loop:
            loop.cancel()
        ok = await get_state_manager().cancel(session_id)
        return {"status": "cancelled" if ok else "not_found", "session_id": session_id}

    async def pause(self, session_id: str) -> dict[str, Any]:
        ok = await get_state_manager().pause(session_id)
        return {"status": "paused" if ok else "not_found", "session_id": session_id}

    async def resume(self, session_id: str) -> dict[str, Any]:
        ok = await get_state_manager().resume(session_id)
        return {"status": "resumed" if ok else "not_found", "session_id": session_id}

    async def kill_switch(self, session_id: str) -> dict[str, Any]:
        loop = self._active_loops.get(session_id)
        if loop:
            loop.cancel()
        ok = await get_state_manager().activate_kill_switch(session_id)
        return {"status": "killed" if ok else "not_found", "session_id": session_id}

    async def get_status(self, session_id: str) -> dict[str, Any] | None:
        session = await get_state_manager().get_session(session_id)
        return session.to_dict() if session else None

    async def list_sessions(self) -> list[dict[str, Any]]:
        return await get_state_manager().list_sessions()

    async def rollback(self, session_id: str) -> dict[str, Any]:
        session = await get_state_manager().get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        checkpoints = [h for h in session.history if h.get("type") == "checkpoint"]
        if not checkpoints:
            return {"error": "No checkpoints available"}
        last = checkpoints[-1].get("data", {})
        commit_hash = last.get("commit_hash", "")
        if not commit_hash:
            return {"error": "No commit hash in checkpoint"}
        project_root = session.context.project_root if session.context else None
        if not project_root:
            return {"error": "No project root"}
        cp = AgentCheckpoint(project_root)
        result = cp.rollback(commit_hash)
        return result


_agent_manager: AgentManager | None = None


def get_agent_manager(
    tool_execute: Any,
    memory: Any | None = None,
    permission_manager: Any | None = None,
    ai_service: Any | None = None,
) -> AgentManager:
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(
            tool_execute=tool_execute,
            memory=memory,
            permission_manager=permission_manager,
            ai_service=ai_service,
        )
    return _agent_manager

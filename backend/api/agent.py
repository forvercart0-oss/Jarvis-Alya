"""Agent API for JARVIS 2.0 Phase 15."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.agent")

router = APIRouter()


class AgentStartRequest(BaseModel):
    message: str
    project: str | None = None
    project_root: str | None = None
    persona: str = "jarvis"
    autonomy_level: str = "assisted"
    dry_run: bool = False


class AgentApproveRequest(BaseModel):
    session_id: str


class AgentPermissionsUpdate(BaseModel):
    auto_execute: bool | None = None
    auto_fix: bool | None = None
    max_retries: int | None = None
    confirmation_level: str | None = None
    terminal: str | None = None
    filesystem_delete: str | None = None
    network: str | None = None
    git: str | None = None


class AutonomyUpdate(BaseModel):
    autonomy_level: str


def _get_manager():
    from backend.main import get_agent_manager_instance
    return get_agent_manager_instance()


@router.post("/agent/start")
async def agent_start(request: AgentStartRequest):
    manager = _get_manager()
    events = []
    async for ev in manager.start_agent(
        user_request=request.message,
        project=request.project,
        project_root=request.project_root,
        persona=request.persona,
        autonomy_level=request.autonomy_level,
        dry_run=request.dry_run,
    ):
        events.append(ev)
    return {"status": "started", "events": events}


@router.post("/agent/approve")
async def agent_approve(request: AgentApproveRequest):
    manager = _get_manager()
    events = []
    async for ev in manager.approve_plan(request.session_id):
        events.append(ev)
    return {"status": "approved", "events": events}


@router.post("/agent/cancel")
async def agent_cancel(request: AgentApproveRequest):
    manager = _get_manager()
    result = await manager.cancel(request.session_id)
    return result


@router.post("/agent/pause")
async def agent_pause(request: AgentApproveRequest):
    manager = _get_manager()
    result = await manager.pause(request.session_id)
    return result


@router.post("/agent/resume")
async def agent_resume(request: AgentApproveRequest):
    manager = _get_manager()
    result = await manager.resume(request.session_id)
    return result


@router.post("/agent/kill")
async def agent_kill(request: AgentApproveRequest):
    manager = _get_manager()
    result = await manager.kill_switch(request.session_id)
    return result


@router.get("/agent/status/{session_id}")
async def agent_status(session_id: str):
    manager = _get_manager()
    status = await manager.get_status(session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return status


@router.get("/agent/sessions")
async def agent_sessions():
    manager = _get_manager()
    sessions = await manager.list_sessions()
    return {"sessions": sessions}


@router.post("/agent/rollback")
async def agent_rollback(request: AgentApproveRequest):
    manager = _get_manager()
    result = await manager.rollback(request.session_id)
    return result


@router.get("/agent/permissions")
async def agent_permissions():
    manager = _get_manager()
    return {"permissions": manager.get_permissions().to_dict()}


@router.put("/agent/permissions")
async def agent_permissions_update(update: AgentPermissionsUpdate):
    manager = _get_manager()
    updates = update.model_dump(exclude_none=True)
    manager.update_permissions(updates)
    return {"permissions": manager.get_permissions().to_dict()}


@router.put("/agent/autonomy")
async def agent_autonomy_update(update: AutonomyUpdate):
    manager = _get_manager()
    manager.update_permissions({"autonomy_level": update.autonomy_level})
    return {"autonomy_level": update.autonomy_level}


class OrchestrateRequest(BaseModel):
    message: str
    persona: str = "jarvis"
    autonomy_level: str = "assisted"


@router.post("/agent/orchestrate")
async def agent_orchestrate(request: OrchestrateRequest):
    manager = _get_manager()
    events = []
    async for ev in manager.start_orchestrated(
        user_request=request.message,
        persona=request.persona,
        autonomy_level=request.autonomy_level,
    ):
        events.append(ev)
    return {"status": "orchestrated", "events": events}


@router.get("/agent/registry")
async def agent_registry_list():
    from agent.registry import agent_registry
    return {"agents": agent_registry.list_agents()}


@router.get("/agent/orchestrator/tasks")
async def orchestrator_tasks():
    from agent.orchestrator import get_orchestrator
    orch = get_orchestrator()
    return {"tasks": orch.list_tasks()}


@router.get("/agent/orchestrator/tasks/{task_id}")
async def orchestrator_task(task_id: str):
    from agent.orchestrator import get_orchestrator
    orch = get_orchestrator()
    result = orch.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.post("/agent/orchestrator/tasks/{task_id}/cancel")
async def orchestrator_cancel(task_id: str):
    from agent.orchestrator import get_orchestrator
    orch = get_orchestrator()
    result = await orch.cancel(task_id)
    return result

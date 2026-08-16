"""Agent API for JARVIS 2.0 Phase 2."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.models import AgentState
from agent.state import get_state_manager

logger = logging.getLogger("jarvis.api.agent")

router = APIRouter()


class AgentStartRequest(BaseModel):
    message: str
    project: str | None = None
    project_root: str | None = None
    persona: str = "jarvis"


class AgentApproveRequest(BaseModel):
    session_id: str


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


@router.get("/agent/status/{session_id}")
async def agent_status(session_id: str):
    manager = _get_manager()
    status = await manager.get_status(session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return status


@router.get("/agent/sessions")
async def agent_sessions():
    state_mgr = get_state_manager()
    return {"sessions": []}

"""Phase 23 API endpoints for autonomous intelligence."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

logger = logging.getLogger("jarvis.api.phase23")

router = APIRouter()


class GoalRequest(BaseModel):
    request: str
    context: dict[str, Any] | None = None


class GoalControlRequest(BaseModel):
    goal_id: str


def _get_orchestrator():
    from agent.orchestrator_v2 import get_autonomous_orchestrator
    return get_autonomous_orchestrator()


@router.post("/goals")
async def create_goal(request: GoalRequest):
    orchestrator = _get_orchestrator()
    result = await orchestrator.execute_goal(request.request, request.context)
    return result


@router.get("/goals")
async def list_goals():
    orchestrator = _get_orchestrator()
    return {"goals": orchestrator.list_goals()}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    orchestrator = _get_orchestrator()
    goal = orchestrator.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.post("/goals/{goal_id}/pause")
async def pause_goal(goal_id: str):
    orchestrator = _get_orchestrator()
    result = await orchestrator.pause_goal(goal_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.post("/goals/{goal_id}/resume")
async def resume_goal(goal_id: str):
    orchestrator = _get_orchestrator()
    result = await orchestrator.resume_goal(goal_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.post("/goals/{goal_id}/cancel")
async def cancel_goal(goal_id: str):
    orchestrator = _get_orchestrator()
    result = await orchestrator.cancel_goal(goal_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/agents")
async def list_agents():
    from agent.registry_v2 import agent_registry_v2
    return {"agents": agent_registry_v2.list_agents()}


@router.get("/artifacts")
async def list_artifacts(goal_id: str = ""):
    from agent.artifact_manager import artifact_manager
    artifacts = artifact_manager.list_by_goal(goal_id) if goal_id else list(artifact_manager._artifacts.values())
    return {"artifacts": [a.to_dict() for a in artifacts]}


@router.get("/resources")
async def get_resources():
    from agent.resource_manager import resource_manager
    resources = resource_manager.get_resources()
    return {
        "cpu_percent": resources.cpu_percent,
        "ram_percent": resources.ram_percent,
        "ram_available_mb": resources.ram_available_mb,
        "gpu_available": resources.gpu_available,
        "active_processes": resources.active_processes,
        "max_parallel_agents": resource_manager.get_max_parallel_agents(),
    }

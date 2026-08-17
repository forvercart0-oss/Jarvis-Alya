"""Task API for JARVIS Phase 5."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.tasks")

router = APIRouter()


class TaskCreateRequest(BaseModel):
    description: str
    task_type: str = "general"
    auto_execute: bool = False
    context: dict[str, Any] | None = None


class TaskControlRequest(BaseModel):
    task_id: str


class TaskPlanRequest(BaseModel):
    task_id: str
    approved: bool = False


def _get_manager():
    from backend.main import task_manager
    return task_manager


@router.get("/tasks")
async def list_tasks(status: str | None = None):
    manager = _get_manager()
    return manager.get_tasks(status=status)


@router.get("/tasks/active")
async def list_active_tasks():
    manager = _get_manager()
    return manager.get_active_tasks()


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    manager = _get_manager()
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    manager = _get_manager()
    task = await manager.create_task(
        description=request.description,
        task_type=request.task_type,
        auto_execute=request.auto_execute,
        context=request.context,
    )
    return task


@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str):
    manager = _get_manager()
    result = await manager.start_task(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    manager = _get_manager()
    result = await manager.pause_task(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    manager = _get_manager()
    result = await manager.resume_task(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    manager = _get_manager()
    result = await manager.cancel_task(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    manager = _get_manager()
    result = await manager.approve_plan(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/tasks/{task_id}/deny")
async def deny_task(task_id: str):
    manager = _get_manager()
    result = await manager.deny_plan(task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    manager = _get_manager()
    ok = manager.store.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted"}


@router.get("/tasks/history")
async def get_task_history(limit: int = 50):
    manager = _get_manager()
    return manager.get_task_history(limit=limit)


@router.post("/tasks/advanced")
async def create_task_advanced(request: dict):
    manager = _get_manager()
    description = request.get("description", "")
    task_type = request.get("task_type", "general")
    auto_execute = request.get("auto_execute", False)
    context = request.get("context")
    dry_run = request.get("dry_run", False)
    if not description:
        raise HTTPException(status_code=400, detail="description is required")
    result = manager.create_task_with_routing(description, task_type=task_type, auto_execute=auto_execute, context=context, dry_run=dry_run)
    return result


@router.get("/tasks/queue")
async def get_task_queue():
    manager = _get_manager()
    return {"queue": manager.get_queue()}


@router.get("/tasks/processes")
async def get_task_processes():
    manager = _get_manager()
    return {"processes": manager.get_processes()}


@router.post("/tasks/autonomy")
async def set_autonomy_level(request: dict):
    manager = _get_manager()
    level = request.get("level", "balanced")
    try:
        manager.set_autonomy_level(level)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"level": manager.get_autonomy_level()}


@router.get("/tasks/project/{project}")
async def get_tasks_by_project(project: str):
    manager = _get_manager()
    return manager.get_tasks_by_project(project)

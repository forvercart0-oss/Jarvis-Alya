"""Workflow API for JARVIS 2.0 Phase 11."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.workflows")

router = APIRouter()


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str = ""
    trigger: dict[str, Any] | None = None
    steps: list[dict[str, Any]] | None = None
    variables: dict[str, Any] | None = None
    permissions: dict[str, Any] | None = None
    enabled: bool = False
    project: str | None = None
    tags: list[str] | None = None


class WorkflowUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger: dict[str, Any] | None = None
    steps: list[dict[str, Any]] | None = None
    variables: dict[str, Any] | None = None
    permissions: dict[str, Any] | None = None
    enabled: bool | None = None
    project: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class ApprovalActionRequest(BaseModel):
    action: str


def _get_store():
    from backend.main import memory_manager
    from workflows.store import WorkflowStore
    return WorkflowStore(memory_manager)


def _get_engine():
    from backend.main import ai_service, tool_registry, ws_manager
    from workflows.engine import WorkflowEngine
    return WorkflowEngine(
        tool_execute=lambda name, confirmed=False, **kwargs: tool_registry.execute(name, confirmed=confirmed, **kwargs),
        ai_service=ai_service,
        ws_broadcast=ws_manager.broadcast,
    )


@router.get("/workflows")
async def list_workflows(status: str | None = None, limit: int = 50):
    store = _get_store()
    return {"workflows": store.get_workflows(status=status, limit=limit)}


@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    from workflows.models import Workflow
    store = _get_store()
    workflow = Workflow(
        name=request.name,
        description=request.description,
        trigger=request.trigger or {},
        steps=[__import__("workflows.models", fromlist=["WorkflowStep"]).WorkflowStep.from_dict(s) for s in (request.steps or [])],
        variables=request.variables or {},
        permissions=request.permissions or {},
        enabled=request.enabled,
        project=request.project,
        tags=request.tags or [],
    )
    result = store.create_workflow(workflow)
    return result


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    store = _get_store()
    result = store.get_workflow(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.put("/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, request: WorkflowUpdateRequest):
    store = _get_store()
    updates = {k: v for k, v in request.__dict__.items() if v is not None}
    if "steps" in updates:
        from workflows.models import WorkflowStep
        updates["steps"] = [WorkflowStep.from_dict(s) for s in updates["steps"]]
    result = store.update_workflow(workflow_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    store = _get_store()
    ok = store.delete_workflow(workflow_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"status": "deleted"}


@router.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    store = _get_store()
    result = store.get_workflow(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    engine = _get_engine()
    from workflows.models import Workflow
    workflow = Workflow.from_dict(result)
    run_id = str(__import__("uuid").uuid4())[:8]
    store.update_workflow(workflow_id, {"status": "running"})
    return {"status": "started", "workflow_id": workflow_id, "run_id": run_id}


@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    store = _get_store()
    result = store.update_workflow(workflow_id, {"status": "paused", "enabled": False})
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.post("/workflows/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    store = _get_store()
    result = store.update_workflow(workflow_id, {"status": "active", "enabled": True})
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    store = _get_store()
    result = store.update_workflow(workflow_id, {"status": "cancelled", "enabled": False})
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/workflows/{workflow_id}/runs")
async def get_workflow_runs(workflow_id: str, limit: int = 50):
    store = _get_store()
    return {"runs": store.get_runs(workflow_id, limit=limit)}


@router.get("/approvals")
async def list_approvals(status: str | None = None):
    store = _get_store()
    return {"approvals": store.get_approvals(status=status)}


@router.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: str):
    store = _get_store()
    result = store.update_approval(approval_id, {"status": "approved"})
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found")
    return result


@router.post("/approvals/{approval_id}/deny")
async def deny_request(approval_id: str):
    store = _get_store()
    result = store.update_approval(approval_id, {"status": "denied"})
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found")
    return result

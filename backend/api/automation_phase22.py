"""Automation API for JARVIS Phase 22.

Provides endpoints for:
- Execution mode
- Automation profiles
- Authorization scopes
- Policy evaluation
- Emergency stop
- Automation dashboard
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.automation")

router = APIRouter()


class ExecutionModeRequest(BaseModel):
    mode: str


class AutomationScopeRequest(BaseModel):
    scope: str
    enabled: bool


class AutomationProfileRequest(BaseModel):
    profile: str


class EmergencyStopRequest(BaseModel):
    task_ids: list[str] | None = None


def _get_policy():
    from backend.main import automation_policy_engine
    return automation_policy_engine


def _get_task_manager():
    from backend.main import task_manager
    return task_manager


@router.get("/automation/mode")
async def get_execution_mode():
    from config.settings import get_settings
    settings = get_settings()
    policy = _get_policy()
    return {
        "mode": settings.execution_mode,
        "profile": settings.automation_profile,
        "scopes": policy.get_enabled_scopes(),
    }


@router.post("/automation/mode")
async def set_execution_mode(request: ExecutionModeRequest):
    from config.settings import get_settings
    settings = get_settings()
    mode = request.mode.lower()
    if mode not in ("assisted", "full_auto", "safe"):
        raise HTTPException(status_code=400, detail="Invalid execution mode")
    settings.execution_mode = mode
    policy = _get_policy()
    policy.set_execution_mode(mode)
    settings.persist()
    return {"mode": settings.execution_mode}


@router.get("/automation/profile")
async def get_automation_profile():
    policy = _get_policy()
    return policy.get_profile_summary()


@router.post("/automation/profile")
async def set_automation_profile(request: AutomationProfileRequest):
    from config.settings import get_settings
    settings = get_settings()
    profile = request.profile.lower()
    policy = _get_policy()
    if profile not in policy.get_profile_summary().get("available_profiles", []):
        raise HTTPException(status_code=400, detail="Invalid profile")
    settings.automation_profile = profile
    policy.set_profile(profile)
    settings.persist()
    return policy.get_profile_summary()


@router.get("/automation/scopes")
async def get_automation_scopes():
    policy = _get_policy()
    return policy.get_scope_summary()


@router.post("/automation/scopes")
async def set_automation_scope(request: AutomationScopeRequest):
    from config.settings import get_settings
    settings = get_settings()
    scope = request.scope.lower()
    policy = _get_policy()
    policy.set_scope(scope, request.enabled)
    scope_map = {
        "files": "automation_scope_files",
        "terminal": "automation_scope_terminal",
        "browser": "automation_scope_browser",
        "applications": "automation_scope_applications",
        "system": "automation_scope_system",
        "coding": "automation_scope_coding",
        "documents": "automation_scope_documents",
        "network": "automation_scope_network",
        "communication": "automation_scope_communication",
        "vision": "automation_scope_vision",
        "automation": "automation_scope_automation",
    }
    setting_key = scope_map.get(scope)
    if setting_key and hasattr(settings, setting_key):
        setattr(settings, setting_key, request.enabled)
        settings.persist()
    return {"scope": scope, "enabled": request.enabled}


@router.post("/automation/emergency-stop")
async def emergency_stop(request: EmergencyStopRequest):
    task_mgr = _get_task_manager()
    task_ids = request.task_ids or [t["id"] for t in task_mgr.get_active_tasks()]
    results = []
    for task_id in task_ids:
        try:
            result = await task_mgr.cancel_task(task_id)
            results.append(result)
        except Exception as exc:
            results.append({"task_id": task_id, "error": str(exc)})
    return {"stopped": len(results), "results": results}


@router.get("/automation/dashboard")
async def get_automation_dashboard():
    task_mgr = _get_task_manager()
    policy = _get_policy()
    tasks = task_mgr.get_tasks()
    active = [t for t in tasks if t.get("status") in ("pending", "planning", "running", "waiting", "paused", "verifying")]
    completed = [t for t in tasks if t.get("status") == "completed"]
    failed = [t for t in tasks if t.get("status") in ("failed", "cancelled")]
    return {
        "execution_mode": policy.execution_mode.value,
        "profile": policy.profile,
        "active_tasks": len(active),
        "completed_tasks": len(completed),
        "failed_tasks": len(failed),
        "total_tasks": len(tasks),
        "scopes": policy.get_enabled_scopes(),
    }


@router.get("/automation/evaluate")
async def evaluate_tool(tool_name: str, confirmed: bool = False):
    policy = _get_policy()
    action, message = policy.evaluate_tool(tool_name, confirmed=confirmed)
    return {
        "tool": tool_name,
        "action": action.value,
        "message": message,
        "auto_execute": policy.should_auto_execute(tool_name),
    }

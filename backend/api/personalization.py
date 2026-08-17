"""Personalization API for JARVIS Phase 21."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.personalization")

router = APIRouter()


class PreferenceRequest(BaseModel):
    key: str
    value: str
    source: str = "explicit_user"
    confidence: str = "high"
    profile: str = "jarvis"
    project: str = ""
    session_id: str = ""


class ForgetRequest(BaseModel):
    preference_id: str = ""
    key: str = ""
    profile: str = "jarvis"


class FeedbackRequest(BaseModel):
    user_message: str
    assistant_response: str
    feedback: str
    profile: str = "jarvis"


class ImportRequest(BaseModel):
    data: dict
    profile: str = "jarvis"


class WorkflowActionRequest(BaseModel):
    action: str
    tool: str
    arguments: dict


@router.get("/personalization")
async def get_personalization(profile: str = "jarvis"):
    from backend.main import memory_service
    context = memory_service.get_personalization_context(profile=profile)
    suggestions = memory_service.get_suggestions(profile=profile)
    return {
        "context": context,
        "suggestions": suggestions,
        "profile": profile,
    }


@router.get("/personalization/preferences")
async def get_preferences(profile: str = "jarvis", project: str = "", session_id: str = ""):
    from backend.main import memory_service
    return memory_service.get_adaptive_preferences(profile=profile, project=project, session_id=session_id)


@router.post("/personalization/preferences")
async def set_preference(request: PreferenceRequest):
    from backend.main import memory_service
    if not request.key or not request.value:
        raise HTTPException(status_code=400, detail="key and value are required")
    result = memory_service.remember_adaptive_preference(
        key=request.key,
        value=request.value,
        source=request.source,
        confidence=request.confidence,
        profile=request.profile,
        project=request.project,
        session_id=request.session_id,
    )
    return result


@router.patch("/personalization/preferences/{preference_id}")
async def update_preference(preference_id: str, request: PreferenceRequest):
    from backend.main import memory_service
    prefs = memory_service.get_adaptive_preferences(profile=request.profile)
    target = next((p for p in prefs if p.get("preference_id") == preference_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Preference not found")
    result = memory_service.remember_adaptive_preference(
        key=request.key or target.get("key", ""),
        value=request.value or target.get("value", ""),
        source=request.source or target.get("source", "explicit_user"),
        confidence=request.confidence or target.get("confidence", "high"),
        profile=request.profile,
        project=request.project,
        session_id=request.session_id,
    )
    return result


@router.delete("/personalization/preferences/{preference_id}")
async def delete_preference(preference_id: str):
    from backend.main import memory_service
    ok = memory_service.forget_adaptive_preference(preference_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"status": "forgotten"}


@router.post("/personalization/forget")
async def forget_preference(request: ForgetRequest):
    from backend.main import memory_service
    if request.preference_id:
        ok = memory_service.forget_adaptive_preference(request.preference_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Preference not found")
        return {"status": "forgotten"}
    if request.key:
        count = memory_service.forget_adaptive_key(request.key, profile=request.profile)
        return {"status": "forgotten", "count": count}
    raise HTTPException(status_code=400, detail="preference_id or key is required")


@router.get("/personalization/suggestions")
async def get_suggestions(profile: str = "jarvis"):
    from backend.main import memory_service
    return {"suggestions": memory_service.get_suggestions(profile=profile)}


@router.get("/personalization/environment")
async def get_environment():
    from memory.environment import environment_profiler
    profile = environment_profiler.get_profile()
    return profile.to_dict()


@router.get("/personalization/analytics")
async def get_analytics(profile: str = "jarvis"):
    from backend.main import memory_service
    outcomes = memory_service.adaptive._task_outcomes if hasattr(memory_service.adaptive, '_task_outcomes') else []
    total = len(outcomes)
    successes = sum(1 for o in outcomes if o.get("success"))
    return {
        "tasks_completed": total,
        "tasks_failed": total - successes,
        "success_rate": successes / total if total else 0,
        "sample_size": total,
        "profile": profile,
    }


@router.post("/personalization/feedback")
async def record_feedback(request: FeedbackRequest):
    from backend.main import memory_service
    from personality.manager import get_personality_engine
    engine = get_personality_engine(memory_manager=memory_service)
    result = engine.process_feedback(request.user_message, request.assistant_response, request.feedback)
    return {"status": "recorded", "learned": result}


@router.post("/personalization/export")
async def export_personalization(profile: str = "jarvis"):
    from backend.main import memory_service
    return memory_service.export_personalization(profile=profile)


@router.post("/personalization/import")
async def import_personalization(request: ImportRequest):
    from backend.main import memory_service
    count = memory_service.import_personalization(request.data, profile=request.profile)
    return {"status": "imported", "count": count}


@router.post("/personalization/workflow/record")
async def record_workflow_action(request: WorkflowActionRequest):
    from memory.workflows import workflow_detector
    workflow_detector.record_action(request.action, request.tool, request.arguments)
    return {"status": "recorded"}


@router.get("/personalization/workflows")
async def get_workflows(profile: str = "jarvis"):
    from backend.main import memory_service
    return {"workflows": memory_service.adaptive.get_workflows()}


@router.post("/personalization/task-outcome")
async def record_task_outcome(request: dict):
    from backend.main import memory_service
    memory_service.record_task_outcome(
        task_type=request.get("task_type", "general"),
        agents_used=request.get("agents_used", []),
        tools_used=request.get("tools_used", []),
        duration_ms=int(request.get("duration_ms", 0)),
        success=bool(request.get("success", False)),
        user_feedback=request.get("user_feedback", ""),
        retry_count=int(request.get("retry_count", 0)),
        provider=request.get("provider", ""),
    )
    return {"status": "recorded"}

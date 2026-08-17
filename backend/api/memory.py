"""Memory API for JARVIS Phase 6."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from memory.manager import SecretMemoryError

logger = logging.getLogger("jarvis.api.memory")

router = APIRouter()


class MemoryRequest(BaseModel):
    content: str
    category: str | None = "general"
    confidence: float = 1.0
    source: str = "explicit_user"
    project: str = ""
    profile: str = "jarvis"
    expires_at: str | None = None


class MemorySearchRequest(BaseModel):
    query: str
    category: str | None = None
    project: str | None = None
    profile: str | None = None
    min_confidence: float = 0.0
    limit: int = 20


class PreferenceRequest(BaseModel):
    key: str
    value: str
    profile: str = "jarvis"


class SummaryRequest(BaseModel):
    conversation_id: str
    summary: str
    message_count: int = 0


class PrivacyRequest(BaseModel):
    mode: str


@router.get("/memory")
async def get_memories(category: str | None = None, project: str | None = None, profile: str | None = None):
    from backend.main import memory_service
    return memory_service.get_all_memories(category=category, project=project, profile=profile)


@router.get("/memory/search")
async def search_memories(
    query: str,
    category: str | None = None,
    project: str | None = None,
    profile: str | None = None,
    min_confidence: float = 0.0,
    limit: int = 20,
):
    from backend.main import memory_service
    return memory_service.search(
        query, category=category, project=project, profile=profile,
        min_confidence=min_confidence, limit=limit,
    )


@router.get("/memory/stats")
async def get_memory_stats():
    from backend.main import memory_service
    return memory_service.get_stats()


@router.get("/memory/categories")
async def get_memory_categories():
    from backend.main import memory_service
    return {"categories": memory_service.categories()}


@router.post("/memory")
async def add_memory(request: MemoryRequest):
    from backend.main import memory_service
    try:
        memory_service.memory.long_term.remember(
            request.content,
            category=request.category or "general",
            confidence=request.confidence,
            source=request.source,
            project=request.project,
            profile=request.profile,
            expires_at=request.expires_at,
        )
    except SecretMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "remembered"}


@router.patch("/memory/{memory_id}")
async def update_memory(memory_id: str, request: MemoryRequest):
    from backend.main import memory_service
    memory = memory_service.memory.long_term.update(
        memory_id, request.content, confidence=request.confidence, source=request.source,
    )
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "updated"}


@router.delete("/memory")
async def clear_all_memories():
    from backend.main import memory_service
    count = memory_service.clear_all()
    return {"status": "cleared", "count": count}


@router.get("/memory/conversations")
async def get_conversations(limit: int = 50):
    from backend.main import memory_service
    return memory_service.get_conversations(limit)


@router.get("/memory/conversations/{conv_id}")
async def get_conversation(conv_id: str, limit: int = 100):
    from backend.main import memory_service
    return memory_service.get_messages(conv_id, limit)


@router.delete("/memory/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    from backend.main import memory_service
    memory_service.delete_conversation(conv_id)
    return {"status": "deleted"}


@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    from backend.main import memory_service
    memory = memory_service.get_memory_by_id(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str):
    from backend.main import memory_service
    if not memory_service.delete_by_id(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "forgotten"}


@router.get("/memory/preferences")
async def get_preferences(profile: str = "jarvis"):
    from backend.main import memory_service
    return memory_service.get_preferences(profile=profile)


@router.post("/memory/preferences")
async def set_preference(request: PreferenceRequest):
    from backend.main import memory_service
    memory_service.set_preference(request.key, request.value, profile=request.profile)
    return {"status": "remembered"}


@router.get("/memory/projects")
async def list_projects():
    from backend.main import memory_service
    return {"projects": memory_service.get_projects()}


@router.get("/memory/projects/{project}")
async def get_project_memory(project: str, query: str = "", limit: int = 50):
    from backend.main import memory_service
    return memory_service.get_project_memory(project, query=query, limit=limit)


@router.get("/memory/summaries")
async def get_summaries(conversation_id: str | None = None, limit: int = 50):
    from backend.main import memory_service
    return memory_service.get_summaries(conversation_id, limit)


@router.post("/memory/summaries")
async def create_summary(request: SummaryRequest):
    from backend.main import memory_service
    return memory_service.create_summary(request.conversation_id, request.summary, request.message_count)


@router.get("/memory/privacy")
async def get_privacy():
    from backend.main import memory_service
    return memory_service.get_privacy_settings()


@router.post("/memory/privacy")
async def set_privacy(request: PrivacyRequest):
    from backend.main import memory_service
    memory_service.set_privacy_mode(request.mode)
    return {"status": "updated"}


@router.get("/memory/health")
async def memory_health():
    from backend.main import memory_service
    return memory_service.get_health()


@router.get("/memory/ranked")
async def search_memories_ranked(
    query: str = "",
    category: str | None = None,
    project: str | None = None,
    profile: str | None = None,
    min_confidence: float = 0.0,
    limit: int = 20,
):
    from backend.main import memory_service
    return memory_service.search_with_ranking(
        query=query, category=category, project=project, profile=profile,
        min_confidence=min_confidence, limit=limit,
    )


@router.get("/memory/context")
async def get_memory_context(
    query: str,
    project: str | None = None,
    profile: str = "jarvis",
    max_memories: int = 8,
    max_tokens: int = 2000,
):
    from backend.main import memory_service
    return memory_service.build_context(
        query, project=project, profile=profile,
        max_memories=max_memories, max_tokens=max_tokens,
    )


@router.get("/memory/duplicates")
async def get_duplicates(threshold: float = 0.85):
    from backend.main import memory_service
    return {"duplicates": memory_service.detect_duplicates(threshold=threshold)}


@router.get("/memory/contradictions")
async def get_contradictions():
    from backend.main import memory_service
    return {"contradictions": memory_service.detect_contradictions()}


@router.post("/memory/decay")
async def apply_memory_decay(decay_rate: float = 0.01):
    from backend.main import memory_service
    updated = memory_service.apply_decay(decay_rate=decay_rate)
    return {"updated": updated}


@router.get("/memory/{memory_id}/related")
async def get_related_memories(memory_id: str, limit: int = 10):
    from backend.main import memory_service
    return {"related": memory_service.get_related_memories(memory_id, limit=limit)}


@router.post("/memory/export")
async def export_memories(category: str | None = None, project: str | None = None, profile: str | None = None):
    from backend.main import memory_service
    return memory_service.export_memories(category=category, project=project, profile=profile)


@router.post("/memory/import")
async def import_memories(request: dict):
    from backend.main import memory_service
    mode = request.get("mode", "merge")
    data = request.get("data", {})
    return memory_service.import_memories(data, mode=mode)


@router.patch("/memory/{memory_id}")
async def update_memory_fields(memory_id: str, updates: dict):
    from backend.main import memory_service
    updated = memory_service.update_memory_fields(memory_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found")
    return updated


@router.get("/memory/dashboard")
async def get_memory_dashboard():
    from backend.main import memory_service
    return memory_service.get_memory_dashboard()


@router.post("/memory/confirm")
async def confirm_memory(request: dict):
    from backend.main import memory_service
    content = request.get("content", "")
    category = request.get("category", "general")
    importance = request.get("importance", "medium")
    memory_type = request.get("memory_type")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    result = memory_service.remember_with_confirmation(
        content, category=category, importance=importance, memory_type=memory_type,
    )
    return result


@router.post("/memory/session")
async def remember_session(request: dict):
    from backend.main import memory_service
    session_id = request.get("session_id", "")
    content = request.get("content", "")
    if not session_id or not content:
        raise HTTPException(status_code=400, detail="session_id and content are required")
    result = memory_service.remember_session(
        session_id, content,
        category=request.get("category", "general"),
        memory_type=request.get("memory_type", "fact"),
        importance=float(request.get("importance", 0.5)),
        expires_at=request.get("expires_at"),
    )
    return result


@router.get("/memory/session/{session_id}")
async def get_session_memories(session_id: str, limit: int = 50):
    from backend.main import memory_service
    return {"memories": memory_service.get_session_memories(session_id, limit=limit)}


@router.delete("/memory/session/{session_id}")
async def clear_session_memories(session_id: str):
    from backend.main import memory_service
    count = memory_service.clear_session_memories(session_id)
    return {"status": "cleared", "count": count}


@router.get("/memory/audit")
async def get_memory_audit(limit: int = 100):
    from backend.main import memory_service
    return {"audit": memory_service.audit.get_recent(limit=limit)}


@router.post("/memory/conflicts/resolve")
async def resolve_memory_conflict(request: dict):
    from backend.main import memory_service
    memory_id = request.get("memory_id", "")
    keep = request.get("keep", True)
    if not memory_id:
        raise HTTPException(status_code=400, detail="memory_id is required")
    result = memory_service.resolve_conflict(memory_id, keep=keep)
    if not result:
        raise HTTPException(status_code=404, detail="Memory not found")
    return result

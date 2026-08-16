"""Memory API for JARVIS Phase 6."""

from __future__ import annotations

import logging
from typing import Any

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
async def search_memories(query: str, category: str | None = None, project: str | None = None, profile: str | None = None, min_confidence: float = 0.0, limit: int = 20):
    from backend.main import memory_service
    return memory_service.search(query, category=category, project=project, profile=profile, min_confidence=min_confidence, limit=limit)


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
    memory = memory_service.memory.long_term.update(memory_id, request.content, confidence=request.confidence, source=request.source)
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

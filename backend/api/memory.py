from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.memory_service import MemoryService

router = APIRouter()


class MemoryRequest(BaseModel):
    content: str
    category: Optional[str] = "general"


@router.get("/memory")
async def get_memories():
    from backend.main import memory_service
    return memory_service.get_all_memories()


@router.post("/memory")
async def add_memory(request: MemoryRequest):
    from backend.main import memory_service
    memory_service.remember(request.content, request.category or "general")
    return {"status": "remembered"}


@router.delete("/memory/{key}")
async def delete_memory(key: str):
    from backend.main import memory_service
    memory_service.forget(key)
    return {"status": "forgotten"}


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

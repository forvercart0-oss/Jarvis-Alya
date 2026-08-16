
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from memory.manager import SecretMemoryError

router = APIRouter()


class MemoryRequest(BaseModel):
    content: str
    category: str | None = "general"


@router.get("/memory")
async def get_memories():
    from backend.main import memory_service
    return memory_service.get_all_memories()


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
        memory_service.remember(request.content, request.category or "general")
    except SecretMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "remembered"}


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

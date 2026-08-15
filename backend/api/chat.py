from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.services.ai_service import AIService
from backend.services.memory_service import MemoryService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    from backend.main import ai_service
    full_response = ""
    conv_id = request.conversation_id
    try:
        async for event in ai_service.process_message(request.message, conversation_id=request.conversation_id):
            if event["event"] == "response" and "chunk" in event["data"]:
                full_response += event["data"]["chunk"]
            if event["event"] == "token" and "chunk" in event["data"]:
                full_response += event["data"]["chunk"]
            if event["event"] == "done":
                conv_id = event["data"].get("conversation_id", conv_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ChatResponse(response=full_response or "No response generated.", conversation_id=conv_id or "")

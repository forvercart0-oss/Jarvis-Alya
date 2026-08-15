from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.services.ai_service import AIService
from backend.services.memory_service import MemoryService
from generation.image.manager import ImageGenerationManager
from generation.video.manager import VideoGenerationManager

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class ImageGenRequest(BaseModel):
    prompt: str
    provider: str = "auto"
    width: int = 1024
    height: int = 1024
    negative_prompt: str = ""


class VideoGenRequest(BaseModel):
    prompt: str
    provider: str = "auto"
    duration: int = 5
    resolution: str = "720p"
    aspect_ratio: str = "16:9"


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


@router.post("/generate/image")
async def generate_image(request: ImageGenRequest):
    from backend.main import ai_service
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    mgr = ImageGenerationManager(ai_service.settings)
    result = await mgr.generate(request.prompt, provider=None if request.provider == "auto" else request.provider, width=request.width, height=request.height, negative_prompt=request.negative_prompt)
    return result


@router.post("/generate/video")
async def generate_video(request: VideoGenRequest):
    from backend.main import ai_service
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    mgr = VideoGenerationManager(ai_service.settings)
    result = await mgr.generate(request.prompt, provider=None if request.provider == "auto" else request.provider, duration=request.duration, resolution=request.resolution, aspect_ratio=request.aspect_ratio)
    return result


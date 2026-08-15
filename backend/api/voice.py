from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str


class ListenResponse(BaseModel):
    transcript: Optional[str] = None
    error: Optional[str] = None


@router.post("/voice/speak")
async def speak(request: SpeakRequest):
    from backend.main import voice_service
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    success = await voice_service.speak(request.text)
    if not success:
        raise HTTPException(status_code=500, detail="TTS failed.")
    return {"status": "spoken"}


@router.post("/voice/listen", response_model=ListenResponse)
async def listen():
    from backend.main import voice_service
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    try:
        text = await voice_service.listen()
        return ListenResponse(transcript=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/test")
async def test_voice(request: SpeakRequest):
    from backend.main import voice_service
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    success = await voice_service.speak_now(request.text or "Hello! This is JARVIS speaking.")
    if not success:
        raise HTTPException(status_code=500, detail="TTS test failed.")
    return {"status": "tested"}


@router.get("/voice/voices")
async def list_voices():
    from backend.main import voice_service, tts_manager
    if not voice_service:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    return {
        "voices": voice_service.list_voices(),
        "catalog": voice_service.voice_catalog(),
        "current": tts_manager.settings.tts_voice,
        "engine": tts_manager.engine,
        "backend": tts_manager.backend,
        "tts_available": voice_service.tts_available,
        "mic_available": voice_service.mic_available,
    }


@router.get("/voice/status")
async def voice_status():
    from backend.main import voice_service, tts_manager
    return {
        "initialized": voice_service.initialized,
        "mic_available": voice_service.mic_available,
        "tts_available": tts_manager.is_available(),
        "tts_backend": tts_manager.backend,
        "tts_engine": tts_manager.engine,
        "speaking": tts_manager.is_speaking(),
    }

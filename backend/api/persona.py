"""Persona endpoints: query current persona and switch JARVIS / ALYA live."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class PersonaSwitchRequest(BaseModel):
    persona: str


@router.get("/persona")
async def get_persona():
    from backend.services.persona_service import persona_service

    payload = persona_service.current()
    payload["assistant_name"] = persona_service.settings.assistant_name
    payload["tts_voice"] = persona_service.settings.tts_voice
    payload["accent_color"] = persona_service.settings.accent_color
    return payload


@router.post("/persona")
async def switch_persona(request: PersonaSwitchRequest):
    from backend.services.persona_service import persona_service

    if not request.persona.strip():
        raise HTTPException(status_code=400, detail="persona is required.")
    try:
        payload = await persona_service.switch(request.persona)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return payload

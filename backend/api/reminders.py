"""Reminders API for JARVIS Phase 6."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.reminders")

router = APIRouter()


class ReminderCreateRequest(BaseModel):
    title: str
    description: str = ""
    due_at: str = ""
    repeat: str = "once"


class ReminderUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: str | None = None
    repeat: str | None = None
    enabled: bool | None = None


@router.get("/reminders")
async def list_reminders(enabled: bool | None = None):
    from backend.main import memory_service
    return memory_service.get_reminders(enabled=enabled)


@router.post("/reminders")
async def create_reminder(request: ReminderCreateRequest):
    from backend.main import memory_service
    return memory_service.create_reminder(request.title, request.description, request.due_at, request.repeat)


@router.patch("/reminders/{reminder_id}")
async def update_reminder(reminder_id: str, request: ReminderUpdateRequest):
    from backend.main import memory_service
    updates = {k: v for k, v in request.dict(exclude_none=True).items()}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    ok = memory_service.update_reminder(reminder_id, updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "updated"}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    from backend.main import memory_service
    ok = memory_service.delete_reminder(reminder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "deleted"}

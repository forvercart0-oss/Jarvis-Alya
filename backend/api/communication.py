"""Communication Phase 26 API routes for JARVIS."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.notification_service import notification_service
from backend.services.ws_manager import ws_manager
from communications.action_planner import communication_action_planner
from communications.contacts import contact_manager
from communications.inbox import UnifiedInbox
from communications.intent_router import intent_router
from communications.manager import communication_manager
from communications.notifications import communication_notifications
from communications.queue import message_queue
from communications.scheduler import scheduled_message_manager

logger = logging.getLogger("jarvis.api.communication")

router = APIRouter(prefix="/communication", tags=["communication"])


class CommunicationGoalRequest(BaseModel):
    goal: str
    context: dict[str, Any] | None = None


class SendMessageRequest(BaseModel):
    provider: str
    conversation_id: str
    text: str
    attachments: list[dict[str, Any]] | None = None


class ScheduleMessageRequest(BaseModel):
    provider: str
    recipient: str
    message: str
    schedule_time: str


class ContactRequest(BaseModel):
    name: str
    aliases: list[str] = []
    providers: dict[str, str] = {}
    tags: list[str] = []
    notes: str = ""


class NotificationSettingsRequest(BaseModel):
    enabled: bool | None = None
    preview: bool | None = None
    read_aloud: bool | None = None
    important_only: bool | None = None
    call_notifications: bool | None = None
    email_notifications: bool | None = None


@router.get("/status")
async def communication_status() -> dict[str, Any]:
    return {
        "enabled": communication_manager.enabled,
        "providers": communication_manager.list_providers(),
        "notifications": {
            "enabled": communication_notifications.enabled,
            "preview": communication_notifications.preview_enabled,
            "read_aloud": communication_notifications.read_aloud,
            "important_only": communication_notifications.important_only,
        },
    }


@router.post("/enable")
async def communication_enable() -> dict[str, Any]:
    communication_manager.enabled = True
    return {"success": True, "enabled": True}


@router.post("/disable")
async def communication_disable() -> dict[str, Any]:
    communication_manager.enabled = False
    return {"success": True, "enabled": False}


@router.post("/intent")
async def communication_intent(request: CommunicationGoalRequest) -> dict[str, Any]:
    intent = intent_router.route(request.goal)
    return {"success": True, "intent": intent.to_dict()}


@router.post("/task")
async def communication_task(request: CommunicationGoalRequest) -> dict[str, Any]:
    await ws_manager.broadcast("communication_task_started", {"goal": request.goal})
    if not communication_action_planner:
        return {"success": False, "error": "Communication planner not initialized"}
    intent = intent_router.route(request.goal)
    actions = communication_action_planner.plan(intent, request.context)
    await ws_manager.broadcast("communication_task_completed", {"goal": request.goal, "actions": len(actions)})
    return {"success": True, "intent": intent.to_dict(), "actions": [a.to_dict() for a in actions]}


@router.get("/inbox")
async def communication_inbox(limit: int = 50) -> dict[str, Any]:
    inbox = UnifiedInbox(communication_manager)
    return await inbox.get_inbox(limit=limit)


@router.get("/inbox/unread")
async def communication_unread(limit: int = 20) -> dict[str, Any]:
    inbox = UnifiedInbox(communication_manager)
    return await inbox.get_unread(limit=limit)


@router.get("/inbox/important")
async def communication_important(limit: int = 20) -> dict[str, Any]:
    inbox = UnifiedInbox(communication_manager)
    return await inbox.get_important(limit=limit)


@router.post("/send")
async def communication_send(request: SendMessageRequest) -> dict[str, Any]:
    return await communication_manager.send_message(
        request.provider, request.conversation_id, request.text, request.attachments
    )


@router.get("/messages")
async def communication_messages(provider: str, conversation_id: str, limit: int = 50) -> dict[str, Any]:
    return await communication_manager.get_messages(provider, conversation_id, limit)


@router.get("/search")
async def communication_search(query: str, limit: int = 20) -> dict[str, Any]:
    return await communication_manager.search_messages(query, limit)


@router.post("/contacts")
async def communication_create_contact(request: ContactRequest) -> dict[str, Any]:
    from communications.models import Contact
    contact = Contact(
        name=request.name,
        aliases=request.aliases,
        providers=request.providers,
        tags=request.tags,
        notes=request.notes,
    )
    contact_manager.add_contact(contact)
    return {"success": True, "contact": contact.to_dict()}


@router.get("/contacts")
async def communication_list_contacts() -> dict[str, Any]:
    return {"success": True, "contacts": contact_manager.list_all()}


@router.get("/contacts/groups")
async def communication_contact_groups() -> dict[str, Any]:
    return {"success": True, "groups": {k: [c.to_dict() for c in v] for k, v in contact_manager.get_groups().items()}}


@router.post("/contacts/resolve")
async def communication_resolve_contact(name: str) -> dict[str, Any]:
    matches = contact_manager.resolve(name)
    return {"success": True, "matches": [m.to_dict() for m in matches], "count": len(matches)}


@router.post("/schedule")
async def communication_schedule(request: ScheduleMessageRequest) -> dict[str, Any]:
    from communications.models import ScheduledMessage
    message = ScheduledMessage(
        provider=request.provider,
        recipient=request.recipient,
        message=request.message,
        schedule_time=request.schedule_time,
    )
    scheduled_message_manager.schedule(message)
    return {"success": True, "schedule": message.to_dict()}


@router.get("/scheduled")
async def communication_list_scheduled() -> dict[str, Any]:
    return {"success": True, "scheduled": scheduled_message_manager.list_pending()}


@router.post("/scheduled/cancel")
async def communication_cancel_scheduled(schedule_id: str) -> dict[str, Any]:
    result = scheduled_message_manager.cancel(schedule_id)
    return {"success": result}


@router.get("/notifications")
async def communication_notifications_list(limit: int = 20) -> dict[str, Any]:
    return {"success": True, "notifications": notification_service.recent(limit)}


@router.post("/notifications/settings")
async def communication_notification_settings(request: NotificationSettingsRequest) -> dict[str, Any]:
    if request.enabled is not None:
        communication_notifications.enabled = request.enabled
    if request.preview is not None:
        communication_notifications.preview_enabled = request.preview
    if request.read_aloud is not None:
        communication_notifications.read_aloud = request.read_aloud
    if request.important_only is not None:
        communication_notifications.important_only = request.important_only
    if request.call_notifications is not None:
        communication_notifications._call_notifications = request.call_notifications
    if request.email_notifications is not None:
        communication_notifications._email_notifications = request.email_notifications
    return {"success": True}


@router.post("/queue")
async def communication_queue_message(provider: str, conversation_id: str, text: str) -> dict[str, Any]:
    from communications.models import QueuedMessage
    msg = QueuedMessage(provider=provider, conversation_id=conversation_id, text=text)
    message_queue.enqueue(msg)
    return {"success": True, "queue_id": msg.queue_id}


@router.get("/queue")
async def communication_list_queue() -> dict[str, Any]:
    return {"success": True, "queue": message_queue.list_pending()}

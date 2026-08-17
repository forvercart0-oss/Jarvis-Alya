"""Communications package for JARVIS Phase 26."""

from __future__ import annotations

from typing import Any

from communications.action_planner import CommunicationActionPlanner, communication_action_planner
from communications.browser_provider import BrowserCommunicationProvider
from communications.contacts import contact_manager
from communications.email_intelligence import email_intelligence
from communications.email_provider import EmailProvider
from communications.inbox import UnifiedInbox
from communications.intent_router import IntentRouter, intent_router
from communications.manager import communication_manager
from communications.messaging_provider import MessagingProvider
from communications.models import (
    Attachment,
    CallRecord,
    Conversation,
    MessageImportance,
    MessageStatus,
    ProviderType,
    ScheduledMessage,
    UnifiedMessage,
)
from communications.notifications import communication_notifications
from communications.providers import CommunicationProvider
from communications.queue import message_queue
from communications.scheduler import scheduled_message_manager
from communications.search import communication_search_engine

__all__ = [
    "Attachment",
    "BrowserCommunicationProvider",
    "CallRecord",
    "CommunicationActionPlanner",
    "CommunicationIntelligence",
    "CommunicationNotificationManager",
    "CommunicationProvider",
    "Conversation",
    "EmailProvider",
    "IntentRouter",
    "MessageImportance",
    "MessageStatus",
    "MessagingProvider",
    "ProviderType",
    "ScheduledMessage",
    "UnifiedInbox",
    "UnifiedMessage",
    "attachment",
    "call_manager",
    "call_record",
    "communication_action_planner",
    "communication_intelligence",
    "communication_manager",
    "communication_notifications",
    "communication_search_engine",
    "contact_manager",
    "email_intelligence",
    "intent_router",
    "message_normalizer",
    "message_queue",
    "scheduled_message_manager",
]


class CommunicationIntelligence:
    def __init__(self):
        self._intent_router = intent_router
        self._action_planner = None
        self._communication_manager = communication_manager

    def initialize(self, communication_manager: Any) -> None:
        self._communication_manager = communication_manager
        self._action_planner = CommunicationActionPlanner(communication_manager, contact_manager)
        global communication_action_planner
        communication_action_planner = self._action_planner
        global communication_search_engine
        from communications.search import CommunicationSearchEngine
        communication_search_engine = CommunicationSearchEngine(communication_manager)

    async def process_message(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        intent = intent_router.route(text)
        if intent.intent == "unknown":
            return {"success": False, "error": "Unknown communication intent", "intent": intent.to_dict()}
        if not self._action_planner:
            return {"success": False, "error": "Communication intelligence not initialized"}
        actions = self._action_planner.plan(intent, context)
        return {"success": True, "intent": intent.to_dict(), "actions": [a.to_dict() for a in actions]}


communication_intelligence = CommunicationIntelligence()

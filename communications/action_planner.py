"""Action planner for JARVIS Phase 26 communication."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.communications.action_planner")


@dataclass
class CommunicationAction:
    action_type: str
    provider: str | None = None
    conversation_id: str | None = None
    recipient: str | None = None
    text: str | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "provider": self.provider,
            "conversation_id": self.conversation_id,
            "recipient": self.recipient,
            "text": self.text,
            "attachments": self.attachments,
            "metadata": self.metadata,
        }


class CommunicationActionPlanner:
    def __init__(self, communication_manager: Any, contact_manager: Any):
        self._manager = communication_manager
        self._contacts = contact_manager

    def plan(self, intent: Any, context: dict[str, Any] | None = None) -> list[CommunicationAction]:
        actions: list[CommunicationAction] = []
        if intent.intent == "read_messages":
            actions.append(CommunicationAction(action_type="read_messages", provider=intent.provider))
        elif intent.intent == "read_email":
            actions.append(CommunicationAction(action_type="read_email", provider=intent.provider or "email"))
        elif intent.intent == "send_message":
            provider = intent.provider or context.get("provider") if context else intent.provider
            actions.append(CommunicationAction(action_type="send_message", provider=provider, recipient=intent.target, text=context.get("text") if context else None))
        elif intent.intent == "send_email":
            actions.append(CommunicationAction(action_type="send_email", provider="email", recipient=intent.target, text=context.get("text") if context else None))
        elif intent.intent == "make_call":
            actions.append(CommunicationAction(action_type="make_call", provider="phone", recipient=intent.target))
        elif intent.intent == "answer_call":
            actions.append(CommunicationAction(action_type="answer_call"))
        elif intent.intent == "hangup_call":
            actions.append(CommunicationAction(action_type="hangup_call"))
        elif intent.intent == "search_messages":
            actions.append(CommunicationAction(action_type="search_messages", provider=intent.provider, text=intent.target))
        elif intent.intent == "summarize":
            actions.append(CommunicationAction(action_type="summarize", provider=intent.provider, text=intent.target))
        elif intent.intent == "read_unread":
            actions.append(CommunicationAction(action_type="read_unread", provider=intent.provider))
        elif intent.intent == "read_important":
            actions.append(CommunicationAction(action_type="read_important", provider=intent.provider))
        elif intent.intent == "set_notification":
            actions.append(CommunicationAction(action_type="set_notification", text=intent.target))
        return actions

    def resolve_recipient(self, target: str) -> list[Any]:
        if not target:
            return []
        return self._contacts.resolve(target)


communication_action_planner: CommunicationActionPlanner | None = None

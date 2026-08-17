"""Messaging provider for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

from communications.models import ProviderType
from communications.providers import CommunicationProvider

logger = logging.getLogger("jarvis.communications.messaging")


class MessagingProvider(CommunicationProvider):
    name = "messaging"
    provider_type = ProviderType.MESSAGING

    def __init__(self, settings: Any | None = None):
        self._settings = settings
        self._connected = False

    async def connect(self) -> dict[str, Any]:
        self._connected = True
        return {"success": True, "status": "connected"}

    async def disconnect(self) -> dict[str, Any]:
        self._connected = False
        return {"success": True, "status": "disconnected"}

    async def health_check(self) -> dict[str, Any]:
        return {"status": "online" if self._connected else "offline", "provider": self.name}

    async def get_profile(self) -> dict[str, Any]:
        return {"name": "User", "id": "user-1"}

    async def get_conversations(self) -> list[dict[str, Any]]:
        return []

    async def get_messages(self, conversation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return []

    async def send_message(self, conversation_id: str, text: str, attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {"success": True, "message_id": "mock-msg-1"}

    async def mark_read(self, conversation_id: str, message_id: str) -> dict[str, Any]:
        return {"success": True}

    async def search_messages(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return []

    async def get_notifications(self) -> list[dict[str, Any]]:
        return []

    async def start_call(self, contact_identifier: str) -> dict[str, Any]:
        return {"success": False, "error": "Messaging provider does not support calls"}

    async def answer_call(self, call_id: str) -> dict[str, Any]:
        return {"success": False, "error": "Messaging provider does not support calls"}

    async def hangup_call(self, call_id: str) -> dict[str, Any]:
        return {"success": False, "error": "Messaging provider does not support calls"}

"""Provider abstraction for JARVIS Phase 26."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from communications.models import ProviderType


class CommunicationProvider(ABC):
    name: str = "base"
    provider_type: ProviderType = ProviderType.MESSAGING

    @abstractmethod
    async def connect(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def disconnect(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_profile(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_conversations(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_messages(self, conversation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def send_message(self, conversation_id: str, text: str, attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        pass

    @abstractmethod
    async def mark_read(self, conversation_id: str, message_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def search_messages(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_notifications(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def start_call(self, contact_identifier: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def answer_call(self, call_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def hangup_call(self, call_id: str) -> dict[str, Any]:
        pass

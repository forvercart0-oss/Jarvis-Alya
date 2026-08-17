"""Communication search engine for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.communications.search")


class CommunicationSearchEngine:
    def __init__(self, communication_manager: Any):
        self._manager = communication_manager

    async def search(self, query: str, limit: int = 20) -> dict[str, Any]:
        return await self._manager.search_messages(query, limit)

    async def search_by_sender(self, sender: str, limit: int = 20) -> dict[str, Any]:
        return await self._manager.search_messages(sender, limit)

    async def search_by_conversation(self, topic: str, limit: int = 20) -> dict[str, Any]:
        return await self._manager.search_messages(topic, limit)


communication_search_engine: CommunicationSearchEngine | None = None

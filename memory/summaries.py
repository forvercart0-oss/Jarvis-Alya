"""Conversation summaries."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.summaries")


class ConversationSummaries:
    """Manage conversation summaries."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def create(self, conversation_id: str, summary: str, message_count: int = 0) -> dict:
        return self._memory.store.add_conversation_summary(conversation_id, summary, message_count)

    def get(self, conversation_id: str | None = None, limit: int = 50) -> list[dict]:
        return self._memory.store.get_conversation_summaries(conversation_id, limit)

    def update(self, summary_id: str, summary: str) -> bool:
        return self._memory.store.update_conversation_summary(summary_id, summary)

    def delete(self, summary_id: str) -> bool:
        return self._memory.store.delete_conversation_summary(summary_id)

    def clear(self, conversation_id: str) -> int:
        summaries = self.get(conversation_id, limit=1000)
        count = 0
        for s in summaries:
            if self._memory.store.delete_conversation_summary(s["id"]):
                count += 1
        return count

"""Message normalizer for JARVIS Phase 26.

Normalizes incoming messages from different providers into a unified format.
"""

from __future__ import annotations

import logging
from typing import Any

from communications.models import UnifiedMessage

logger = logging.getLogger("jarvis.communications.normalizer")


class MessageNormalizer:
    def normalize(self, raw: dict[str, Any], provider: str, provider_type: str) -> UnifiedMessage:
        text = raw.get("text") or raw.get("content") or raw.get("body") or raw.get("message") or ""
        return UnifiedMessage(
            provider=provider,
            provider_type=provider_type,
            conversation_id=raw.get("conversation_id") or raw.get("chat_id") or raw.get("thread_id") or "",
            message_id=raw.get("message_id") or raw.get("id") or "",
            sender=raw.get("sender") or raw.get("from") or raw.get("author") or "",
            recipient=raw.get("recipient") or raw.get("to") or raw.get("destinatary") or "",
            text=str(text),
            timestamp=raw.get("timestamp") or raw.get("date") or "",
            attachments=raw.get("attachments") or raw.get("files") or [],
            status=raw.get("status", "pending"),
            unread=bool(raw.get("unread", False)),
            importance=raw.get("importance", "unknown"),
            metadata=raw.get("metadata") or {},
        )

    def normalize_conversation(self, raw: dict[str, Any], provider: str, provider_type: str) -> dict[str, Any]:
        participants = raw.get("participants") or raw.get("members") or []
        if isinstance(participants, list) and participants and not isinstance(participants[0], str):
            participants = [p.get("name") or p.get("id") or str(p) for p in participants]
        return {
            "conversation_id": raw.get("conversation_id") or raw.get("id") or "",
            "provider": provider,
            "provider_type": provider_type,
            "participants": participants,
            "title": raw.get("title") or raw.get("name") or "",
            "last_message": raw.get("last_message") or raw.get("last_text") or "",
            "last_timestamp": raw.get("last_timestamp") or raw.get("updated_at") or "",
            "unread_count": int(raw.get("unread_count") or raw.get("unreadCount") or 0),
            "metadata": raw.get("metadata") or {},
        }


message_normalizer = MessageNormalizer()

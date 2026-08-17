"""Unified communication models for JARVIS Phase 26."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class MessageStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageImportance(StrEnum):
    IMPORTANT = "important"
    NORMAL = "normal"
    PROMOTIONAL = "promotional"
    NOTIFICATION = "notification"
    SPAM = "spam"
    UNKNOWN = "unknown"


class CallStatus(StrEnum):
    IDLE = "idle"
    RINGING = "ringing"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    MUTED = "muted"
    ON_HOLD = "on_hold"
    ENDED = "ended"
    FAILED = "failed"


class ProviderType(StrEnum):
    EMAIL = "email"
    MESSAGING = "messaging"
    SOCIAL = "social"
    TEAM_CHAT = "team_chat"
    SMS = "sms"
    PHONE = "phone"
    VIDEO = "video"
    BROWSER = "browser"


@dataclass
class UnifiedMessage:
    provider: str = ""
    provider_type: str = ""
    conversation_id: str = ""
    message_id: str = ""
    sender: str = ""
    recipient: str = ""
    text: str = ""
    timestamp: str = ""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    status: str = MessageStatus.PENDING
    unread: bool = False
    importance: str = MessageImportance.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "text": self.text,
            "timestamp": self.timestamp,
            "attachments": self.attachments,
            "status": self.status,
            "unread": self.unread,
            "importance": self.importance,
            "metadata": self.metadata,
        }


@dataclass
class Conversation:
    conversation_id: str = ""
    provider: str = ""
    provider_type: str = ""
    participants: list[str] = field(default_factory=list)
    title: str = ""
    last_message: str = ""
    last_timestamp: str = ""
    unread_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        if not self.last_timestamp:
            self.last_timestamp = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "provider": self.provider,
            "provider_type": self.provider_type,
            "participants": self.participants,
            "title": self.title,
            "last_message": self.last_message,
            "last_timestamp": self.last_timestamp,
            "unread_count": self.unread_count,
            "metadata": self.metadata,
        }


@dataclass
class Contact:
    contact_id: str = ""
    name: str = ""
    aliases: list[str] = field(default_factory=list)
    providers: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.contact_id:
            self.contact_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "aliases": self.aliases,
            "providers": self.providers,
            "tags": self.tags,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class ScheduledMessage:
    schedule_id: str = ""
    provider: str = ""
    recipient: str = ""
    message: str = ""
    schedule_time: str = ""
    status: str = MessageStatus.PENDING
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.schedule_id:
            self.schedule_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "provider": self.provider,
            "recipient": self.recipient,
            "message": self.message,
            "schedule_time": self.schedule_time,
            "status": self.status,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class CallRecord:
    call_id: str = ""
    provider: str = ""
    caller: str = ""
    recipient: str = ""
    timestamp: str = ""
    duration: int = 0
    status: str = CallStatus.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.call_id:
            self.call_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "provider": self.provider,
            "caller": self.caller,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class Attachment:
    attachment_id: str = ""
    filename: str = ""
    mime_type: str = ""
    size: int = 0
    url: str = ""
    local_path: str = ""
    status: str = MessageStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.attachment_id:
            self.attachment_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size": self.size,
            "url": self.url,
            "local_path": self.local_path,
            "status": self.status,
            "metadata": self.metadata,
        }

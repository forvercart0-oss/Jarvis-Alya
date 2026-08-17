"""Message queue for JARVIS Phase 26."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.communications.queue")


@dataclass
class QueuedMessage:
    queue_id: str = ""
    provider: str = ""
    conversation_id: str = ""
    recipient: str = ""
    text: str = ""
    status: str = "pending"
    retries: int = 0
    max_retries: int = 3
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.queue_id:
            self.queue_id = str(__import__("uuid").uuid4())
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "provider": self.provider,
            "conversation_id": self.conversation_id,
            "recipient": self.recipient,
            "text": self.text,
            "status": self.status,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


class MessageQueue:
    def __init__(self):
        self._queue: dict[str, QueuedMessage] = {}

    def enqueue(self, message: QueuedMessage) -> None:
        self._queue[message.queue_id] = message
        logger.info("Message queued: %s -> %s", message.queue_id, message.recipient)

    def dequeue(self, queue_id: str) -> QueuedMessage | None:
        return self._queue.pop(queue_id, None)

    def get(self, queue_id: str) -> QueuedMessage | None:
        return self._queue.get(queue_id)

    def list_pending(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._queue.values() if m.status == "pending"]

    def update_status(self, queue_id: str, status: str) -> QueuedMessage | None:
        msg = self._queue.get(queue_id)
        if msg:
            msg.status = status
            msg.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
            if status == "sending":
                msg.retries += 1
        return msg


message_queue = MessageQueue()

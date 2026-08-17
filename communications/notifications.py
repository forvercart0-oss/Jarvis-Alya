"""Notification manager for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

from backend.services.notification_service import notification_service

logger = logging.getLogger("jarvis.communications.notifications")


class CommunicationNotificationManager:
    def __init__(self):
        self._enabled = True
        self._preview_enabled = True
        self._read_aloud = False
        self._important_only = False
        self._call_notifications = True
        self._email_notifications = True
        self._desktop_notifications = True
        self._sound = True

    async def notify_message(self, message: dict[str, Any]) -> None:
        if not self._enabled:
            return
        if self._important_only and message.get("importance") != "important":
            return
        sender = message.get("sender", "Unknown")
        text = message.get("text", "")
        preview = text[:100] if self._preview_enabled else "[Message hidden]"
        await notification_service.push(
            f"New message from {sender}",
            preview,
            ntype="message",
            data={"provider": message.get("provider"), "message_id": message.get("message_id")},
        )

    async def notify_call(self, call: dict[str, Any]) -> None:
        if not self._enabled or not self._call_notifications:
            return
        caller = call.get("caller", "Unknown")
        await notification_service.push(
            f"Incoming call from {caller}",
            "Tap to answer",
            ntype="call",
            data={"call_id": call.get("call_id"), "provider": call.get("provider")},
        )

    async def notify_email(self, email: dict[str, Any]) -> None:
        if not self._enabled or not self._email_notifications:
            return
        sender = email.get("sender", "Unknown")
        subject = email.get("subject", "No subject")
        preview = subject[:100] if self._preview_enabled else "[Email hidden]"
        await notification_service.push(
            f"Email from {sender}",
            preview,
            ntype="email",
            data={"message_id": email.get("message_id"), "importance": email.get("importance")},
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def preview_enabled(self) -> bool:
        return self._preview_enabled

    @preview_enabled.setter
    def preview_enabled(self, value: bool) -> None:
        self._preview_enabled = value

    @property
    def read_aloud(self) -> bool:
        return self._read_aloud

    @read_aloud.setter
    def read_aloud(self, value: bool) -> None:
        self._read_aloud = value

    @property
    def important_only(self) -> bool:
        return self._important_only

    @important_only.setter
    def important_only(self, value: bool) -> None:
        self._important_only = value


communication_notifications = CommunicationNotificationManager()

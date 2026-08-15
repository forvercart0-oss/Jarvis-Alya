"""Call control manager."""

from __future__ import annotations

import logging
from typing import Optional

from communications.calls.provider import CallProvider

logger = logging.getLogger("jarvis.calls.manager")


class CallManager:
    def __init__(self, settings):
        self.settings = settings
        self._provider: CallProvider | None = None
        self._active_call: str | None = None

    def register_provider(self, provider: CallProvider) -> None:
        self._provider = provider

    def is_available(self) -> bool:
        return self._provider is not None and self._provider.health_check().get("status") == "online"

    async def call(self, contact_identifier: str) -> dict:
        if not self._provider:
            return {"success": False, "error": "No call provider configured."}
        try:
            result = await self._provider.call(contact_identifier)
            if result.get("success"):
                self._active_call = result.get("call_id")
            return result
        except Exception as exc:
            logger.warning("Call failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def hangup(self) -> dict:
        if not self._active_call or not self._provider:
            return {"success": False, "error": "No active call."}
        try:
            result = await self._provider.hangup(self._active_call)
            self._active_call = None
            return result
        except Exception as exc:
            logger.warning("Hangup failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def accept(self, call_id: str) -> dict:
        if not self._provider:
            return {"success": False, "error": "No call provider configured."}
        try:
            return await self._provider.accept(call_id)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def decline(self, call_id: str) -> dict:
        if not self._provider:
            return {"success": False, "error": "No call provider configured."}
        try:
            return await self._provider.decline(call_id)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @property
    def active_call(self) -> Optional[str]:
        return self._active_call

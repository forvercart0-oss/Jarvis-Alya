"""Unified inbox for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.communications.inbox")


class UnifiedInbox:
    def __init__(self, communication_manager: Any):
        self._manager = communication_manager

    async def get_inbox(self, limit: int = 50) -> dict[str, Any]:
        return await self._manager.get_unified_inbox()

    async def get_unread(self, limit: int = 20) -> dict[str, Any]:
        result = await self._manager.get_unified_inbox()
        if not result.get("success"):
            return result
        unread = [item for item in result.get("inbox", []) if item.get("unread_count", 0) > 0]
        return {"success": True, "unread": unread[:limit]}

    async def get_important(self, limit: int = 20) -> dict[str, Any]:
        result = await self._manager.get_unified_inbox()
        if not result.get("success"):
            return result
        important = [item for item in result.get("inbox", []) if item.get("importance") == "important"]
        return {"success": True, "important": important[:limit]}

    async def get_by_provider(self, provider: str, limit: int = 50) -> dict[str, Any]:
        result = await self._manager.get_unified_inbox()
        if not result.get("success"):
            return result
        filtered = [item for item in result.get("inbox", []) if item.get("provider") == provider]
        return {"success": True, "items": filtered[:limit]}

"""Communication manager for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

from communications.normalizer import message_normalizer

logger = logging.getLogger("jarvis.communications.manager")


class CommunicationManager:
    def __init__(self):
        self._providers: dict[str, Any] = {}
        self._enabled = False
        self._broadcast = None

    def set_broadcast(self, broadcast: Any) -> None:
        self._broadcast = broadcast

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def register_provider(self, name: str, provider: Any) -> None:
        self._providers[name] = provider
        logger.info("Communication provider registered: %s", name)

    def get_provider(self, name: str) -> Any | None:
        return self._providers.get(name)

    def list_providers(self) -> list[dict[str, Any]]:
        result = []
        for name, provider in self._providers.items():
            try:
                health = provider.health_check()
                result.append({"name": name, "provider_type": getattr(provider, "provider_type", "unknown"), "health": health})
            except Exception as exc:
                result.append({"name": name, "provider_type": getattr(provider, "provider_type", "unknown"), "health": {"status": "error", "error": str(exc)}})
        return result

    async def _broadcast(self, event: str, data: dict[str, Any]) -> None:
        if self._broadcast:
            try:
                await self._broadcast(event, data)
            except Exception:
                pass

    async def get_unified_inbox(self) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Communication disabled"}
        all_messages = []
        for name, provider in self._providers.items():
            try:
                if hasattr(provider, "get_conversations"):
                    conversations = await provider.get_conversations()
                    for conv in conversations[:10]:
                        all_messages.append({**conv, "provider": name})
            except Exception as exc:
                logger.debug("Inbox fetch failed for %s: %s", name, exc)
        all_messages.sort(key=lambda x: x.get("last_timestamp", ""), reverse=True)
        return {"success": True, "inbox": all_messages[:50]}

    async def send_message(self, provider: str, conversation_id: str, text: str, attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Communication disabled"}
        p = self._providers.get(provider)
        if not p:
            return {"success": False, "error": f"Provider not found: {provider}"}
        try:
            result = await p.send_message(conversation_id, text, attachments)
            await self._broadcast("message_sent", {"provider": provider, "conversation_id": conversation_id, "result": result})
            return result
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def get_messages(self, provider: str, conversation_id: str, limit: int = 50) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Communication disabled"}
        p = self._providers.get(provider)
        if not p:
            return {"success": False, "error": f"Provider not found: {provider}"}
        try:
            messages = await p.get_messages(conversation_id, limit)
            normalized = [message_normalizer.normalize(m, provider, getattr(p, "provider_type", "unknown")).to_dict() for m in messages]
            return {"success": True, "messages": normalized}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def search_messages(self, query: str, limit: int = 20) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Communication disabled"}
        results = []
        for name, provider in self._providers.items():
            try:
                if hasattr(provider, "search_messages"):
                    messages = await provider.search_messages(query, limit)
                    for m in messages:
                        results.append(message_normalizer.normalize(m, name, getattr(provider, "provider_type", "unknown")).to_dict())
            except Exception as exc:
                logger.debug("Search failed for %s: %s", name, exc)
        return {"success": True, "results": results[:limit]}


communication_manager = CommunicationManager()

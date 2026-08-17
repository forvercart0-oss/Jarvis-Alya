"""Base specialized agent for JARVIS Phase 20."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.agent.specialized")


class BaseSpecializedAgent:
    def __init__(self, agent_id: str, name: str, tool_execute: Any | None = None, memory: Any | None = None):
        self.agent_id = agent_id
        self.name = name
        self._tool_execute = tool_execute
        self._memory = memory

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        raise NotImplementedError

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._tool_execute:
            return {"success": False, "error": "No tool executor available"}
        try:
            result = await self._tool_execute(tool_name, arguments)
            if hasattr(result, 'to_dict'):
                result = result.to_dict()
            return result
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _get_context(self, context: dict[str, Any]) -> str:
        return context.get("description", "")

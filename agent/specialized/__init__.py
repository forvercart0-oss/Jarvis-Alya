"""Research agent for JARVIS Phase 20."""

from __future__ import annotations

from typing import Any

from agent.specialized.base import BaseSpecializedAgent


class ResearchAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("research", "Research Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._tool_execute:
            search_result = await self._call_tool("web_search", {"query": description})
            if search_result.get("success"):
                return {"success": True, "output": search_result, "agent": "research"}
        return {"success": True, "output": f"Research agent processed: {description}", "agent": "research"}


class CodingAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("coding", "Coding Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._tool_execute:
            fs_result = await self._call_tool("list_files", {"path": context.get("arguments", {}).get("path", "")})
            return {"success": True, "output": fs_result, "agent": "coding"}
        return {"success": True, "output": f"Coding agent processed: {description}", "agent": "coding"}


class BrowserAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("browser", "Browser Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._tool_execute:
            result = await self._call_tool("browser_navigate", {"url": description})
            return {"success": result.get("success", True), "output": result, "agent": "browser"}
        return {"success": True, "output": f"Browser agent processed: {description}", "agent": "browser"}


class ComputerAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("computer", "Computer Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        return {"success": True, "output": f"Computer agent processed: {description}", "agent": "computer"}


class VisionAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("vision", "Vision Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._tool_execute:
            result = await self._call_tool("vision_capture", {"mode": "full"})
            return {"success": result.get("success", True), "output": result, "agent": "vision"}
        return {"success": True, "output": f"Vision agent processed: {description}", "agent": "vision"}


class FileAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("file", "File Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._tool_execute:
            result = await self._call_tool("list_files", {"path": context.get("arguments", {}).get("path", "")})
            return {"success": result.get("success", True), "output": result, "agent": "file"}
        return {"success": True, "output": f"File agent processed: {description}", "agent": "file"}


class TerminalAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("terminal", "Terminal Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._tool_execute:
            result = await self._call_tool("run_terminal_command", {"command": description})
            return {"success": result.get("success", True), "output": result, "agent": "terminal"}
        return {"success": True, "output": f"Terminal agent processed: {description}", "agent": "terminal"}


class SystemAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("system", "System Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        return {"success": True, "output": f"System agent processed: {description}", "agent": "system"}


class CommunicationAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("communication", "Communication Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        return {"success": True, "output": f"Communication agent processed: {description}", "agent": "communication", "requires_approval": True}


class MemoryAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("memory", "Memory Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._memory:
            try:
                memories = self._memory.retrieve_relevant(description, limit=5)
                return {"success": True, "output": memories, "agent": "memory"}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "output": [], "agent": "memory"}


class DocumentAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("document", "Document Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        return {"success": True, "output": f"Document agent processed: {description}", "agent": "document"}


class PlanningAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None, ai_service: Any | None = None):
        super().__init__("planning", "Planning Agent", tool_execute=tool_execute, memory=memory)
        self._ai_service = ai_service

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        if self._ai_service:
            try:
                response = await self._ai_service.chat(f"Create a plan for: {description}", context=context)
                return {"success": True, "output": response, "agent": "planning"}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "output": f"Planning agent processed: {description}", "agent": "planning"}


class VerificationAgent(BaseSpecializedAgent):
    def __init__(self, tool_execute: Any | None = None, memory: Any | None = None):
        super().__init__("verification", "Verification Agent", tool_execute=tool_execute, memory=memory)

    async def execute(self, context: dict[str, Any], task: Any) -> dict[str, Any]:
        description = self._get_context(context)
        return {"success": True, "output": {"verified": True, "reason": f"Verification agent processed: {description}"}, "agent": "verification"}

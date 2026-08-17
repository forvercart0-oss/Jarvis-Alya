"""Agent registry for JARVIS Phase 20."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger("jarvis.agent.registry")


@dataclass
class AgentDefinition:
    agent_id: str
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    status: str = "idle"
    priority: str = "normal"
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, AgentDefinition] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        builtins = [
            AgentDefinition("general", "General Agent", "Handles conversation, questions, and simple commands", capabilities=["conversation", "reasoning", "simple_tasks"], tools=["chat", "memory"], permissions=["READ_PAGE", "NAVIGATE"], priority="normal"),
            AgentDefinition("research", "Research Agent", "Deep research, web search, source collection, summarization", capabilities=["research", "web_search", "summarization", "fact_check"], tools=["web_search", "browser", "document"], permissions=["NETWORK", "WEB_SEARCH"], priority="high"),
            AgentDefinition("coding", "Coding Agent", "Code reading, editing, debugging, testing", capabilities=["coding", "debugging", "testing", "file_editing"], tools=["filesystem", "terminal", "code_tools"], permissions=["FILE_WRITE", "TERMINAL_EXECUTE"], priority="high"),
            AgentDefinition("browser", "Browser Agent", "Web automation, page inspection, interaction", capabilities=["browser_automation", "web_interaction", "data_extraction"], tools=["browser", "vision", "ocr"], permissions=["BROWSER_CONTROL"], priority="normal"),
            AgentDefinition("computer", "Computer Agent", "Desktop control, mouse, keyboard, windows", capabilities=["computer_control", "mouse_keyboard", "window_management"], tools=["computer", "vision"], permissions=["MOUSE_CONTROL", "KEYBOARD_CONTROL", "WINDOW_CONTROL"], priority="high"),
            AgentDefinition("vision", "Vision Agent", "Screen analysis, OCR, image understanding", capabilities=["vision", "ocr", "ui_detection", "visual_grounding"], tools=["vision", "screenshot"], permissions=["SCREEN_READ"], priority="normal"),
            AgentDefinition("file", "File Agent", "File search, read, create, edit, organize", capabilities=["file_search", "file_read", "file_write", "file_organize"], tools=["filesystem"], permissions=["FILE_READ", "FILE_WRITE"], priority="normal"),
            AgentDefinition("terminal", "Terminal Agent", "Command execution, output analysis, diagnostics", capabilities=["terminal", "command_execution", "process_monitoring"], tools=["terminal", "process"], permissions=["TERMINAL_EXECUTE"], priority="high"),
            AgentDefinition("system", "System Agent", "System info, diagnostics, health checks", capabilities=["system_info", "diagnostics", "health"], tools=["system"], permissions=["SYSTEM_READ"], priority="normal"),
            AgentDefinition("communication", "Communication Agent", "Notifications, messages, approved communication", capabilities=["notifications", "messaging", "email"], tools=["notifications"], permissions=["SEND_MESSAGE"], priority="normal"),
            AgentDefinition("memory", "Memory Agent", "Memory retrieval, storage, summarization", capabilities=["memory_retrieval", "memory_storage", "summarization"], tools=["memory"], permissions=["MEMORY_READ", "MEMORY_WRITE"], priority="normal"),
            AgentDefinition("document", "Document Agent", "Document creation, reading, summarization, conversion", capabilities=["document_create", "document_read", "summarization", "report_generation"], tools=["document", "filesystem"], permissions=["FILE_WRITE"], priority="normal"),
            AgentDefinition("planning", "Planning Agent", "Task decomposition, planning, scheduling", capabilities=["planning", "decomposition", "scheduling"], tools=["planner"], permissions=["PLAN"], priority="high"),
            AgentDefinition("verification", "Verification Agent", "Task verification, validation, quality checks", capabilities=["verification", "validation", "quality_check"], tools=["verifier"], permissions=["VERIFY"], priority="high"),
        ]
        for agent in builtins:
            self._agents[agent.agent_id] = agent

    def register(self, definition: AgentDefinition) -> None:
        self._agents[definition.agent_id] = definition
        logger.info("Registered agent: %s", definition.agent_id)

    def get(self, agent_id: str) -> AgentDefinition | None:
        return self._agents.get(agent_id)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def list_agents(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._agents.values()]

    def find_by_capability(self, capability: str) -> list[AgentDefinition]:
        return [a for a in self._agents.values() if capability in a.capabilities]

    def find_by_tool(self, tool: str) -> list[AgentDefinition]:
        return [a for a in self._agents.values() if tool in a.tools]


agent_registry = AgentRegistry()

"""Agent Registry 2.0 for JARVIS Phase 23.

Dynamic agent registry with capability advertising, automatic
agent selection based on task requirements, and model routing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("jarvis.agent.registry_v2")


@dataclass
class AgentCapability:
    capability_id: str
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    cost_level: str = "medium"
    avg_latency_ms: int = 1000
    availability: float = 1.0
    specialization: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRegistration:
    agent_id: str
    name: str
    description: str
    capabilities: list[AgentCapability] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    cost_level: str = "medium"
    avg_latency_ms: int = 1000
    availability: float = 1.0
    specialization: str = "general"
    status: str = "idle"
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.__dict__ for c in self.capabilities],
            "tools": self.tools,
            "models": self.models,
            "cost_level": self.cost_level,
            "avg_latency_ms": self.avg_latency_ms,
            "availability": self.availability,
            "specialization": self.specialization,
            "status": self.status,
            "version": self.version,
            "metadata": self.metadata,
            "registered_at": self.registered_at,
        }


class AgentRegistryV2:
    """Dynamic agent registry for Phase 23."""

    def __init__(self):
        self._agents: dict[str, AgentRegistration] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        builtins = [
            AgentRegistration(
                agent_id="general", name="General Agent",
                description="Handles conversation, questions, and simple commands",
                capabilities=[AgentCapability(capability_id="general_chat", name="General Chat", description="General conversation", tools=["chat", "memory"], specialization="general")],
                tools=["chat", "memory"], models=["local", "groq"], cost_level="low", avg_latency_ms=500, specialization="general",
            ),
            AgentRegistration(
                agent_id="research", name="Research Agent",
                description="Deep research, web search, source collection, summarization",
                capabilities=[AgentCapability(capability_id="research", name="Research", description="Deep research", tools=["web_search", "browser", "document"], models=["groq", "gemini"], specialization="research")],
                tools=["web_search", "browser", "document"], models=["groq", "gemini"], cost_level="medium", avg_latency_ms=3000, specialization="research",
            ),
            AgentRegistration(
                agent_id="coding", name="Coding Agent",
                description="Code reading, editing, debugging, testing",
                capabilities=[AgentCapability(capability_id="coding", name="Coding", description="Code operations", tools=["filesystem", "terminal", "code_tools"], models=["groq", "local"], specialization="coding")],
                tools=["filesystem", "terminal", "code_tools"], models=["groq", "local"], cost_level="medium", avg_latency_ms=2000, specialization="coding",
            ),
            AgentRegistration(
                agent_id="browser", name="Browser Agent",
                description="Web automation, page inspection, interaction",
                capabilities=[AgentCapability(capability_id="browser", name="Browser Automation", description="Browser control", tools=["browser", "vision", "ocr"], models=["local"], specialization="browser")],
                tools=["browser", "vision", "ocr"], models=["local"], cost_level="low", avg_latency_ms=1500, specialization="browser",
            ),
            AgentRegistration(
                agent_id="computer", name="Computer Agent",
                description="Desktop control, mouse, keyboard, windows",
                capabilities=[AgentCapability(capability_id="computer", name="Computer Control", description="Desktop automation", tools=["computer", "vision"], models=["local"], specialization="computer")],
                tools=["computer", "vision"], models=["local"], cost_level="low", avg_latency_ms=2000, specialization="computer",
            ),
            AgentRegistration(
                agent_id="vision", name="Vision Agent",
                description="Screen analysis, OCR, image understanding",
                capabilities=[AgentCapability(capability_id="vision", name="Vision", description="Visual analysis", tools=["vision", "screenshot"], models=["local", "gemini"], specialization="vision")],
                tools=["vision", "screenshot"], models=["local", "gemini"], cost_level="medium", avg_latency_ms=2500, specialization="vision",
            ),
            AgentRegistration(
                agent_id="file", name="File Agent",
                description="File search, read, create, edit, organize",
                capabilities=[AgentCapability(capability_id="files", name="File Operations", description="File management", tools=["filesystem"], models=["local"], specialization="files")],
                tools=["filesystem"], models=["local"], cost_level="low", avg_latency_ms=800, specialization="files",
            ),
            AgentRegistration(
                agent_id="terminal", name="Terminal Agent",
                description="Command execution, output analysis, diagnostics",
                capabilities=[AgentCapability(capability_id="terminal", name="Terminal", description="Command execution", tools=["terminal", "process"], models=["local"], specialization="terminal")],
                tools=["terminal", "process"], models=["local"], cost_level="low", avg_latency_ms=1000, specialization="terminal",
            ),
            AgentRegistration(
                agent_id="system", name="System Agent",
                description="System info, diagnostics, health checks",
                capabilities=[AgentCapability(capability_id="system", name="System", description="System operations", tools=["system"], models=["local"], specialization="system")],
                tools=["system"], models=["local"], cost_level="low", avg_latency_ms=500, specialization="system",
            ),
            AgentRegistration(
                agent_id="communication", name="Communication Agent",
                description="Notifications, messages, approved communication",
                capabilities=[AgentCapability(capability_id="communication", name="Communication", description="Messaging", tools=["notifications"], models=["local"], specialization="communication")],
                tools=["notifications"], models=["local"], cost_level="low", avg_latency_ms=500, specialization="communication",
            ),
            AgentRegistration(
                agent_id="document", name="Document Agent",
                description="Document creation, reading, summarization, conversion",
                capabilities=[AgentCapability(capability_id="document", name="Document", description="Document operations", tools=["document", "filesystem"], models=["local", "groq"], specialization="document")],
                tools=["document", "filesystem"], models=["local", "groq"], cost_level="medium", avg_latency_ms=1500, specialization="document",
            ),
            AgentRegistration(
                agent_id="planning", name="Planning Agent",
                description="Task decomposition, planning, scheduling",
                capabilities=[AgentCapability(capability_id="planning", name="Planning", description="Goal decomposition", tools=["planner"], models=["groq", "local"], specialization="planning")],
                tools=["planner"], models=["groq", "local"], cost_level="medium", avg_latency_ms=2000, specialization="planning",
            ),
            AgentRegistration(
                agent_id="verification", name="Verification Agent",
                description="Task verification, validation, quality checks",
                capabilities=[AgentCapability(capability_id="verification", name="Verification", description="Result verification", tools=["verifier"], models=["local"], specialization="verification")],
                tools=["verifier"], models=["local"], cost_level="low", avg_latency_ms=800, specialization="verification",
            ),
        ]
        for agent in builtins:
            self._agents[agent.agent_id] = agent

    def register(self, registration: AgentRegistration) -> None:
        self._agents[registration.agent_id] = registration
        logger.info("Registered agent: %s", registration.agent_id)

    def get(self, agent_id: str) -> AgentRegistration | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._agents.values()]

    def find_by_capability(self, capability: str) -> list[AgentRegistration]:
        return [a for a in self._agents.values() for c in a.capabilities if capability in c.name.lower() or capability in c.description.lower()]

    def find_by_tool(self, tool: str) -> list[AgentRegistration]:
        return [a for a in self._agents.values() if tool in a.tools]

    def find_by_specialization(self, specialization: str) -> list[AgentRegistration]:
        return [a for a in self._agents.values() if a.specialization == specialization]

    def select_best(self, task_description: str, required_tools: list[str] | None = None, preferred_model: str | None = None) -> AgentRegistration | None:
        candidates = list(self._agents.values())
        if required_tools:
            scored = []
            for agent in candidates:
                tool_matches = sum(1 for t in required_tools if t in agent.tools)
                if tool_matches > 0:
                    scored.append((agent, tool_matches / len(required_tools), agent.availability, -agent.avg_latency_ms))
            if scored:
                scored.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
                return scored[0][0]

        scored = [(a, a.availability, -a.avg_latency_ms) for a in candidates]
        scored.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return scored[0][0] if scored else None


agent_registry_v2 = AgentRegistryV2()

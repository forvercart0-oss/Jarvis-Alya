"""Multi-agent coding system for JARVIS Phase 27."""

from __future__ import annotations

import logging
from typing import Any

from coding.models import AgentType, CodingTask

logger = logging.getLogger("jarvis.coding.multi_agent")


class CodingAgent:
    def __init__(self, agent_type: str, name: str):
        self.agent_type = agent_type
        self.name = name

    async def execute(self, task: CodingTask, context: dict[str, Any]) -> dict[str, Any]:
        logger.info("Agent %s executing task %s", self.name, task.task_id)
        return {"success": True, "agent": self.name, "type": self.agent_type, "result": {}}


class MultiAgentSystem:
    def __init__(self):
        self._agents: dict[str, CodingAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        for agent_type in AgentType:
            self._agents[agent_type.value] = CodingAgent(agent_type.value, f"{agent_type.value.capitalize()}Agent")

    def get_agent(self, agent_type: str) -> CodingAgent | None:
        return self._agents.get(agent_type)

    async def route(self, task: CodingTask, context: dict[str, Any]) -> dict[str, Any]:
        goal_lower = task.goal.lower()
        if any(k in goal_lower for k in ["review", "security", "audit"]):
            agent = self.get_agent(AgentType.SECURITY.value)
        elif any(k in goal_lower for k in ["test", "tests", "testing"]):
            agent = self.get_agent(AgentType.TESTING.value)
        elif any(k in goal_lower for k in ["debug", "fix", "error", "bug"]):
            agent = self.get_agent(AgentType.DEBUGGER.value)
        elif any(k in goal_lower for k in ["document", "readme", "docs"]):
            agent = self.get_agent(AgentType.DOCUMENTATION.value)
        elif any(k in goal_lower for k in ["architecture", "design", "plan"]):
            agent = self.get_agent(AgentType.ARCHITECT.value)
        else:
            agent = self.get_agent(AgentType.CODER.value)
        if not agent:
            return {"success": False, "error": "No suitable agent found"}
        return await agent.execute(task, context)


multi_agent_system = MultiAgentSystem()

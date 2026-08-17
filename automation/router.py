"""Agent, skill, and tool router for JARVIS Phase 13."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.automation.router")


class AgentRouter:
    AGENT_KEYWORDS = {
        "browser": ["open browser", "navigate", "github", "website", "web", "browse"],
        "computer": ["open firefox", "open chrome", "click", "type", "desktop", "application", "terminal"],
        "coding": ["code", "python", "javascript", "react", "api", "backend", "frontend", "project", "build"],
        "research": ["research", "deep search", "investigate", "analyze topic", "find sources"],
        "workflow": ["workflow", "automate", "schedule", "remind"],
        "memory": ["remember", "recall", "what do you remember", "memory"],
        "vision": ["see", "screen", "capture", "vision", "image"],
    }

    def route(self, description: str) -> str:
        lower = description.lower()
        scores = {}
        for agent, keywords in self.AGENT_KEYWORDS.items():
            score = sum(1 for k in keywords if k in lower)
            if score:
                scores[agent] = score
        if not scores:
            return "agent"
        return max(scores, key=scores.get)


class SkillRouter:
    def __init__(self, skill_registry: Any | None = None):
        self._registry = skill_registry

    def route(self, description: str) -> list[str]:
        if not self._registry:
            return []
        try:
            skills = self._registry.list_skills()
            lower = description.lower()
            matched = []
            for skill in skills:
                triggers = getattr(skill, "triggers", []) or []
                if any(t.lower() in lower for t in triggers):
                    matched.append(getattr(skill, "id", ""))
            return matched
        except Exception as exc:
            logger.debug("Skill routing failed: %s", exc)
            return []


class ToolRouter:
    def __init__(self, tool_registry: Any | None = None):
        self._registry = tool_registry
        self._risk_map = {
            "read_file": "low",
            "system_info": "low",
            "web_search": "low",
            "open_browser": "low",
            "write_file": "medium",
            "terminal": "medium",
            "run_project_command": "medium",
            "computer_control": "medium",
            "browser_navigate": "medium",
            "delete_file": "high",
            "shutdown": "critical",
            "reboot": "critical",
            "send_message": "high",
            "execute_automation": "low",
        }

    def get_risk(self, tool_name: str) -> str:
        return self._risk_map.get(tool_name, "medium")

    def requires_approval(self, tool_name: str) -> bool:
        risk = self.get_risk(tool_name)
        return risk in ("high", "critical")

    def is_allowed(self, tool_name: str) -> bool:
        if not self._registry:
            return True
        try:
            return tool_name in self._registry.names()
        except Exception:
            return True

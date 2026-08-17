"""Agent context manager for JARVIS Phase 20."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.agent.context_manager")


class AgentContextManager:
    def __init__(self, memory: Any | None = None):
        self._memory = memory

    def build_context(self, task: dict[str, Any], agent_id: str) -> dict[str, Any]:
        context = {
            "task_id": task.get("task_id", ""),
            "agent_id": agent_id,
            "description": task.get("description", task.get("title", "")),
            "arguments": task.get("arguments", {}),
            "input": task.get("input", {}),
            "dependencies": task.get("dependencies", []),
            "priority": task.get("priority", "normal"),
            "permissions": task.get("permissions", []),
        }
        if self._memory:
            try:
                relevant = self._memory.retrieve_relevant(context["description"], limit=5)
                context["relevant_memory"] = relevant
            except Exception:
                context["relevant_memory"] = []
        return context

    def minimize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        minimized = {
            "task_id": context.get("task_id"),
            "agent_id": context.get("agent_id"),
            "description": context.get("description"),
            "arguments": context.get("arguments", {}),
        }
        if context.get("dependencies"):
            minimized["dependencies"] = context["dependencies"]
        return minimized

    def redact_secrets(self, context: dict[str, Any]) -> dict[str, Any]:
        import re
        patterns = [
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
            (re.compile(r"\b(GROQ|OPENAI|ANTHROPIC|GEMINI|OPENROUTER|BEARER|AUTH|AUTHORIZATION)[\s:]+[A-Za-z0-9\-_.]+", re.I), "[REDACTED_AUTH]"),
            (re.compile(r"\b(?:api[_-]?key|apikey|token|secret|password|passwd|pwd|private[_-]?key)\b", re.I), "[REDACTED_KEY]"),
            (re.compile(r"\b[A-Za-z0-9]{20,}\b"), "[REDACTED_TOKEN]"),
        ]
        result = dict(context)
        text = str(result.get("description", "")) + " " + str(result.get("input", {}))
        for pattern, replacement in patterns:
            text = pattern.sub(replacement, text)
        result["description"] = text.strip()
        return result


agent_context_manager = AgentContextManager()

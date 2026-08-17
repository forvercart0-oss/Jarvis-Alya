"""Workflow detection and suggestions for JARVIS Phase 21."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

logger = logging.getLogger("jarvis.memory.workflow")


class WorkflowDetector:
    def __init__(self, adaptive_memory: Any | None = None, broadcast: Any | None = None):
        self._adaptive_memory = adaptive_memory
        self._broadcast = broadcast
        self._recent_actions: list[dict[str, Any]] = []

    def set_broadcast(self, broadcast: Any) -> None:
        self._broadcast = broadcast

    def record_action(self, action: str, tool: str, arguments: dict[str, Any]) -> None:
        self._recent_actions.append({
            "action": action,
            "tool": tool,
            "arguments": arguments,
            "timestamp": time.time(),
        })
        if len(self._recent_actions) > 50:
            self._recent_actions = self._recent_actions[-50:]

    def detect_patterns(self, min_repetitions: int = 3) -> list[dict[str, Any]]:
        patterns = []
        if self._adaptive_memory:
            detected = self._adaptive_memory.detect_workflow(
                [a["action"] for a in self._recent_actions[-10:]]
            )
            if detected:
                patterns.append(detected)
                if self._broadcast:
                    try:
                        import asyncio
                        asyncio.get_event_loop().run_until_complete(
                            self._broadcast("workflow_detected", detected)
                        )
                    except Exception:
                        pass
        return patterns

    def suggest_skill(self, workflow: dict[str, Any]) -> dict[str, Any] | None:
        steps = workflow.get("steps", [])
        if not steps or len(steps) < 2:
            return None
        return {
            "suggestion_id": str(uuid.uuid4())[:8],
            "type": "create_skill",
            "workflow_id": workflow.get("id", ""),
            "title": f"Automated Workflow ({len(steps)} steps)",
            "description": f"Create a skill for: {' -> '.join(steps)}",
            "actions": steps,
            "repetitions": workflow.get("repetitions", 0),
        }


class SuggestionEngine:
    def __init__(self, adaptive_memory: Any | None = None):
        self._adaptive_memory = adaptive_memory
        self._suggested: set[str] = set()

    def generate_suggestions(self, profile: str = "jarvis") -> list[dict[str, Any]]:
        suggestions = []
        if self._adaptive_memory:
            workflows = self._adaptive_memory.get_workflows()
            detector = WorkflowDetector(self._adaptive_memory)
            for wf in workflows:
                wf_id = wf.get("id", "")
                if wf_id not in self._suggested:
                    skill_suggestion = detector.suggest_skill(wf)
                    if skill_suggestion:
                        suggestions.append(skill_suggestion)
                        self._suggested.add(wf_id)
        return suggestions

    def mark_suggested(self, suggestion_id: str) -> None:
        self._suggested.add(suggestion_id)


workflow_detector = WorkflowDetector()
suggestion_engine = SuggestionEngine()

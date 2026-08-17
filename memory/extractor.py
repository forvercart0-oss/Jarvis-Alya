"""Automatic memory extraction for JARVIS Phase 16."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from memory.types import MemoryImportance, MemorySource, MemoryType, normalize_memory_type

logger = logging.getLogger("jarvis.memory.extractor")


class MemoryExtractor:
    def __init__(self, memory_manager: Any, ai_provider: Any | None = None):
        self._memory = memory_manager
        self._ai = ai_provider

    def should_remember(self, user_message: str, assistant_response: str) -> str | None:
        lower = user_message.lower()
        if any(k in lower for k in ("remember that", "remember this", "don't forget", "make a note", "save this")):
            return "remember"
        if any(k in lower for k in ("forget that", "forget this", "delete this", "remove this", "don't remember")):
            return "forget"
        if any(k in lower for k in ("update my", "change my", "my preference is")):
            return "update"
        if self._ai:
            try:
                prompt = (
                    "Classify the following user message as one of: REMEMBER, IGNORE, UPDATE, MERGE, DELETE. "
                    "Only respond with the classification word.\n\n"
                    f"User: {user_message}\nAssistant: {assistant_response}"
                )
                result = asyncio.get_event_loop().run_until_complete(
                    self._ai.chat_with_tools([{"role": "user", "content": prompt}], tools_spec=[])
                )
                text = str(result).strip().upper()
                if text in {"REMEMBER", "IGNORE", "UPDATE", "MERGE", "DELETE"}:
                    return text
            except Exception as exc:
                logger.debug("Memory classification failed: %s", exc)
        return "ignore"

    def extract(self, user_message: str, assistant_response: str, project: str | None = None, profile: str = "jarvis") -> dict | None:
        action = self.should_remember(user_message, assistant_response)
        if action == "remember":
            content = user_message
            for prefix in ["remember that", "remember this", "don't forget", "make a note", "save this"]:
                content = re.sub(re.escape(prefix), "", content, flags=re.IGNORECASE).strip()
            if not content:
                return None
            mem_type, importance = self._classify(content)
            return {
                "action": "remember",
                "content": content,
                "category": normalize_memory_type(mem_type),
                "memory_type": mem_type,
                "importance": importance,
                "source": MemorySource.CONVERSATION.value,
                "project": project,
                "profile": profile,
                "confidence": 0.8,
            }
        if action == "forget":
            query = user_message
            for prefix in ["forget that", "forget this", "delete this", "remove this", "don't remember"]:
                query = re.sub(re.escape(prefix), "", query, flags=re.IGNORECASE).strip()
            return {"action": "forget", "query": query}
        if action == "update":
            return {"action": "update", "content": user_message, "project": project, "profile": profile}
        return None

    def extract_from_task(self, task_result: dict[str, Any], project: str | None = None, profile: str = "jarvis") -> dict | None:
        if not task_result.get("success"):
            return None
        summary = task_result.get("summary") or task_result.get("output") or ""
        if not summary or len(summary) < 10:
            return None
        mem_type, importance = self._classify(summary)
        return {
            "action": "remember",
            "content": summary[:500],
            "category": normalize_memory_type(mem_type),
            "memory_type": mem_type,
            "importance": importance,
            "source": MemorySource.TASK.value,
            "project": project,
            "profile": profile,
            "confidence": 0.7,
        }

    def _classify(self, text: str) -> tuple[str, str]:
        lower = text.lower()
        preference_keywords = ["prefer", "like", "don't like", "dislike", "theme", "language", "voice", "style"]
        project_keywords = ["project", "repo", "codebase", "application", "database", "frontend", "backend"]
        decision_keywords = ["decided", "decision", "chosen", "selected", "approved", "rejected"]
        goal_keywords = ["goal", "objective", "target", "plan to", "aim to", "want to"]
        profile_keywords = ["name", "call me", "i am", "my name", "assistant name"]

        if any(k in lower for k in preference_keywords):
            return MemoryType.USER_PREFERENCE.value, MemoryImportance.MEDIUM.value
        if any(k in lower for k in project_keywords):
            return MemoryType.PROJECT.value, MemoryImportance.HIGH.value
        if any(k in lower for k in decision_keywords):
            return MemoryType.DECISION.value, MemoryImportance.HIGH.value
        if any(k in lower for k in goal_keywords):
            return MemoryType.GOAL.value, MemoryImportance.MEDIUM.value
        if any(k in lower for k in profile_keywords):
            return MemoryType.USER_PROFILE.value, MemoryImportance.HIGH.value
        return MemoryType.FACT.value, MemoryImportance.LOW.value

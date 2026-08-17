"""Context builder for JARVIS Phase 16."""

from __future__ import annotations

import logging
from typing import Any

from memory.ranker import MemoryRanker
from memory.types import MemoryType, normalize_memory_type

logger = logging.getLogger("jarvis.memory.context_builder")


class ContextBuilder:
    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def build(self, user_message: str, project: str | None = None, profile: str = "jarvis", max_memories: int = 8, max_tokens: int = 2000, task_type: str | None = None) -> dict:
        raw_memories = self._memory.get_memories_for_context(user_message, project=project, profile=profile, limit=max_memories * 2)
        allowed_categories = self._allowed_categories(task_type)
        filtered = [m for m in raw_memories if normalize_memory_type(m.get("category") or m.get("memory_type")) in allowed_categories]
        ranked = MemoryRanker(self._memory.store).rank(filtered, query=user_message)
        selected = []
        total_chars = 0
        for mem in ranked[:max_memories]:
            text = mem.get("value") or mem.get("key") or ""
            if total_chars + len(text) > max_tokens:
                break
            selected.append({
                "id": mem.get("id"),
                "content": text,
                "type": mem.get("memory_type") or mem.get("category") or "fact",
                "confidence": mem.get("confidence"),
                "importance": mem.get("importance"),
                "source": mem.get("source"),
                "memory_type": mem.get("memory_type"),
                "category": mem.get("category"),
                "project": mem.get("project"),
                "tags": mem.get("tags") or [],
            })
            total_chars += len(text)
        return {
            "memories": selected,
            "token_budget_used": total_chars,
            "retrieved_count": len(selected),
            "query": user_message,
            "project": project,
            "profile": profile,
        }

    def _allowed_categories(self, task_type: str | None) -> set[str]:
        base = {
            MemoryType.USER_PREFERENCE.value,
            MemoryType.USER_PROFILE.value,
            MemoryType.PROJECT.value,
            MemoryType.PROJECT_PREFERENCE.value,
            MemoryType.FACT.value,
            MemoryType.DECISION.value,
            MemoryType.GOAL.value,
            MemoryType.IMPORTANT_CONTEXT.value,
            MemoryType.CONVERSATION.value,
            MemoryType.TASK.value,
            MemoryType.GENERAL.value,
        }
        if task_type == "coding":
            base.update({MemoryType.PROJECT.value, MemoryType.PROJECT_PREFERENCE.value, MemoryType.SKILL.value})
        elif task_type == "research":
            base.update({MemoryType.FACT.value, MemoryType.DECISION.value, MemoryType.CONVERSATION.value})
        elif task_type == "browser":
            base.update({MemoryType.USER_PREFERENCE.value, MemoryType.PROJECT.value})
        return base

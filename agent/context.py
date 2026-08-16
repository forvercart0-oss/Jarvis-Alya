"""Agent context builder for JARVIS Phase 2."""

from __future__ import annotations

from agent.models import AgentContext
from memory.manager import MemoryManager
from safety import classify_request, get_refusal_response
from safety.classifier import SafetyCategory


class AgentContextBuilder:
    def __init__(self, memory: MemoryManager | None = None):
        self._memory = memory

    def build(self, user_request: str, project: str | None = None, project_root: str | None = None, persona: str = "jarvis") -> AgentContext:
        language = "en"
        if self._memory:
            try:
                relevant = self._memory.retrieve_relevant(user_request, limit=3)
                if relevant:
                    language = "en"
            except Exception:
                pass

        classification = classify_request(user_request)
        if classification.category == SafetyCategory.HARMFUL:
            refusal = get_refusal_response(classification, persona, language)
            if refusal:
                pass

        return AgentContext(
            user_request=user_request,
            project=project,
            project_root=project_root,
            language=language,
            persona=persona,
            metadata={
                "safety_category": classification.category.value,
                "safety_confidence": classification.confidence,
            },
        )

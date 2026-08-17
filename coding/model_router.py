"""Coding model router for JARVIS Phase 27."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.coding.model_router")


class CodingModelRouter:
    def __init__(self):
        self._local_enabled = False
        self._groq_enabled = False

    def route(self, task_type: str, size: str = "medium") -> dict[str, Any]:
        if size == "small" and self._local_enabled:
            return {"provider": "local", "model": "local-llm", "reason": "small task, local preferred"}
        if task_type in ("debugging", "architecture", "security_review") and self._groq_enabled:
            return {"provider": "groq", "model": "groq-model", "reason": "complex reasoning task"}
        if self._local_enabled:
            return {"provider": "local", "model": "local-llm", "reason": "local fallback"}
        return {"provider": "groq", "model": "groq-model", "reason": "default provider"}

    def set_local_enabled(self, enabled: bool) -> None:
        self._local_enabled = enabled

    def set_groq_enabled(self, enabled: bool) -> None:
        self._groq_enabled = enabled


coding_model_router = CodingModelRouter()

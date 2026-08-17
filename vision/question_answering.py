"""Visual question answering for JARVIS Phase 17."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.qa")


class VisualQA:
    """Answers natural language questions about visual content."""

    def __init__(self, vision_provider: Any | None = None):
        self._provider = vision_provider

    def set_provider(self, provider: Any) -> None:
        self._provider = provider

    async def answer(self, image_path: str, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        prompts = {
            "what_is_on_screen": "Describe what is currently visible on this screen in one concise sentence.",
            "what_error": "Is there any error message visible on this screen? If yes, quote it exactly.",
            "what_button": f"Is there a button or link labeled '{context.get('target', '') if context else ''}'? If yes, describe its location.",
            "read_screen": "Read and summarize all visible text on this screen.",
            "default": f"{question}",
        }
        lower = question.lower()
        if "error" in lower:
            prompt = prompts["what_error"]
        elif "button" in lower or "link" in lower or "click" in lower:
            prompt = prompts["what_button"]
        elif "read" in lower or "text" in lower:
            prompt = prompts["read_screen"]
        elif "what is" in lower or "what's" in lower:
            prompt = prompts["what_is_on_screen"]
        else:
            prompt = prompts["default"]

        if self._provider:
            try:
                result = await self._provider.analyze_image(image_path, prompt=prompt)
                return {
                    "success": result.success,
                    "answer": result.description or result.text,
                    "confidence": result.confidence,
                    "backend": getattr(self._provider, "name", "unknown"),
                }
            except Exception as exc:
                logger.debug("Visual QA provider failed: %s", exc)

        return {"success": False, "answer": "Vision provider unavailable.", "confidence": 0.0, "backend": "none"}


visual_qa = VisualQA()

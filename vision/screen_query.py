"""Screen query engine for JARVIS Phase 24.

Answers natural language questions about the current screen.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.screen_query")


class ScreenQueryEngine:
    def __init__(self):
        self._understanding_engine = None

    def _get_understanding_engine(self):
        if self._understanding_engine is None:
            from vision.screen_understanding import screen_understanding_engine
            self._understanding_engine = screen_understanding_engine
        return self._understanding_engine

    async def query(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        understanding = self._get_understanding_engine().get_last_understanding()
        if not understanding:
            return {"success": False, "error": "No screen context available. Capture a screen first."}

        lower = question.lower()
        if any(k in lower for k in ["what is", "what's on", "what does", "what am i"]):
            return self._summarize(understanding)
        if any(k in lower for k in ["read", "text on", "content"]):
            return self._read_text(understanding)
        if any(k in lower for k in ["error", "wrong", "not working", "issue"]):
            return self._find_errors(understanding)
        if any(k in lower for k in ["button", "click", "find", "where is", "locate"]):
            return self._find_elements(understanding, question)
        if any(k in lower for k in ["explain", "describe"]):
            return self._explain(understanding)
        if any(k in lower for k in ["application", "app", "program"]):
            return {
                "success": True,
                "answer": f"You are currently using {understanding.application or 'an unknown application'}.",
                "application": understanding.application,
                "window_title": understanding.window_title,
            }
        if any(k in lower for k in ["title", "window"]):
            return {
                "success": True,
                "answer": f"Window title: {understanding.window_title or 'Unknown'}",
                "window_title": understanding.window_title,
            }
        return self._summarize(understanding)

    def _summarize(self, understanding: Any) -> dict[str, Any]:
        app = understanding.application or "Unknown application"
        desc = understanding.description or ""
        ocr_text = understanding.ocr_text
        ocr_preview = ocr_text[:150] + "..." if len(ocr_text) > 150 else ocr_text
        elements = [e.get("label", e.get("type", "")) for e in understanding.detected_elements[:5]]
        summary = f"You're currently viewing {app}"
        if understanding.window_title:
            summary += f" ({understanding.window_title})"
        if desc:
            summary += f". {desc}"
        if elements:
            summary += f". Detected elements: {', '.join(elements)}"
        return {
            "success": True,
            "answer": summary,
            "application": app,
            "window_title": understanding.window_title,
            "ocr_preview": ocr_preview,
            "elements": understanding.detected_elements[:10],
            "confidence": understanding.confidence,
        }

    def _read_text(self, understanding: Any) -> dict[str, Any]:
        text = understanding.ocr_text
        if not text:
            return {"success": True, "answer": "No readable text detected on screen.", "text": ""}
        return {
            "success": True,
            "answer": f"Screen text: {text[:500]}",
            "text": text,
        }

    def _find_errors(self, understanding: Any) -> dict[str, Any]:
        error_patterns = ["error", "exception", "traceback", "failed", "warning", "critical", "fatal"]
        errors = []
        for line in understanding.ocr_text.splitlines():
            if any(p in line.lower() for p in error_patterns):
                errors.append(line.strip())
        if errors:
            return {
                "success": True,
                "answer": f"Found {len(errors)} potential error lines: " + "; ".join(errors[:3]),
                "errors": errors,
            }
        return {"success": True, "answer": "No obvious errors detected on screen.", "errors": []}

    def _find_elements(self, understanding: Any, question: str) -> dict[str, Any]:
        lower = question.lower()
        target = (
            lower.replace("find", "")
            .replace("where is", "")
            .replace("the", "")
            .replace("button", "")
            .replace("click", "")
            .strip()
        )
        matches = []
        for el in understanding.detected_elements:
            label = el.get("label", "").lower()
            if target in label or label in target:
                matches.append(el)
        if matches:
            return {
                "success": True,
                "answer": f"Found {len(matches)} matching element(s).",
                "matches": matches,
            }
        return {"success": True, "answer": f"No elements matching '{target}' detected.", "matches": []}

    def _explain(self, understanding: Any) -> dict[str, Any]:
        desc = understanding.description or "No detailed description available."
        elements = understanding.detected_elements[:8]
        element_summary = []
        for el in elements:
            element_summary.append(f"{el.get('type', 'element')}: {el.get('label', 'unnamed')}")
        explanation = desc
        if element_summary:
            explanation += " Key controls: " + "; ".join(element_summary) + "."
        return {
            "success": True,
            "answer": explanation,
            "description": desc,
            "elements": elements,
        }


screen_query_engine = ScreenQueryEngine()

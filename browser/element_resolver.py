"""Element resolver for JARVIS Phase 25.

Resolves natural language element references using priority chain:
1. accessibility
2. semantic DOM
3. text
4. attributes
5. visual grounding (Phase 24)
6. coordinate fallback
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.element_resolver")


@dataclass
class ResolvedElement:
    element_type: str = "unknown"
    label: str = ""
    selector: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_type": self.element_type,
            "label": self.label,
            "selector": self.selector,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
        }


class ElementResolver:
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold

    async def resolve(self, target: str, context: Any, page: Any = None) -> ResolvedElement | None:
        if not target or not context:
            return None

        elements = getattr(context, "interactive_elements", [])
        analyzed = getattr(context, "analyzed_elements", [])
        accessibility = getattr(context, "accessibility_elements", [])

        element = self._resolve_accessibility(target, accessibility)
        if element and element.confidence >= self.confidence_threshold:
            return element

        element = self._resolve_dom(target, analyzed or elements)
        if element and element.confidence >= self.confidence_threshold:
            return element

        element = self._resolve_semantic(target, context)
        if element and element.confidence >= self.confidence_threshold:
            return element

        if page:
            element = await self._resolve_vision(target, page)
            if element and element.confidence >= self.confidence_threshold:
                return element

        element = self._resolve_fallback(target, analyzed or elements)
        if element:
            return element

        return None

    def _resolve_accessibility(self, target: str, elements: list[Any]) -> ResolvedElement | None:
        lower = target.lower()
        best = None
        best_score = 0.0
        for el in elements:
            if not isinstance(el, dict):
                continue
            name = (el.get("name") or "").lower()
            role = (el.get("role") or "").lower()
            if lower in name or name in lower:
                score = 0.95
                if score > best_score:
                    best = ResolvedElement(
                        element_type=el.get("role", "unknown"),
                        label=el.get("name", ""),
                        confidence=score,
                        source="accessibility",
                        metadata=el,
                    )
                    best_score = score
            elif lower in role:
                score = 0.7
                if score > best_score:
                    best = ResolvedElement(
                        element_type=el.get("role", "unknown"),
                        label=el.get("name", ""),
                        confidence=score,
                        source="accessibility",
                        metadata=el,
                    )
                    best_score = score
        return best

    def _resolve_dom(self, target: str, elements: list[Any]) -> ResolvedElement | None:
        lower = target.lower()
        best = None
        best_score = 0.0
        for el in elements:
            if not isinstance(el, dict):
                continue
            text = (el.get("text") or "").lower()
            label = (el.get("label") or "").lower()
            placeholder = (el.get("placeholder") or "").lower()
            name = (el.get("name") or "").lower()
            score = 0.0
            if lower in text:
                score = 0.9
            elif lower in label:
                score = 0.85
            elif lower in placeholder:
                score = 0.7
            elif lower in name:
                score = 0.65
            if not el.get("visible", True):
                score *= 0.5
            if not el.get("enabled", True):
                score *= 0.3
            if score > best_score:
                best = ResolvedElement(
                    element_type=el.get("type", "unknown"),
                    label=el.get("text") or el.get("label") or "",
                    selector=el.get("selector", ""),
                    confidence=score,
                    source="dom",
                    metadata=el,
                )
                best_score = score
        return best if best_score >= self.confidence_threshold else None

    def _resolve_semantic(self, target: str, context: Any) -> ResolvedElement | None:
        lower = target.lower()
        buttons = getattr(context, "buttons", [])
        inputs = getattr(context, "inputs", [])
        links = getattr(context, "links", [])
        all_elements = []
        for el in buttons:
            all_elements.append({**el, "element_type": "button"})
        for el in inputs:
            all_elements.append({**el, "element_type": el.get("type", "input")})
        for el in links:
            all_elements.append({**el, "element_type": "link"})

        best = None
        best_score = 0.0
        for el in all_elements:
            text = (el.get("text") or "").lower()
            label = (el.get("label") or "").lower()
            aria = (el.get("aria_label") or el.get("aria-label") or "").lower()
            score = 0.0
            if lower in text:
                score = 0.9
            elif lower in label:
                score = 0.85
            elif lower in aria:
                score = 0.8
            if score > best_score:
                best = ResolvedElement(
                    element_type=el.get("element_type", "unknown"),
                    label=el.get("text") or el.get("label") or "",
                    selector=el.get("selector", ""),
                    confidence=score,
                    source="semantic",
                    metadata=el,
                )
                best_score = score
        return best if best_score >= self.confidence_threshold else None

    async def _resolve_vision(self, target: str, page: Any) -> ResolvedElement | None:
        try:
            screenshot = await page.screenshot(full_page=False)
            import os
            import tempfile
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            with open(path, "wb") as f:
                f.write(screenshot)
            try:
                from vision.grounding import VisualGrounding
                from vision.screen_understanding import screen_understanding_engine
                understanding = await screen_understanding_engine.understand(path)
                if understanding and understanding.detected_elements:
                    grounding = VisualGrounding(confidence_threshold=self.confidence_threshold)
                    grounded = grounding.ground(understanding.detected_elements)
                    element = grounding.find_element(grounded, target)
                    if element:
                        return ResolvedElement(
                            element_type=element.element_type,
                            label=element.label,
                            x=element.x,
                            y=element.y,
                            width=element.width,
                            height=element.height,
                            confidence=element.confidence,
                            source="vision",
                        )
            finally:
                with contextlib.suppress(OSError):
                    os.unlink(path)
        except Exception as exc:
            logger.debug("Vision resolution failed: %s", exc)
        return None

    def _resolve_fallback(self, target: str, elements: list[Any]) -> ResolvedElement | None:
        lower = target.lower()
        best = None
        best_score = 0.0
        for el in elements:
            if not isinstance(el, dict):
                continue
            text = (el.get("text") or "").lower()
            label = (el.get("label") or "").lower()
            if lower in text or lower in label:
                score = 0.4
                if score > best_score:
                    best = ResolvedElement(
                        element_type=el.get("type", "unknown"),
                        label=el.get("text") or el.get("label") or "",
                        selector=el.get("selector", ""),
                        confidence=score,
                        source="fallback",
                        metadata=el,
                    )
                    best_score = score
        return best


element_resolver = ElementResolver()

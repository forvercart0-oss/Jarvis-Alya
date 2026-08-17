"""Visual grounding for JARVIS Phase 17."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("jarvis.vision.grounding")


@dataclass
class GroundedElement:
    element_type: str
    label: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    source: str = ""
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.element_type,
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
        }


class VisualGrounding:
    """Maps detected UI elements to screen coordinates."""

    def __init__(self, confidence_threshold: float = 0.70):
        self.confidence_threshold = confidence_threshold

    def ground(self, elements: list[dict[str, Any]], screen_width: int = 0, screen_height: int = 0) -> list[GroundedElement]:
        grounded: list[GroundedElement] = []
        for el in elements:
            confidence = float(el.get("confidence", 0.0))
            if confidence < self.confidence_threshold:
                continue
            bbox = el.get("bbox") or el.get("bounding_box") or {}
            if isinstance(bbox, dict):
                x = int(bbox.get("x", 0))
                y = int(bbox.get("y", 0))
                width = int(bbox.get("width", 0))
                height = int(bbox.get("height", 0))
            else:
                x = y = width = height = 0
            if screen_width and screen_height:
                x = max(0, min(x, screen_width))
                y = max(0, min(y, screen_height))
                width = max(0, min(width, screen_width - x))
                height = max(0, min(height, screen_height - y))
            grounded.append(GroundedElement(
                element_type=el.get("type", "unknown"),
                label=el.get("label", ""),
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=confidence,
                source=el.get("source", "vision"),
                metadata=el.get("metadata", {}),
            ))
        return grounded

    def find_element(self, elements: list[GroundedElement], target: str) -> GroundedElement | None:
        lower = target.lower()
        best = None
        best_score = 0.0
        for el in elements:
            label = el.label.lower()
            if lower in label or label in lower:
                score = el.confidence
                if score > best_score:
                    best = el
                    best_score = score
        return best

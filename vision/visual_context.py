"""Visual context model for JARVIS Phase 17."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class VisualContext:
    timestamp: str = ""
    application: str = ""
    window_title: str = ""
    screen_size: dict[str, int] = field(default_factory=dict)
    ocr_text: str = ""
    detected_elements: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""
    confidence: float = 0.0
    backend: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.screen_size:
            self.screen_size = {"width": 0, "height": 0}

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "application": self.application,
            "window_title": self.window_title,
            "screen_size": self.screen_size,
            "ocr_text": self.ocr_text,
            "detected_elements": self.detected_elements,
            "description": self.description,
            "confidence": self.confidence,
            "backend": self.backend,
            "metadata": self.metadata,
        }

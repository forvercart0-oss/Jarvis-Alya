"""Screen understanding engine for JARVIS Phase 24.

Combines OCR, UI detection, vision model, active window, and accessibility
information into a structured representation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("jarvis.vision.screen_understanding")


@dataclass
class ScreenUnderstanding:
    timestamp: str = ""
    application: str = ""
    window_title: str = ""
    screen_size: dict[str, int] = field(default_factory=dict)
    description: str = ""
    ocr_text: str = ""
    detected_elements: list[dict[str, Any]] = field(default_factory=list)
    accessibility_elements: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    backend: str = ""
    mode: str = ""
    monitor: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()
        if not self.screen_size:
            self.screen_size = {"width": 0, "height": 0}

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "application": self.application,
            "window_title": self.window_title,
            "screen_size": self.screen_size,
            "description": self.description,
            "ocr_text": self.ocr_text,
            "detected_elements": self.detected_elements,
            "accessibility_elements": self.accessibility_elements,
            "confidence": self.confidence,
            "backend": self.backend,
            "mode": self.mode,
            "monitor": self.monitor,
            "metadata": self.metadata,
        }


class ScreenUnderstandingEngine:
    def __init__(self):
        self._last_understanding: ScreenUnderstanding | None = None
        self._cache: dict[str, Any] = {}

    async def understand(
        self,
        image_path: str,
        mode: str = "full",
        monitor: int | None = None,
        window: str | None = None,
    ) -> ScreenUnderstanding:
        understanding = ScreenUnderstanding(mode=mode, monitor=monitor)

        try:
            from vision.capture import get_active_window, get_screen_info
            window_info = await get_active_window()
            if isinstance(window_info, dict):
                understanding.application = window_info.get("app", window_info.get("title", ""))
                understanding.window_title = window_info.get("title", "")
        except Exception as exc:
            logger.debug("Active window detection failed: %s", exc)

        try:
            from vision.capture import get_screen_info
            screen = await get_screen_info()
            if isinstance(screen, dict):
                understanding.screen_size = {
                    "width": screen.get("width", 0),
                    "height": screen.get("height", 0),
                }
        except Exception as exc:
            logger.debug("Screen info detection failed: %s", exc)

        try:
            from vision.ocr import ocr_image
            ocr = await ocr_image(image_path)
            if isinstance(ocr, dict) and ocr.get("text"):
                understanding.ocr_text = ocr.get("text", "")
            elif isinstance(ocr, dict) and not ocr.get("success"):
                logger.debug("OCR failed: %s", ocr.get("error"))
        except Exception as exc:
            logger.debug("OCR failed: %s", exc)

        try:
            from vision.ui_detector import detect_ui_elements
            elements = detect_ui_elements(understanding.ocr_text)
            understanding.detected_elements = elements
        except Exception as exc:
            logger.debug("UI detection failed: %s", exc)

        try:
            from vision.accessibility import get_adapter
            adapter = get_adapter()
            if adapter:
                tree = await adapter.get_element_tree()
                understanding.accessibility_elements = [e.to_dict() for e in tree]
        except Exception as exc:
            logger.debug("Accessibility detection failed: %s", exc)

        try:
            from vision.analyzer import describe_screen
            desc = await describe_screen(image_path)
            if isinstance(desc, dict):
                understanding.description = desc.get("description", "")
                understanding.confidence = desc.get("confidence", 0.0)
                understanding.backend = desc.get("metadata", {}).get("backend", "")
        except Exception as exc:
            logger.debug("Vision description failed: %s", exc)

        if not understanding.description and understanding.ocr_text:
            understanding.description = understanding.ocr_text[:200]
            understanding.confidence = 0.6

        self._last_understanding = understanding
        return understanding

    def get_last_understanding(self) -> ScreenUnderstanding | None:
        return self._last_understanding


screen_understanding_engine = ScreenUnderstandingEngine()

"""Mock vision provider for JARVIS Phase 4."""

from __future__ import annotations

import logging
from typing import Any

from vision.providers.base import VisionProvider, VisionResult

logger = logging.getLogger("jarvis.vision.providers.mock")


class MockVisionProvider(VisionProvider):
    name = "mock"

    async def analyze_image(self, image_path: str, prompt: str = "") -> VisionResult:
        return VisionResult(
            success=True,
            description=f"Mock analysis of {image_path}. Prompt: {prompt or 'none'}",
            confidence=0.8,
        )

    async def detect_elements(self, image_path: str) -> VisionResult:
        return VisionResult(
            success=True,
            elements=[
                {"type": "button", "label": "Mock Button", "x": 100, "y": 200, "width": 120, "height": 40, "confidence": 0.9},
            ],
            confidence=0.9,
        )

    async def describe_screen(self, image_path: str) -> VisionResult:
        return VisionResult(
            success=True,
            description=f"Screen captured at {image_path}. Mock description.",
        )

    async def find_target(self, image_path: str, target: str) -> VisionResult:
        return VisionResult(
            success=True,
            description=f"Found {target}",
            confidence=0.95,
            metadata={"x": 820, "y": 420, "width": 100, "height": 40},
        )

    async def health_check(self) -> dict[str, Any]:
        return {"status": "online", "provider": self.name}

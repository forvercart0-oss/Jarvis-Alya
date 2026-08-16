"""Vision module tests for JARVIS Phase 4."""

from __future__ import annotations

import pytest

from vision.regions import parse_region
from vision.providers.base import VisionProvider, VisionResult
from vision.manager import VisionManager


class MockVisionProvider(VisionProvider):
    name = "test_mock"

    async def analyze_image(self, image_path: str, prompt: str = "") -> VisionResult:
        return VisionResult(success=True, description="test", confidence=0.9)

    async def detect_elements(self, image_path: str) -> VisionResult:
        return VisionResult(success=True, elements=[], confidence=0.9)

    async def describe_screen(self, image_path: str) -> VisionResult:
        return VisionResult(success=True, description="test screen")

    async def find_target(self, image_path: str, target: str) -> VisionResult:
        return VisionResult(success=True, confidence=0.95, metadata={"x": 10, "y": 20, "width": 100, "height": 40})

    async def health_check(self) -> dict:
        return {"status": "online"}


def test_parse_region():
    assert parse_region("100x200+10+20") == {"x": 10, "y": 20, "width": 100, "height": 200}
    assert parse_region("") is None
    assert parse_region("10,20,100,200") == {"x": 10, "y": 20, "width": 100, "height": 200}


def test_vision_manager_registration():
    mgr = VisionManager()
    mgr.register_provider(MockVisionProvider())
    assert len(mgr._providers) == 1


@pytest.mark.asyncio
async def test_vision_manager_status():
    mgr = VisionManager()
    status = mgr.status()
    assert status["enabled"] is False
    assert status["providers"] == 0

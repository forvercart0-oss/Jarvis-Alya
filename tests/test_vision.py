"""Vision module tests for JARVIS Phase 14."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest

from vision.regions import parse_region
from vision.providers.base import VisionProvider, VisionResult
from vision.manager import VisionManager, vision_audit
from vision.image_utils import (
    validate_image,
    preprocess_image,
    image_hash,
    detect_secrets_in_text,
    ImageValidationError,
)
from vision.comparison import compare_images
from vision.camera import CameraManager


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

    async def understand_ui(self, image_path: str) -> VisionResult:
        return VisionResult(success=True, description="ui understood", confidence=0.9)

    async def answer_visual_question(self, image_path: str, question: str) -> VisionResult:
        return VisionResult(success=True, description="answer", confidence=0.9)

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


@pytest.mark.asyncio
async def test_vision_manager_disabled():
    mgr = VisionManager()
    result = await mgr.analyze("/tmp/nonexistent.png", "test")
    assert result["success"] is False
    assert "disabled" in result.get("error", "").lower()


@pytest.mark.asyncio
async def test_vision_manager_screenshot_disabled():
    mgr = VisionManager()
    result = await mgr.screenshot()
    assert result["success"] is False
    assert "disabled" in result.get("error", "").lower()


@pytest.mark.asyncio
async def test_vision_manager_compare_disabled():
    mgr = VisionManager()
    result = await mgr.compare("/tmp/a.png", "/tmp/b.png")
    assert result["success"] is False
    assert "disabled" in result.get("error", "").lower()


@pytest.mark.asyncio
async def test_vision_manager_camera_operations():
    mgr = VisionManager()
    with patch("vision.permissions.vision_capture", return_value={"allowed": True}):
        start = await mgr.camera_start()
        assert start["success"] is True
        assert mgr.camera_active is True
        stop = await mgr.camera_stop()
        assert stop["success"] is True
        assert mgr.camera_active is False
    status = mgr.status()
    assert status.get("camera_active") is False


def test_validate_image_valid(tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"PNGDATA1234")
    result = validate_image(str(img))
    assert result["valid"] is True
    assert result["extension"] == ".png"


def test_validate_image_missing():
    with pytest.raises(ImageValidationError):
        validate_image("/tmp/nonexistent_xyz_123.png")


def test_validate_image_unsupported_format(tmp_path):
    img = tmp_path / "test.txt"
    img.write_text("hello")
    with pytest.raises(ImageValidationError):
        validate_image(str(img))


def test_validate_image_too_large(tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"PNGDATA1234")
    with pytest.raises(ImageValidationError):
        validate_image(str(img), max_size_mb=0.000001)


def test_image_hash():
    h = image_hash(__file__)
    assert isinstance(h, str)
    assert len(h) == 16


def test_detect_secrets_in_text():
    assert len(detect_secrets_in_text("")) == 0
    findings = detect_secrets_in_text("api_key=sk-1234567890abcdefghij")
    assert len(findings) >= 1
    findings2 = detect_secrets_in_text("no secrets here")
    assert len(findings2) == 0


@pytest.mark.asyncio
async def test_compare_images_identical():
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_header)
        a = f.name
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_header)
        b = f.name
    try:
        result = await compare_images(a, b)
        assert result["success"] is True
    finally:
        os.unlink(a)
        os.unlink(b)


@pytest.mark.asyncio
async def test_camera_manager():
    cam = CameraManager()
    assert cam.active is False
    start = await cam.start()
    assert start["success"] is True
    assert cam.active is True
    stop = await cam.stop()
    assert stop["success"] is True
    assert cam.active is False


def test_vision_audit_logger():
    vision_audit.clear()
    vision_audit.log("test_event", {"key": "value"})
    events = vision_audit.events()
    assert len(events) == 1
    assert events[0]["event"] == "test_event"
    assert events[0]["data"]["key"] == "value"

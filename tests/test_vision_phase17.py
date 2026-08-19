"""Tests for Phase 17 Vision + Screen Understanding 2.0."""

from __future__ import annotations

import os
import tempfile

import pytest

from vision.screen import SystemScreenCaptureProvider, WindowInfo, ScreenInfo
from vision.ocr_preprocessor import ocr_preprocessor
from vision.visual_context import VisualContext
from vision.ui_detector import detect_ui_elements, classify_command
from vision.grounding import VisualGrounding, GroundedElement
from vision.question_answering import VisualQA
from vision.sensitive import sensitive_detector


def test_window_info_defaults():
    w = WindowInfo(title="Test", app="Firefox")
    assert w.title == "Test"
    assert w.app == "Firefox"
    assert w.x == 0
    assert w.is_active is False


def test_screen_info_defaults():
    s = ScreenInfo()
    assert s.width == 0
    assert s.height == 0
    assert s.monitors == []


def test_screen_provider_singleton():
    from vision.screen import get_screen_provider
    p1 = get_screen_provider()
    p2 = get_screen_provider()
    assert p1 is p2


@pytest.mark.asyncio
async def test_screen_provider_health_check():
    provider = SystemScreenCaptureProvider()
    result = await provider.health_check()
    assert "status" in result


def test_ocr_preprocessor_available():
    assert ocr_preprocessor.available in (True, False)


@pytest.mark.asyncio
async def test_ocr_preprocess_returns_result():
    from PIL import Image
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    Image.new("RGB", (100, 100), color="white").save(path)
    res = await ocr_preprocessor.preprocess(path)
    assert res.success in (True, False)
    os.unlink(path)


def test_visual_context_to_dict():
    ctx = VisualContext(application="Firefox", window_title="GitHub", description="test")
    d = ctx.to_dict()
    assert d["application"] == "Firefox"
    assert d["window_title"] == "GitHub"
    assert "timestamp" in d


def test_visual_context_default_timestamp():
    ctx = VisualContext()
    assert ctx.timestamp != ""


def test_ui_detector_finds_buttons():
    elements = detect_ui_elements("Click the Submit button to continue")
    types = [e["type"] for e in elements]
    assert "button" in types


def test_ui_detector_finds_inputs():
    elements = detect_ui_elements("Enter your email in the input field")
    types = [e["type"] for e in elements]
    assert "input" in types


def test_ui_detector_empty_text():
    elements = detect_ui_elements("")
    assert elements == []


def test_classify_command_read():
    assert classify_command("What is on my screen?") == "read"


def test_classify_command_click():
    assert classify_command("Click the login button") == "click"


def test_classify_command_type():
    assert classify_command("Type hello world") == "type"


def test_classify_command_scroll():
    assert classify_command("Scroll down") == "scroll"


def test_classify_command_find():
    assert classify_command("Find the settings button") == "find"


def test_classify_command_open():
    assert classify_command("Open Firefox") == "open"


def test_grounding_filters_by_confidence():
    grounding = VisualGrounding(confidence_threshold=0.8)
    elements = [
        {"type": "button", "label": "Submit", "confidence": 0.9, "bbox": {"x": 10, "y": 20, "width": 100, "height": 30}},
        {"type": "button", "label": "Cancel", "confidence": 0.5, "bbox": {"x": 120, "y": 20, "width": 100, "height": 30}},
    ]
    grounded = grounding.ground(elements, screen_width=1920, screen_height=1080)
    assert len(grounded) == 1
    assert grounded[0].label == "Submit"


def test_grounding_find_element():
    grounding = VisualGrounding(confidence_threshold=0.0)
    elements = [
        {"type": "button", "label": "Settings", "confidence": 0.9, "bbox": {"x": 0, "y": 0, "width": 100, "height": 30}},
        {"type": "button", "label": "Login", "confidence": 0.8, "bbox": {"x": 0, "y": 0, "width": 100, "height": 30}},
    ]
    grounded = grounding.ground(elements)
    found = grounding.find_element(grounded, "settings")
    assert found is not None
    assert found.label == "Settings"


def test_grounded_element_to_dict():
    el = GroundedElement(element_type="button", label="OK", x=10, y=20, width=100, height=30, confidence=0.9)
    d = el.to_dict()
    assert d["type"] == "button"
    assert d["x"] == 10
    assert d["confidence"] == 0.9


def test_sensitive_detector_is_sensitive_text():
    sensitive, hits = sensitive_detector.is_sensitive_text("My api_key is sk-1234567890abcdefghij")
    assert sensitive is True


def test_sensitive_detector_not_sensitive():
    sensitive, hits = sensitive_detector.is_sensitive_text("Hello world")
    assert sensitive is False


def test_sensitive_detector_screen():
    is_sensitive, reason = sensitive_detector.is_sensitive_screen("Enter your password", "Login")
    assert is_sensitive is True


def test_sensitive_detector_redact():
    text = "My api_key is sk-1234567890abcdefghij and password is secret123"
    redacted = sensitive_detector.redact(text)
    assert "[REDACTED]" in redacted


@pytest.mark.asyncio
async def test_visual_qa_no_provider():
    qa = VisualQA()
    res = await qa.answer("/tmp/nonexistent.png", "What is on screen?")
    assert res["success"] is False

"""Tests for Phase 24 Screen Intelligence 2.0."""

from __future__ import annotations


from vision.screen_understanding import ScreenUnderstanding
from vision.action_planner import VisualActionPlanner
from vision.screen_diff import ScreenDiffEngine
from vision.wait_for_element import WaitForElement, SmartWait
from vision.accessibility import AccessibilityElement, get_adapter
from vision.action_verification import ActionVerifier
from vision.action_log import ActionLogger, ActionLogEntry
from vision.screen_intelligence import ScreenIntelligenceMode
from vision.ocr_providers import OCRResult, OCRTextRegion, TesseractOCRProvider


def test_screen_understanding_defaults():
    u = ScreenUnderstanding()
    assert u.application == ""
    assert u.window_title == ""
    assert u.screen_size == {"width": 0, "height": 0}
    assert u.timestamp != ""


def test_screen_understanding_to_dict():
    u = ScreenUnderstanding(application="Firefox", window_title="GitHub", description="test")
    d = u.to_dict()
    assert d["application"] == "Firefox"
    assert d["window_title"] == "GitHub"
    assert "timestamp" in d


def test_action_planner_click():
    planner = VisualActionPlanner()
    plan = planner.plan("Click the login button")
    assert len(plan.actions) > 0
    assert plan.actions[0].action_type == "find_and_click"


def test_action_planner_scroll():
    planner = VisualActionPlanner()
    plan = planner.plan("Scroll down 5")
    assert plan.actions[0].action_type == "scroll"
    assert plan.actions[0].arguments.get("amount") == 5


def test_action_planner_type():
    planner = VisualActionPlanner()
    plan = planner.plan('Type "hello world"')
    assert plan.actions[0].action_type == "find_and_type"


def test_action_planner_summarize():
    planner = VisualActionPlanner()
    plan = planner.plan("What is on my screen?")
    assert len(plan.actions) > 0
    assert plan.actions[0].action_type in ("summarize_screen", "query_screen")


def test_action_planner_explain():
    planner = VisualActionPlanner()
    plan = planner.plan("Explain this screen")
    assert plan.actions[0].action_type == "explain_screen"


def test_action_planner_find():
    planner = VisualActionPlanner()
    plan = planner.plan("Find the settings button")
    assert plan.actions[0].action_type == "find_element"


def test_action_plan_to_dict():
    planner = VisualActionPlanner()
    plan = planner.plan("Click the submit button")
    d = plan.to_dict()
    assert "goal" in d
    assert "actions" in d
    assert "confidence" in d


def test_screen_diff_engine():
    engine = ScreenDiffEngine()
    diff = engine.diff("hello world", "Window A", [], "hash1")
    assert diff.has_changes is False
    diff2 = engine.diff("hello changed", "Window B", [{"label": "new"}], "hash2")
    assert diff2.has_changes is True


def test_screen_diff_reset():
    engine = ScreenDiffEngine()
    engine.diff("hello", "Window A", [], "hash1")
    engine.reset()
    diff = engine.diff("hello2", "Window B", [], "hash2")
    assert diff.has_changes is False


def test_ocr_text_region():
    region = OCRTextRegion(text="Hello", bounding_box=[10, 20, 100, 40], confidence=0.95)
    d = region.to_dict()
    assert d["text"] == "Hello"
    assert d["confidence"] == 0.95


def test_ocr_result():
    result = OCRResult(success=True, text="test", backend="tesseract")
    d = result.to_dict()
    assert d["success"] is True
    assert d["backend"] == "tesseract"


def test_accessibility_element():
    el = AccessibilityElement(role="button", name="Submit", x=100, y=200, width=120, height=40)
    d = el.to_dict()
    assert d["role"] == "button"
    assert d["name"] == "Submit"
    assert d["x"] == 100


def test_get_adapter_returns_none_on_unsupported():
    import platform
    original = platform.system
    platform.system = lambda: "unsupported"
    try:
        adapter = get_adapter()
        assert adapter is None
    finally:
        platform.system = original


def test_action_log_entry_redacts_password():
    entry = ActionLogEntry(action="type", target="password field", arguments={"text": "password=secret123"})
    d = entry.to_dict()
    assert "[REDACTED]" in d["arguments"]["text"]


def test_action_logger():
    logger = ActionLogger(max_entries=10)
    logger.log(ActionLogEntry(action="click", target="button", success=True))
    entries = logger.get_entries(5)
    assert len(entries) == 1
    assert entries[0]["action"] == "click"


def test_action_logger_clear():
    logger = ActionLogger()
    logger.log(ActionLogEntry(action="click", success=True))
    logger.clear()
    assert len(logger.get_entries()) == 0


def test_screen_intelligence_mode_values():
    assert ScreenIntelligenceMode.OFF == "off"
    assert ScreenIntelligenceMode.ON_DEMAND == "on_demand"
    assert ScreenIntelligenceMode.CONTINUOUS == "continuous"


def test_wait_for_element_timeout():
    import asyncio

    async def run():
        waiter = WaitForElement(timeout=0.1, poll_interval=0.05)
        async def always_fail():
            return {"success": False}
        result = await waiter.wait_for_element(always_fail)
        assert result["success"] is False
        assert result["timeout"] is True

    asyncio.run(run())


def test_wait_for_element_success():
    import asyncio

    async def run():
        waiter = WaitForElement(timeout=1.0, poll_interval=0.1)
        call_count = 0
        async def succeed_on_second():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                return {"success": True, "found": True}
            return {"success": False}
        result = await waiter.wait_for_element(succeed_on_second)
        assert result["success"] is True
        assert result["found"] is True

    asyncio.run(run())


def test_smart_wait_imports():
    assert SmartWait is not None
    assert hasattr(SmartWait, "wait_for_page_load")
    assert hasattr(SmartWait, "wait_for_window")
    assert hasattr(SmartWait, "wait_for_dialog")
    assert hasattr(SmartWait, "wait_for_button_enabled")


def test_action_verifier_imports():
    assert ActionVerifier is not None
    assert hasattr(ActionVerifier, "verify_click")
    assert hasattr(ActionVerifier, "verify_screen_changed")
    assert hasattr(ActionVerifier, "verify_element_present")


def test_tesseract_provider_health_check():
    import asyncio
    provider = TesseractOCRProvider()
    result = asyncio.run(provider.health_check())
    assert "status" in result
    assert "backend" in result

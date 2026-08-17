"""Tests for Phase 30 Advanced Computer Vision + Screen Understanding 2.0."""

from __future__ import annotations

import pytest

from vision.application_understanding import ApplicationUnderstanding, application_understanding
from vision.dialog_detection import DialogDetector, DialogDetectionResult, dialog_detector
from vision.workflow_recorder import WorkflowRecorder, RecordedWorkflow, RecordedStep, workflow_recorder
from vision.workflow_replay import WorkflowReplayer, workflow_replayer
from vision.visual_skills import VisualSkillManager, VisualSkill, visual_skill_manager
from vision.gesture import GestureController, GestureDetector, get_gesture, GESTURES


def test_application_understanding_detects_firefox():
    au = ApplicationUnderstanding()
    result = au.detect_application("Firefox - GitHub", "")
    assert result["application"] == "firefox"
    assert result["confidence"] > 0


def test_application_understanding_detects_vscode():
    au = ApplicationUnderstanding()
    result = au.detect_application("Visual Studio Code", "")
    assert result["application"] == "vscode"


def test_application_understanding_detects_terminal():
    au = ApplicationUnderstanding()
    result = au.detect_application("Terminal - user@host", "")
    assert result["application"] == "terminal"


def test_application_understanding_unknown():
    au = ApplicationUnderstanding()
    result = au.detect_application("Some Random App", "")
    assert result["application"] == "unknown"


def test_application_context_terminal():
    au = ApplicationUnderstanding()
    ctx = au.get_application_context("terminal", "$ ls\n$ echo hello\n")
    assert ctx["state"] == "terminal"
    assert "terminal" in ctx["elements"]


def test_application_context_editor():
    au = ApplicationUnderstanding()
    ctx = au.get_application_context("vscode", "main.py\nutils.py\n")
    assert ctx["state"] == "editor"
    assert "editor" in ctx["elements"]


def test_application_context_file_manager():
    au = ApplicationUnderstanding()
    ctx = au.get_application_context("dolphin", "Documents/\nDownloads/\nfile.txt\n")
    assert ctx["state"] == "file_manager"
    assert "Documents/" in ctx.get("folders", [])


def test_application_context_browser():
    au = ApplicationUnderstanding()
    ctx = au.get_application_context("firefox", "https://github.com/jarvis-alya\n")
    assert ctx["state"] == "browser"
    assert "https://github.com/jarvis-alya" in ctx.get("urls", [])


def test_application_understanding_singleton():
    assert application_understanding is not None
    assert hasattr(application_understanding, "detect_application")
    assert hasattr(application_understanding, "get_application_context")


def test_dialog_detector_confirmation():
    detector = DialogDetector()
    result = detector.detect("Do you want to save changes? [OK] [Cancel]")
    assert result is not None
    assert result.dialog_type == "confirmation"


def test_dialog_detector_error():
    detector = DialogDetector()
    result = detector.detect("Error: File not found")
    assert result is not None
    assert result.dialog_type == "error"


def test_dialog_detector_login():
    detector = DialogDetector()
    result = detector.detect("Please enter your username and password")
    assert result is not None
    assert result.dialog_type == "login"


def test_dialog_detector_permission():
    detector = DialogDetector()
    result = detector.detect("Allow this application to access your files?")
    assert result is not None
    assert result.dialog_type == "permission"


def test_dialog_detector_destructive():
    detector = DialogDetector()
    result = detector.detect("Are you sure you want to permanently delete this file?")
    assert result is not None
    assert result.destructive is True


def test_dialog_detector_captcha():
    detector = DialogDetector()
    result = detector.detect("CAPTCHA: Select all squares with traffic lights")
    assert result is not None
    assert result.captcha is True


def test_dialog_detector_no_dialog():
    detector = DialogDetector()
    result = detector.detect("Hello world, this is normal text.")
    assert result is None


def test_dialog_detector_warning():
    detector = DialogDetector()
    result = detector.detect("Warning: Low disk space")
    assert result is not None
    assert result.dialog_type == "warning"


def test_workflow_recorder_start_stop():
    recorder = WorkflowRecorder()
    workflow = recorder.start("test_workflow")
    assert workflow.name == "test_workflow"
    assert recorder.recording is True
    stopped = recorder.stop()
    assert stopped.workflow_id == workflow.workflow_id
    assert recorder.recording is False


def test_workflow_recorder_record_step():
    recorder = WorkflowRecorder()
    recorder.start("test")
    step = recorder.record_step(action_type="click", target="button", success=True)
    assert step.action_type == "click"
    assert step.target == "button"
    assert step.success is True
    workflow = recorder.stop()
    assert len(workflow.steps) == 1


def test_workflow_recorder_no_active_recording():
    recorder = WorkflowRecorder()
    with pytest.raises(RuntimeError):
        recorder.record_step(action_type="click")


def test_workflow_recorder_get_current():
    recorder = WorkflowRecorder()
    assert recorder.get_current() is None
    workflow = recorder.start("test")
    assert recorder.get_current() is workflow


def test_recorded_workflow_to_dict():
    workflow = RecordedWorkflow(name="test")
    workflow.steps.append(RecordedStep(action_type="click", target="btn"))
    d = workflow.to_dict()
    assert d["name"] == "test"
    assert len(d["steps"]) == 1
    assert d["steps"][0]["action_type"] == "click"


def test_recorded_step_defaults():
    step = RecordedStep()
    assert step.step_id != ""
    assert step.timestamp > 0
    assert step.success is False


def test_workflow_replayer_unsupported_action():
    import asyncio

    async def run():
        replayer = WorkflowReplayer()
        workflow = {
            "steps": [
                {"action_type": "unknown_action", "target": "something"}
            ]
        }
        result = await replayer.replay(workflow)
        assert result["success"] is False
        assert len(result["results"]) == 1

    asyncio.run(run())


def test_workflow_replayer_stop():
    import asyncio

    async def run():
        replayer = WorkflowReplayer()
        assert replayer._stopped is False
        replayer.stop()
        assert replayer._stopped is True

    asyncio.run(run())


def test_visual_skill_from_dict():
    data = {
        "name": "Open Dev Environment",
        "trigger": "open development environment",
        "steps": [{"action": "open", "target": "vscode"}],
        "verification": [{"type": "window", "title": "Visual Studio Code"}],
    }
    skill = VisualSkill.from_dict(data)
    assert skill.name == "Open Dev Environment"
    assert skill.trigger == "open development environment"
    assert len(skill.steps) == 1
    assert len(skill.verification) == 1


def test_visual_skill_to_dict():
    skill = VisualSkill(name="Test Skill", trigger="test trigger")
    d = skill.to_dict()
    assert d["name"] == "Test Skill"
    assert d["trigger"] == "test trigger"


def test_visual_skill_manager_find_by_trigger():
    manager = VisualSkillManager(skills_dir="/nonexistent")
    manager._skills["open dev"] = VisualSkill(name="Open Dev", trigger="open development environment")
    skill = manager.find_by_trigger("open development environment")
    assert skill is not None
    assert skill.name == "Open Dev"


def test_visual_skill_manager_list():
    manager = VisualSkillManager(skills_dir="/nonexistent")
    manager._skills["test"] = VisualSkill(name="Test", trigger="test")
    skills = manager.list_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "Test"


def test_gesture_get_default():
    gesture = get_gesture("open_palm")
    assert gesture is not None
    assert gesture.id == "open_palm"
    assert gesture.name == "Open Palm"


def test_gesture_get_unknown():
    gesture = get_gesture("unknown_gesture")
    assert gesture is None


def test_gestures_list():
    assert len(GESTURES) > 0
    ids = [g.id for g in GESTURES]
    assert "open_palm" in ids
    assert "thumbs_up" in ids
    assert "point" in ids


def test_gesture_controller_handle():
    controller = GestureController(settings=None)
    controller._load_defaults()
    action = controller.handle_gesture("thumbs_up")
    assert action == "confirm"


def test_gesture_detector_is_available():
    detector = GestureDetector(settings=None)
    assert detector.is_available() is False


def test_gesture_controller_on_action_callback():
    controller = GestureController(settings=None)
    callback_invoked = []

    def callback(gesture_id, action):
        callback_invoked.append((gesture_id, action))

    controller.on_action(callback)
    controller.handle_gesture("point")
    assert len(callback_invoked) == 1
    assert callback_invoked[0] == ("point", "select")


def test_dialog_detection_result_to_dict():
    result = DialogDetectionResult(
        dialog_type="login",
        destructive=False,
        captcha=False,
        confidence=0.9,
        matched_text="password",
    )
    d = result.to_dict()
    assert d["dialog_type"] == "login"
    assert d["confidence"] == 0.9
    assert d["matched_text"] == "password"


def test_application_understanding_terminal_errors():
    au = ApplicationUnderstanding()
    ctx = au._analyze_terminal("Error: Connection refused\nTraceback (most recent call last):\n")
    assert len(ctx["errors"]) > 0
    assert "terminal" in ctx["elements"]


def test_application_understanding_discord():
    au = ApplicationUnderstanding()
    ctx = au._analyze_discord("#general\nHey everyone!")
    assert ctx["state"] == "discord"


def test_workflow_recorder_reset():
    recorder = WorkflowRecorder()
    recorder.start("test")
    recorder.record_step(action_type="click")
    recorder.stop()
    recorder._recording = False
    recorder._current_workflow = None
    assert recorder.recording is False
    assert recorder.get_current() is None


def test_visual_skill_manager_load_skills_empty_dir():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = VisualSkillManager(skills_dir=tmpdir)
        manager.load_skills()
        assert len(manager.list_skills()) == 0


def test_workflow_replayer_click_mocked():
    import asyncio
    from unittest.mock import patch, AsyncMock

    async def run():
        replayer = WorkflowReplayer()
        workflow = {
            "steps": [
                {
                    "action_type": "type",
                    "text_entered": "hello",
                }
            ]
        }
        mock_type = AsyncMock(return_value={"success": True})
        with patch("vision.actions.keyboard_type", mock_type):
            result = await replayer.replay(workflow)
            assert result["success"] is True
            mock_type.assert_called_once_with("hello")

    asyncio.run(run())


def test_application_understanding_browser_urls():
    au = ApplicationUnderstanding()
    ctx = au._analyze_browser("Visit https://github.com and https://gitlab.com")
    assert len(ctx["urls"]) == 2
    assert "https://github.com" in ctx["urls"]


def test_application_understanding_file_manager_items():
    au = ApplicationUnderstanding()
    ctx = au._analyze_file_manager("Documents/\nDownloads/\nreport.pdf\nimage.png\n")
    assert len(ctx["folders"]) == 2
    assert len(ctx["files"]) == 2

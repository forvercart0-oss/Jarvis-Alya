"""Tests for Phase 19 Advanced Computer Control 2.0."""

from __future__ import annotations

import asyncio
import pytest

from computer.window_manager import WindowManager, window_manager
from computer.app_manager import ApplicationManager, app_manager
from computer.file_manager import FileManager, file_manager
from computer.terminal import TerminalProvider, terminal_provider
from computer.processes import ProcessManager, process_manager
from computer.clipboard import ClipboardProvider, clipboard_provider
from computer.task_planner import ComputerTaskPlanner, ComputerTask, ComputerTaskState, computer_planner
from computer.takeover import ComputerTakeover, computer_takeover
from computer.trust import ComputerPermissionManager, TrustLevel, computer_permission_manager
from computer.safety import ComputerSafety


@pytest.mark.asyncio
async def test_window_manager_find_by_title():
    wm = WindowManager(provider=None)
    assert await wm.find_by_title("Firefox") is None


@pytest.mark.asyncio
async def test_app_manager_is_running_no_provider():
    am = ApplicationManager(provider=None)
    assert await am.is_running("firefox") is False


def test_file_manager_list_home():
    result = file_manager.list("")
    assert result.get("success") is True


def test_file_manager_search():
    result = file_manager.search(".py")
    assert result.get("success") is True
    assert "results" in result


def test_file_manager_create_folder(tmp_path):
    target = str(tmp_path / "new_folder")
    result = file_manager.create_folder(target)
    assert result.get("success") is True


def test_terminal_classify_safe():
    assert terminal_provider.classify_command("python --version") == "SAFE"


def test_terminal_classify_destructive():
    assert terminal_provider.classify_command("rm -rf /tmp/test") == "DESTRUCTIVE"


def test_terminal_classify_sensitive():
    assert terminal_provider.classify_command("apt install package") == "SENSITIVE"


def test_clipboard_read_no_pyperclip():
    cp = ClipboardProvider()
    result = cp.read()
    assert "success" in result


@pytest.mark.asyncio
async def test_process_manager_find_no_provider():
    pm = ProcessManager(provider=None)
    assert await pm.find("python") is None


def test_task_planner_create_task():
    task = computer_planner.create_task("Open project")
    assert task.goal == "Open project"
    assert task.state == ComputerTaskState.IDLE


def test_task_planner_can_act():
    task = computer_planner.create_task("Test")
    assert computer_planner.can_act(task) is True


def test_task_planner_record_action():
    task = computer_planner.create_task("Test")
    computer_planner.record_action(task, "navigate", {"url": "https://example.com"})
    assert task.action_count == 1


def test_task_planner_max_actions():
    task = computer_planner.create_task("Test", max_actions=2)
    computer_planner.record_action(task, "navigate", {})
    computer_planner.record_action(task, "click", {})
    assert computer_planner.can_act(task) is False


def test_task_planner_checkpoints():
    task = computer_planner.create_task("Test")
    computer_planner.add_checkpoint(task, "opened", {"ok": True})
    assert len(task.checkpoints) == 1


def test_task_planner_retry():
    task = computer_planner.create_task("Test")
    task.max_retries = 2
    assert computer_planner.should_retry(task) is True
    computer_planner.increment_retry(task)
    assert computer_planner.should_retry(task) is True
    computer_planner.increment_retry(task)
    assert computer_planner.should_retry(task) is False


def test_takeover_enable_disable():
    computer_takeover._takeover_sessions.clear()
    result = computer_takeover.enable("default")
    assert result["takeover"] is True
    assert computer_takeover.is_takeover("default") is True
    result = computer_takeover.disable("default")
    assert result["takeover"] is False


def test_permission_manager_ask_always():
    mgr = ComputerPermissionManager(trust_level=TrustLevel.ASK_ALWAYS)
    assert mgr.requires_confirmation("FILE_WRITE") is True
    assert mgr.is_allowed("FILE_WRITE") is True


def test_permission_manager_trusted():
    mgr = ComputerPermissionManager(trust_level=TrustLevel.TRUSTED)
    assert mgr.requires_confirmation("FILE_DELETE") is False
    assert mgr.is_allowed("FILE_DELETE") is True


def test_permission_manager_disabled():
    mgr = ComputerPermissionManager(trust_level=TrustLevel.DISABLED)
    assert mgr.is_allowed("READ_PAGE") is False


def test_permission_manager_override():
    mgr = ComputerPermissionManager(trust_level=TrustLevel.ASK_ALWAYS)
    mgr.override("READ_PAGE", TrustLevel.TRUSTED)
    assert mgr.requires_confirmation("READ_PAGE") is False


def test_safety_classify_command():
    assert ComputerSafety.classify_command("python --version") == "SAFE"
    assert ComputerSafety.classify_command("rm -rf /tmp/test") == "DESTRUCTIVE"
    assert ComputerSafety.classify_command("sudo apt install") == "SENSITIVE"


def test_safety_is_dangerous_command():
    assert ComputerSafety.is_dangerous_command("rm -rf /") is True
    assert ComputerSafety.is_dangerous_command("ls") is False


def test_safety_is_sensitive_command():
    assert ComputerSafety.is_sensitive_command("sudo apt install") is True
    assert ComputerSafety.is_sensitive_command("echo hello") is False


def test_computer_task_state_enum():
    assert ComputerTaskState.IDLE.value == "idle"
    assert ComputerTaskState.EXECUTING.value == "executing"


def test_computer_task_to_dict():
    task = ComputerTask(goal="Test", state=ComputerTaskState.PLANNING)
    d = task.to_dict()
    assert d["goal"] == "Test"
    assert d["state"] == "planning"


def test_computer_planner_takeover():
    task = computer_planner.create_task("Test")
    computer_planner.set_takeover("default", True)
    assert computer_planner.is_takeover("default") is True
    assert computer_planner.can_act(task) is False


def test_file_manager_delete_protection():
    result = file_manager.delete("/etc/passwd")
    assert result.get("success") is False or result.get("error") is not None

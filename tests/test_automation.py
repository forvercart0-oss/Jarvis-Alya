"""Tests for Phase 5 automation system."""

from __future__ import annotations

import asyncio

import pytest

from automation.policies import classify_task_complexity, get_policy_for_complexity, get_tool_risk
from automation.task_state import TaskComplexity, TaskState
from automation.verifier import ActionVerifier


def test_classify_simple():
    assert classify_task_complexity("Open Firefox") == TaskComplexity.SIMPLE


def test_classify_moderate():
    assert classify_task_complexity("Open GitHub and check my repository") == TaskComplexity.MODERATE


def test_classify_complex():
    assert classify_task_complexity("Build and test an ecommerce application") == TaskComplexity.COMPLEX


def test_get_policy_simple():
    policy = get_policy_for_complexity(TaskComplexity.SIMPLE)
    assert policy.timeout_seconds == 60.0
    assert policy.max_retries == 2
    assert policy.auto_execute is True


def test_get_policy_complex():
    policy = get_policy_for_complexity(TaskComplexity.COMPLEX)
    assert policy.timeout_seconds == 600.0
    assert policy.max_retries == 3


def test_get_tool_risk():
    assert get_tool_risk("read_file") == "minimal"
    assert get_tool_risk("shutdown") == "critical"
    assert get_tool_risk("unknown_tool") == "medium"


def test_verifier_success():
    v = ActionVerifier()
    ok, msg = v.verify("read_file", {"success": True, "content": "hello"})
    assert ok is True


def test_verifier_failure():
    v = ActionVerifier()
    ok, msg = v.verify("terminal", {"success": False, "error": "command not found"})
    assert ok is False


def test_verifier_missing_result():
    v = ActionVerifier()
    ok, msg = v.verify("read_file", None)
    assert ok is False


def test_task_states():
    assert TaskState.PENDING.value == "pending"
    assert TaskState.RUNNING.value == "running"
    assert TaskState.COMPLETED.value == "completed"
    assert TaskState.FAILED.value == "failed"
    assert TaskState.CANCELLED.value == "cancelled"
    assert TaskState.PAUSED.value == "paused"


def test_task_complexity_values():
    assert TaskComplexity.SIMPLE.value == "simple"
    assert TaskComplexity.MODERATE.value == "moderate"
    assert TaskComplexity.COMPLEX.value == "complex"


def test_active_states():
    from automation.task_state import ACTIVE_STATES
    assert TaskState.RUNNING in ACTIVE_STATES
    assert TaskState.PAUSED in ACTIVE_STATES
    assert TaskState.COMPLETED not in ACTIVE_STATES


def test_terminal_states():
    from automation.task_state import TERMINAL_STATES
    assert TaskState.COMPLETED in TERMINAL_STATES
    assert TaskState.FAILED in TERMINAL_STATES
    assert TaskState.CANCELLED in TERMINAL_STATES
    assert TaskState.RUNNING not in TERMINAL_STATES

"""Phase 22 tests: Full Auto Mode, Autonomous Execution, and Automation Policies."""

from __future__ import annotations

import asyncio
import logging

import pytest

from automation.execution_engine import AutonomousExecutionEngine, ExecutionContext, ExecutionMode, ExecutionPath
from automation.policy_engine import AutomationPolicyEngine, ExecutionMode as PolicyExecutionMode

logger = logging.getLogger("jarvis.test.phase22")


class DummyToolExecutor:
    def __init__(self, responses=None):
        self._responses = responses or {}
        self.calls = []

    async def execute(self, tool_name, confirmed=False, **kwargs):
        self.calls.append((tool_name, kwargs))
        if tool_name in self._responses:
            return self._responses[tool_name]
        return {"success": True, "result": f"executed {tool_name}"}


@pytest.fixture
def policy_engine():
    return AutomationPolicyEngine(
        execution_mode=PolicyExecutionMode.ASSISTED,
        enabled_scopes={s: True for s in ["files", "terminal", "browser", "applications", "system", "coding", "documents", "network", "communication", "vision", "automation"]},
        profile="development",
    )


@pytest.fixture
def execution_engine(policy_engine):
    return AutonomousExecutionEngine(
        tool_execute=lambda name, confirmed=False, **kwargs: DummyToolExecutor().execute(name, confirmed=confirmed, **kwargs),
        policy_engine=policy_engine,
    )


def test_policy_engine_full_auto_allows_enabled_scope(policy_engine):
    policy_engine.set_execution_mode("full_auto")
    policy_engine.set_scope("files", True)
    action, message = policy_engine.evaluate_tool("read_file", confirmed=False)
    assert action.value == "allow"


def test_policy_engine_full_auto_denies_disabled_scope(policy_engine):
    policy_engine.set_execution_mode("full_auto")
    policy_engine.set_scope("terminal", False)
    action, message = policy_engine.evaluate_tool("terminal", confirmed=False)
    assert action.value == "ask"


def test_policy_engine_assisted_asks_for_medium_risk(policy_engine):
    policy_engine.set_execution_mode("assisted")
    action, message = policy_engine.evaluate_tool("write_file", confirmed=False)
    assert action.value == "ask"


def test_policy_engine_safe_always_asks(policy_engine):
    policy_engine.set_execution_mode("safe")
    action, message = policy_engine.evaluate_tool("read_file", confirmed=False)
    assert action.value == "ask"


def test_policy_engine_immutable_deny(policy_engine):
    action, message = policy_engine.evaluate_tool("format_disk", confirmed=False)
    assert action.value == "deny"


def test_policy_engine_profile_switch(policy_engine):
    policy_engine.set_profile("safe")
    assert policy_engine.profile == "safe"
    assert not policy_engine.is_scope_enabled("terminal")


def test_policy_engine_profile_full_auto_enables_all(policy_engine):
    policy_engine.set_profile("full_auto")
    for scope in ["files", "terminal", "browser", "coding"]:
        assert policy_engine.is_scope_enabled(scope)


@pytest.mark.asyncio
async def test_execution_engine_fast_path(execution_engine):
    ctx = ExecutionContext(task_id="t1", user_request="read /etc/hostname")
    results = []
    async for result in execution_engine.execute_command(ctx.user_request, ctx):
        results.append(result)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_execution_engine_cancel(execution_engine):
    ctx = ExecutionContext(task_id="t2", user_request="open browser")
    results = []
    async for result in execution_engine.execute_command(ctx.user_request, ctx):
        results.append(result)
        if len(results) >= 1:
            execution_engine.cancel_task(ctx.task_id)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_execution_engine_smart_retry(execution_engine):
    call_count = 0

    async def flaky_tool(name, confirmed=False, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("transient failure")
        return {"success": True}

    engine = AutonomousExecutionEngine(
        tool_execute=flaky_tool,
        policy_engine=execution_engine._policy,
    )

    ctx = ExecutionContext(task_id="t3", user_request="test")
    results = []
    async for result in engine._execute_with_policy("read_file", {}, ctx, max_retries=3):
        results.append(result)
    success_results = [r for r in results if r.outcome.value == "success"]
    assert len(success_results) >= 1


@pytest.mark.asyncio
async def test_execution_engine_verification(execution_engine):
    ctx = ExecutionContext(task_id="t4", user_request="test")
    verified = await execution_engine.verify_result(type("Step", (), {"verify": None, "arguments": {}})(), {"success": True})
    assert verified is True


def test_policy_engine_default_scopes():
    engine = AutomationPolicyEngine(execution_mode="assisted")
    for scope in ["files", "terminal", "browser", "coding"]:
        assert not engine.is_scope_enabled(scope)


def test_policy_engine_development_profile_enables_coding():
    engine = AutomationPolicyEngine(execution_mode="assisted")
    engine.set_profile("development")
    assert engine.is_scope_enabled("coding")
    assert engine.is_scope_enabled("terminal")
    assert not engine.is_scope_enabled("system")


def test_execution_context_defaults():
    ctx = ExecutionContext(task_id="x1", user_request="hello")
    assert ctx.execution_path == ExecutionPath.FAST
    assert ctx.dry_run is False


def test_automation_policy_engine_global():
    from automation.policy_engine import get_automation_policy_engine, reset_automation_policy_engine
    engine1 = get_automation_policy_engine(execution_mode="assisted")
    engine2 = get_automation_policy_engine()
    assert engine1 is engine2
    reset_automation_policy_engine()


def test_execution_engine_global():
    from automation.execution_engine import get_execution_engine
    import automation.execution_engine as ee_module
    ee_module._execution_engine = None
    engine1 = get_execution_engine(tool_execute=lambda name, confirmed=False, **kwargs: {"success": True})
    engine2 = get_execution_engine(tool_execute=lambda name, confirmed=False, **kwargs: {"success": True})
    assert engine1 is engine2
    ee_module._execution_engine = None
    reset_automation_policy_engine()


def test_execution_engine_global():
    from automation.execution_engine import get_execution_engine, _execution_engine
    _execution_engine = None
    engine1 = get_execution_engine(tool_execute=lambda name, confirmed=False, **kwargs: {"success": True})
    engine2 = get_execution_engine(tool_execute=lambda name, confirmed=False, **kwargs: {"success": True})
    assert engine1 is engine2

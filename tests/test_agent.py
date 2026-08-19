"""Tests for the Phase 2 Agent system."""

from __future__ import annotations

import asyncio

import pytest

from agent.classifier import CommandCategory, command_classifier
from agent.manager import get_agent_manager
from agent.models import (
    AgentArtifacts,
    AgentContext,
    AgentPlan,
    AgentState,
    AgentTask,
    AutonomyLevel,
    ConfidenceLevel,
    TaskStatus,
    TaskType,
)
from agent.planner import AgentPlanner
from agent.state import get_state_manager
from agent.verifier import verification_engine
from agent.validator import AgentValidationError, validate_plan


def test_agent_task_creation():
    task = AgentTask(task_id="1", title="Read file", type=TaskType.FILESYSTEM_READ)
    assert task.status == TaskStatus.PENDING
    assert task.to_dict()["task_id"] == "1"


def test_agent_plan_creation():
    plan = AgentPlan(plan_id="p1", title="Test plan", description="Do things")
    assert plan.approved is False
    assert plan.to_dict()["plan_id"] == "p1"


def test_agent_context_creation():
    ctx = AgentContext(user_request="fix bug", project="myapp")
    assert ctx.project == "myapp"
    assert ctx.to_dict()["project"] == "myapp"


def test_planner_creates_plan():
    planner = AgentPlanner()
    ctx = AgentContext(user_request="run tests in my project")
    plan = planner.create_plan(ctx)
    assert len(plan.tasks) >= 1
    types = [t.type for t in plan.tasks]
    assert TaskType.TEST in types


def test_planner_creates_git_plan():
    planner = AgentPlanner()
    ctx = AgentContext(user_request="git status and commit changes")
    plan = planner.create_plan(ctx)
    types = [t.type for t in plan.tasks]
    assert TaskType.GIT in types


def test_validate_plan_accepts_valid():
    validate_plan({
        "plan_id": "p1",
        "title": "Test",
        "description": "Desc",
        "tasks": [{"title": "Do thing", "type": "terminal"}],
    })


def test_validate_plan_rejects_missing_tasks():
    with pytest.raises(AgentValidationError):
        validate_plan({"plan_id": "p1", "title": "Test"})


def test_validate_plan_rejects_non_list_tasks():
    with pytest.raises(AgentValidationError):
        validate_plan({"plan_id": "p1", "title": "Test", "tasks": "not a list"})


def test_state_manager_create_and_get():
    from agent.context import AgentContextBuilder
    builder = AgentContextBuilder()
    ctx = builder.build("test request", persona="jarvis")
    async def go():
        mgr = get_state_manager()
        session = await mgr.create_session(ctx)
        assert session.session_id is not None
        loaded = await mgr.get_session(session.session_id)
        assert loaded is not None
        assert loaded.context.user_request == "test request"
    asyncio.run(go())


def test_state_manager_cancel():
    from agent.context import AgentContextBuilder
    builder = AgentContextBuilder()
    ctx = builder.build("test request", persona="jarvis")
    async def go():
        mgr = get_state_manager()
        session = await mgr.create_session(ctx)
        ok = await mgr.cancel(session.session_id)
        assert ok is True
        loaded = await mgr.get_session(session.session_id)
        assert loaded.state == AgentState.CANCELLED
    asyncio.run(go())


# Phase 15 tests


class TestCommandClassifier:
    def test_read_classification(self):
        cat = command_classifier.classify("read the README file")
        assert cat == CommandCategory.READ

    def test_create_classification(self):
        cat = command_classifier.classify("create a new file")
        assert cat == CommandCategory.CREATE

    def test_modify_classification(self):
        cat = command_classifier.classify("modify the config")
        assert cat == CommandCategory.MODIFY

    def test_delete_classification(self):
        cat = command_classifier.classify("delete old logs")
        assert cat == CommandCategory.DELETE

    def test_communicate_classification(self):
        cat = command_classifier.classify("send message to team")
        assert cat == CommandCategory.COMMUNICATE

    def test_transaction_classification(self):
        cat = command_classifier.classify("purchase a license")
        assert cat == CommandCategory.TRANSACTION

    def test_security_classification(self):
        cat = command_classifier.classify("rotate the api key")
        assert cat == CommandCategory.SECURITY

    def test_system_classification(self):
        cat = command_classifier.classify("install the package")
        assert cat == CommandCategory.SYSTEM

    def test_requires_approval_manual(self):
        assert command_classifier.requires_approval(CommandCategory.READ, "manual") is True
        assert command_classifier.requires_approval(CommandCategory.DELETE, "manual") is True

    def test_requires_approval_autonomous(self):
        assert command_classifier.requires_approval(CommandCategory.READ, "autonomous") is False
        assert command_classifier.requires_approval(CommandCategory.DELETE, "autonomous") is True


class TestVerificationEngine:
    def test_verify_success(self):
        ok, conf, msg = verification_engine.verify("terminal", {"success": True})
        assert ok is True
        assert conf == ConfidenceLevel.HIGH

    def test_verify_failure(self):
        ok, conf, msg = verification_engine.verify("terminal", {"success": False, "error": "boom"})
        assert ok is False
        assert conf == ConfidenceLevel.HIGH

    def test_verify_missing_content(self):
        ok, conf, msg = verification_engine.verify("web_search", {"success": True})
        assert ok is False
        assert conf == ConfidenceLevel.MEDIUM

    def test_verify_observation_low_confidence(self):
        ok, conf, msg = verification_engine.verify("terminal", {"success": True}, observation="error: timeout")
        assert ok is True
        assert conf == ConfidenceLevel.LOW


class TestAgentStateMachine:
    def test_states_exist(self):
        assert AgentState.IDLE.value == "idle"
        assert AgentState.PLANNING.value == "planning"
        assert AgentState.WAITING_FOR_PERMISSION.value == "waiting_for_permission"
        assert AgentState.EXECUTING.value == "executing"
        assert AgentState.OBSERVING.value == "observing"
        assert AgentState.VERIFYING.value == "verifying"
        assert AgentState.RECOVERING.value == "recovering"
        assert AgentState.PAUSED.value == "paused"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"
        assert AgentState.CANCELLED.value == "cancelled"

    def test_state_manager_pause_resume(self):
        from agent.context import AgentContextBuilder
        builder = AgentContextBuilder()
        ctx = builder.build("test", persona="jarvis")
        async def go():
            mgr = get_state_manager()
            session = await mgr.create_session(ctx)
            ok = await mgr.pause(session.session_id)
            assert ok is True
            loaded = await mgr.get_session(session.session_id)
            assert loaded.state == AgentState.PAUSED
            ok = await mgr.resume(session.session_id)
            assert ok is True
            loaded = await mgr.get_session(session.session_id)
            assert loaded.state == AgentState.EXECUTING
        asyncio.run(go())

    def test_state_manager_kill_switch(self):
        from agent.context import AgentContextBuilder
        builder = AgentContextBuilder()
        ctx = builder.build("test", persona="jarvis")
        async def go():
            mgr = get_state_manager()
            session = await mgr.create_session(ctx)
            ok = await mgr.activate_kill_switch(session.session_id)
            assert ok is True
            loaded = await mgr.get_session(session.session_id)
            assert loaded.kill_switch is True
            assert loaded.state == AgentState.CANCELLED
        asyncio.run(go())


class TestAgentPlannerPhase15:
    def test_planner_autonomy_level(self):
        planner = AgentPlanner()
        ctx = AgentContext(user_request="fix frontend", autonomy_level=AutonomyLevel.AUTONOMOUS)
        plan = planner.create_plan(ctx)
        assert plan.autonomy_level == AutonomyLevel.AUTONOMOUS

    def test_planner_dry_run(self):
        planner = AgentPlanner()
        ctx = AgentContext(user_request="inspect project", metadata={"dry_run": True})
        plan = planner.create_plan(ctx)
        assert plan.dry_run is True

    def test_planner_browser_task(self):
        planner = AgentPlanner()
        ctx = AgentContext(user_request="open chrome and search for linux kernel news")
        plan = planner.create_plan(ctx)
        types = [t.type for t in plan.tasks]
        assert TaskType.BROWSER_NAVIGATE in types

    def test_planner_vision_task(self):
        planner = AgentPlanner()
        ctx = AgentContext(user_request="take a screenshot and analyze it")
        plan = planner.create_plan(ctx)
        types = [t.type for t in plan.tasks]
        assert TaskType.VISION_CAPTURE in types

    def test_planner_computer_task(self):
        planner = AgentPlanner()
        ctx = AgentContext(user_request="click on the login button and type password")
        plan = planner.create_plan(ctx)
        types = [t.type for t in plan.tasks]
        assert TaskType.COMPUTER_MOUSE in types

    def test_planner_command_category_assigned(self):
        planner = AgentPlanner()
        ctx = AgentContext(user_request="run tests")
        plan = planner.create_plan(ctx)
        for task in plan.tasks:
            assert task.command_category is not None


class TestAgentModels:
    def test_agent_task_phase15_fields(self):
        task = AgentTask(
            task_id="t1",
            title="Test",
            type=TaskType.TERMINAL,
            command_category=CommandCategory.SYSTEM,
            confidence=ConfidenceLevel.MEDIUM,
            observation="some output",
            verification="verified",
            requires_approval=True,
            dry_run=False,
        )
        assert task.command_category == CommandCategory.SYSTEM
        assert task.confidence == ConfidenceLevel.MEDIUM
        assert task.requires_approval is True
        d = task.to_dict()
        assert d["command_category"] == "system"
        assert d["confidence"] == "medium"

    def test_agent_artifacts_timeline(self):
        art = AgentArtifacts(task_id="a1")
        art.timeline.append({"ts": "2024-01-01", "content": "event"})
        d = art.to_dict()
        assert len(d["timeline"]) == 1

    def test_agent_context_autonomy(self):
        ctx = AgentContext(user_request="test", autonomy_level=AutonomyLevel.MANUAL)
        assert ctx.autonomy_level == AutonomyLevel.MANUAL
        assert ctx.to_dict()["autonomy_level"] == "manual"


class TestAgentManager:
    def test_manager_pause_resume_kill(self):
        async def go():
            manager = get_agent_manager(tool_execute=None)
            _ctx = AgentContext(user_request="do something")
            events = []
            async for ev in manager.start_agent("do something", autonomy_level="assisted"):
                events.append(ev)
            session_id = events[0]["data"]["session_id"]
            status = await manager.get_status(session_id)
            assert status is not None
            pause_res = await manager.pause(session_id)
            assert pause_res["status"] == "paused"
            resume_res = await manager.resume(session_id)
            assert resume_res["status"] == "resumed"
            kill_res = await manager.kill_switch(session_id)
            assert kill_res["status"] == "killed"
        asyncio.run(go())

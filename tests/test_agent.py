"""Tests for the Phase 2 Agent system."""

from __future__ import annotations

import pytest

from agent.models import AgentContext, AgentPlan, AgentState, AgentTask, TaskStatus, TaskType
from agent.planner import AgentPlanner
from agent.state import get_state_manager
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
    import asyncio
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
    import asyncio
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

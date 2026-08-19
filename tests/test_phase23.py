"""Phase 23 tests: Autonomous Intelligence + Multi-Agent Orchestration 2.0."""

from __future__ import annotations

import logging

import pytest

from agent.goal_engine import GoalEngine, get_goal_engine
from agent.task_graph import TaskGraph, GraphNode
from agent.registry_v2 import agent_registry_v2
from agent.orchestrator_v2 import get_autonomous_orchestrator
from agent.recovery_engine import RecoveryEngine, ErrorClass
from agent.verification_engine_v2 import VerificationEngine
from agent.artifact_manager import ArtifactManager
from agent.checkpoint_manager import CheckpointManager
from agent.resource_manager import ResourceManager
from agent.working_memory import WorkingMemory

logger = logging.getLogger("jarvis.test.phase23")


class DummyToolExecutor:
    def __init__(self, responses=None):
        self._responses = responses or {}
        self.calls = []

    async def execute(self, agent_name, arguments):
        self.calls.append((agent_name, arguments))
        if agent_name in self._responses:
            return self._responses[agent_name]
        return {"success": True, "output": f"executed by {agent_name}"}


@pytest.fixture(autouse=True)
def reset_globals():
    get_goal_engine.cache_clear() if hasattr(get_goal_engine, 'cache_clear') else None
    yield


def test_goal_engine_analyze_build_request():
    engine = GoalEngine()
    goal = engine.analyze("Build me a complete online store")
    assert goal.goal_id is not None
    assert len(goal.tasks) > 0
    assert any("frontend" in t.title.lower() for t in goal.tasks)
    assert any("backend" in t.title.lower() for t in goal.tasks)


def test_goal_engine_analyze_research_request():
    engine = GoalEngine()
    goal = engine.analyze("Research AI APIs and compare them")
    assert len(goal.tasks) >= 2
    assert any("research" in t.title.lower() for t in goal.tasks)


def test_goal_engine_analyze_fix_request():
    engine = GoalEngine()
    goal = engine.analyze("Fix the bug in my backend")
    assert any("fix" in t.title.lower() or "error" in t.title.lower() for t in goal.tasks)


def test_task_graph_topological_sort():
    graph = TaskGraph()
    graph.add_node(GraphNode(task_id="a", data={}))
    graph.add_node(GraphNode(task_id="b", data={}))
    graph.add_node(GraphNode(task_id="c", data={}))
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")
    order = graph.topological_sort()
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_task_graph_parallel_groups():
    graph = TaskGraph()
    graph.add_node(GraphNode(task_id="a", data={}))
    graph.add_node(GraphNode(task_id="b", data={}))
    graph.add_node(GraphNode(task_id="c", data={}))
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    groups = graph.get_parallel_groups()
    assert len(groups) == 2
    assert "a" in groups[0]
    assert "b" in groups[1]
    assert "c" in groups[1]


def test_task_graph_cycle_detection():
    graph = TaskGraph()
    graph.add_node(GraphNode(task_id="a", data={}))
    graph.add_node(GraphNode(task_id="b", data={}))
    graph.add_edge("a", "b")
    graph.add_edge("b", "a")
    with pytest.raises(ValueError):
        graph.topological_sort()


def test_task_graph_critical_path():
    graph = TaskGraph()
    graph.add_node(GraphNode(task_id="a", data={}))
    graph.add_node(GraphNode(task_id="b", data={}))
    graph.add_node(GraphNode(task_id="c", data={}))
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    critical = graph.get_critical_path()
    assert "a" in critical


def test_agent_registry_v2_builtins():
    assert agent_registry_v2.get("general") is not None
    assert agent_registry_v2.get("coding") is not None
    assert agent_registry_v2.get("research") is not None
    assert len(agent_registry_v2.list_agents()) >= 10


def test_agent_registry_v2_find_by_capability():
    agents = agent_registry_v2.find_by_capability("coding")
    assert len(agents) >= 1
    assert any(a.agent_id == "coding" for a in agents)


def test_agent_registry_v2_select_best():
    agent = agent_registry_v2.select_best("fix the code", required_tools=["terminal", "filesystem"])
    assert agent is not None


def test_recovery_engine_classify_error():
    engine = RecoveryEngine()
    assert engine.classify_error("Connection timeout") == ErrorClass.TIMEOUT
    assert engine.classify_error("Network unreachable") == ErrorClass.NETWORK_ERROR
    assert engine.classify_error("Permission denied") == ErrorClass.AUTH_ERROR
    assert engine.classify_error("Memory OOM") == ErrorClass.RESOURCE_ERROR


@pytest.mark.asyncio
async def test_recovery_engine_retry():
    engine = RecoveryEngine()
    result = await engine.attempt_recovery("timeout", {}, max_retries=2)
    assert result.attempts >= 1


@pytest.mark.asyncio
async def test_verification_engine_code():
    engine = VerificationEngine()
    result = await engine._verify_code({"success": True}, {})
    assert result["verified"] is True


@pytest.mark.asyncio
async def test_verification_engine_file():
    engine = VerificationEngine()
    result = await engine._verify_file_exists({"success": True}, {"path": "/tmp"})
    assert result["verified"] is True


def test_artifact_manager_create_and_list():
    mgr = ArtifactManager()
    artifact = mgr.create("file", "test.txt", path="/tmp/test.txt", created_by="test", task_id="t1", goal_id="g1")
    assert artifact.artifact_id is not None
    by_goal = mgr.list_by_goal("g1")
    assert len(by_goal) == 1
    by_task = mgr.list_by_task("t1")
    assert len(by_task) == 1


def test_artifact_manager_search():
    mgr = ArtifactManager()
    mgr.create("file", "report.pdf", goal_id="g1")
    mgr.create("file", "notes.txt", goal_id="g1")
    results = mgr.search("report", goal_id="g1")
    assert len(results) == 1
    assert results[0].name == "report.pdf"


def test_checkpoint_manager():
    mgr = CheckpointManager()
    cp = mgr.create("g1", "t1", "Step 1 complete", state={"step": 1})
    assert cp.checkpoint_id is not None
    last = mgr.get_last("g1")
    assert last is not None
    assert last.label == "Step 1 complete"
    state = mgr.restore("g1")
    assert state == {"step": 1}


def test_working_memory():
    wm = WorkingMemory()
    wm.set("key", "value", goal_id="g1")
    assert wm.get("key", goal_id="g1") == "value"
    ctx = wm.get_goal_context("g1")
    assert ctx["key"] == "value"
    wm.clear_goal("g1")
    assert wm.get("key", goal_id="g1") is None


def test_resource_manager_defaults():
    rm = ResourceManager()
    resources = rm.get_resources()
    assert resources.cpu_percent >= 0
    assert rm.get_max_parallel_agents() >= 1


@pytest.mark.asyncio
async def test_autonomous_orchestrator_simple_goal():
    orchestrator = get_autonomous_orchestrator(
        tool_execute=lambda agent, args: {"success": True, "output": "done"},
    )
    result = await orchestrator.execute_goal("Open Firefox")
    assert result is not None


def test_goal_progress():
    from agent.goal_engine import Goal, GoalTask, GoalStatus, TaskPriority
    goal = Goal(goal_id="g1", user_request="test")
    goal.tasks.append(GoalTask(task_id="t1", title="Task 1", description="desc", priority=TaskPriority.NORMAL))
    goal.tasks.append(GoalTask(task_id="t2", title="Task 2", description="desc", priority=TaskPriority.NORMAL))
    assert goal.progress() == 0.0
    goal.tasks[0].status = GoalStatus.COMPLETED
    assert abs(goal.progress() - 0.5) < 0.01


def test_task_graph_validate():
    graph = TaskGraph()
    graph.add_node(GraphNode(task_id="a", data={}))
    graph.add_node(GraphNode(task_id="b", data={}))
    graph.add_edge("a", "b")
    assert graph.validate() is True

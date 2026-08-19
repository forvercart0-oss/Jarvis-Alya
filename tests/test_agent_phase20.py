"""Tests for Phase 20 Multi-Agent Intelligence System 2.0."""

from __future__ import annotations

import pytest

from agent.registry import AgentDefinition, agent_registry
from agent.context_manager import agent_context_manager
from agent.result_aggregator import result_aggregator
from agent.message import AgentMessage
from agent.orchestrator import OrchestratorState, OrchestrationTask
from agent.specialized import (
    ResearchAgent, CommunicationAgent, VerificationAgent,
)


def test_agent_registry_builtins():
    assert agent_registry.get("general") is not None
    assert agent_registry.get("research") is not None
    assert agent_registry.get("coding") is not None
    assert agent_registry.get("browser") is not None
    assert agent_registry.get("computer") is not None
    assert agent_registry.get("vision") is not None
    assert agent_registry.get("file") is not None
    assert agent_registry.get("terminal") is not None
    assert agent_registry.get("system") is not None
    assert agent_registry.get("communication") is not None
    assert agent_registry.get("memory") is not None
    assert agent_registry.get("document") is not None
    assert agent_registry.get("planning") is not None
    assert agent_registry.get("verification") is not None


def test_agent_registry_find_by_capability():
    agents = agent_registry.find_by_capability("vision")
    assert len(agents) >= 1
    assert any(a.agent_id == "vision" for a in agents)


def test_agent_registry_find_by_tool():
    agents = agent_registry.find_by_tool("browser")
    assert len(agents) >= 1


def test_agent_registry_register():
    agent_registry.register(AgentDefinition(agent_id="custom_test", name="Test", description="Test agent", capabilities=["test"]))
    assert agent_registry.get("custom_test") is not None
    agent_registry._agents.pop("custom_test", None)


def test_agent_context_manager_build():
    ctx = agent_context_manager.build_context({"task_id": "1", "description": "test"}, "general")
    assert ctx["task_id"] == "1"
    assert ctx["agent_id"] == "general"


def test_agent_context_manager_minimize():
    full = {"task_id": "1", "agent_id": "general", "description": "test", "dependencies": ["2"], "permissions": ["READ"]}
    mini = agent_context_manager.minimize_context(full)
    assert "dependencies" in mini
    assert "permissions" not in mini


def test_agent_context_manager_redact():
    ctx = {"description": "My api_key is sk-1234567890abcdefghij"}
    redacted = agent_context_manager.redact_secrets(ctx)
    assert "sk-1234567890abcdefghij" not in redacted["description"]


def test_result_aggregator_empty():
    result = result_aggregator.aggregate([])
    assert result["success"] is False


def test_result_aggregator_all_success():
    results = [{"success": True, "output": "a"}, {"success": True, "output": "b"}]
    result = result_aggregator.aggregate(results)
    assert result["success"] is True
    assert result["confidence"] == 1.0


def test_result_aggregator_partial():
    results = [{"success": True, "output": "a"}, {"success": False, "error": "fail"}]
    result = result_aggregator.aggregate(results)
    assert result["partial_success"] is True
    assert result["success_count"] == 1


def test_result_aggregator_merge():
    primary = {"success": True, "output": {"a": 1}}
    secondary = {"success": True, "output": {"b": 2}}
    merged = result_aggregator.merge(primary, secondary)
    assert merged["output"]["a"] == 1
    assert merged["output"]["b"] == 2


def test_agent_message():
    msg = AgentMessage(sender="a", receiver="b", task_id="1", type="request", content="hello")
    assert msg.sender == "a"
    d = msg.to_dict()
    assert d["type"] == "request"
    assert "timestamp" in d


def test_orchestrator_state_enum():
    assert OrchestratorState.IDLE.value == "idle"
    assert OrchestratorState.RUNNING.value == "running"


def test_orchestration_task():
    task = OrchestrationTask(task_id="1", user_request="test")
    assert task.state == OrchestratorState.IDLE
    d = task.to_dict()
    assert d["task_id"] == "1"


@pytest.mark.asyncio
async def test_research_agent():
    agent = ResearchAgent()
    res = await agent.execute({"description": "test"}, None)
    assert res["agent"] == "research"


@pytest.mark.asyncio
async def test_verification_agent():
    agent = VerificationAgent()
    res = await agent.execute({"description": "test"}, None)
    assert res["agent"] == "verification"
    assert res["success"] is True


@pytest.mark.asyncio
async def test_communication_agent_requires_approval():
    agent = CommunicationAgent()
    res = await agent.execute({"description": "send message"}, None)
    assert res.get("requires_approval") is True


def test_specialized_agent_base():
    from agent.specialized.base import BaseSpecializedAgent
    agent = BaseSpecializedAgent("test", "Test")
    assert agent.agent_id == "test"

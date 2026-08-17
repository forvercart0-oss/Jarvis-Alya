"""Agent subsystem for JARVIS 2.0 Phase 20."""

from __future__ import annotations

from agent.checkpoint import AgentCheckpoint
from agent.context import AgentContextBuilder
from agent.context_manager import AgentContextManager, agent_context_manager
from agent.executor import AgentExecutor
from agent.loop import AgentLoop
from agent.manager import AgentManager, get_agent_manager
from agent.message import AgentMessage
from agent.models import (
    AgentArtifacts,
    AgentContext,
    AgentPlan,
    AgentState,
    AgentTask,
    TaskStatus,
    TaskType,
)
from agent.observer import AgentObserver, get_observer
from agent.orchestrator import AgentOrchestrator, OrchestrationTask, OrchestratorState, get_orchestrator
from agent.permissions import AgentPermissions
from agent.planner import AgentPlanner
from agent.registry import AgentDefinition, AgentRegistry, agent_registry
from agent.result_aggregator import ResultAggregator, result_aggregator
from agent.specialized import (
    BaseSpecializedAgent,
    BrowserAgent,
    CodingAgent,
    CommunicationAgent,
    ComputerAgent,
    DocumentAgent,
    FileAgent,
    MemoryAgent,
    PlanningAgent,
    ResearchAgent,
    SystemAgent,
    TerminalAgent,
    VerificationAgent,
    VisionAgent,
)
from agent.state import AgentSession, AgentStateManager, get_state_manager
from agent.task import TaskResult, create_task
from agent.validator import AgentValidationError, validate_plan, validate_task_arguments
from agent.verifier import VerificationEngine, verification_engine

__all__ = [
    "AgentArtifacts",
    "AgentCheckpoint",
    "AgentContext",
    "AgentContextBuilder",
    "AgentContextManager",
    "AgentDefinition",
    "AgentExecutor",
    "AgentLoop",
    "AgentManager",
    "AgentMessage",
    "AgentObserver",
    "AgentOrchestrator",
    "AgentPermissions",
    "AgentPlan",
    "AgentPlanner",
    "AgentRegistry",
    "AgentSession",
    "AgentState",
    "AgentStateManager",
    "AgentTask",
    "AgentValidationError",
    "BaseSpecializedAgent",
    "BrowserAgent",
    "CodingAgent",
    "CommunicationAgent",
    "ComputerAgent",
    "DocumentAgent",
    "FileAgent",
    "MemoryAgent",
    "OrchestrationTask",
    "OrchestratorState",
    "PlanningAgent",
    "ResearchAgent",
    "ResultAggregator",
    "SystemAgent",
    "TaskResult",
    "TaskStatus",
    "TaskType",
    "TerminalAgent",
    "VerificationAgent",
    "VerificationEngine",
    "VisionAgent",
    "agent_context_manager",
    "agent_registry",
    "create_task",
    "get_agent_manager",
    "get_observer",
    "get_orchestrator",
    "get_state_manager",
    "result_aggregator",
    "validate_plan",
    "validate_task_arguments",
    "verification_engine",
]


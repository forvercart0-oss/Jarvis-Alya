"""Autonomous Orchestrator 2.0 for JARVIS Phase 23.

Transforms JARVIS from a command executor into a goal-oriented
autonomous assistant. Handles goal analysis, task decomposition,
agent selection, parallel execution, verification, and recovery.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agent.checkpoint_manager import checkpoint_manager
from agent.goal_engine import Goal, GoalEngine, GoalStatus, GoalTask, get_goal_engine
from agent.recovery_engine import recovery_engine
from agent.resource_manager import resource_manager
from agent.task_graph import GraphNode, TaskGraph
from agent.verification_engine_v2 import verification_engine_v2
from agent.working_memory import working_memory
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.agent.orchestrator_v2")


class OrchestratorStateV2(StrEnum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class AutonomousOrchestrator:
    """Goal-oriented autonomous orchestrator for Phase 23."""
    tool_execute: Any = None
    memory: Any = None
    permission_manager: Any = None
    ai_service: Any = None
    goal_engine: GoalEngine | None = None
    _state: OrchestratorStateV2 = OrchestratorStateV2.IDLE
    _goals: dict[str, Goal] = field(default_factory=dict)
    _active_goal_id: str | None = None
    _cancel_flags: dict[str, bool] = field(default_factory=dict)
    _pause_flags: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        if self.goal_engine is None:
            self.goal_engine = get_goal_engine(ai_service=self.ai_service)

    async def execute_goal(self, user_request: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a high-level user goal."""
        goal_id = str(uuid.uuid4())[:8]
        self._active_goal_id = goal_id
        self._state = OrchestratorStateV2.ANALYZING
        await ws_manager.broadcast("goal_started", {"goal_id": goal_id, "request": user_request})

        working_memory.set_goal_context(goal_id, {"user_request": user_request, "status": "analyzing"})

        goal = self.goal_engine.analyze(user_request)
        goal.metadata.update(context or {})
        self._goals[goal_id] = goal

        await ws_manager.broadcast("goal_analyzed", {"goal_id": goal_id, "goal": goal.to_dict()})

        self._state = OrchestratorStateV2.PLANNING
        goal.status = GoalStatus.PLANNING
        await ws_manager.broadcast("goal_planning", {"goal_id": goal_id, "tasks": [t.to_dict() for t in goal.tasks]})

        graph = self._build_task_graph(goal)
        await ws_manager.broadcast("task_graph_created", {"goal_id": goal_id, "graph": graph.to_dict()})

        checkpoint_manager.create(goal_id, "", "Plan complete", state=goal.to_dict())

        self._state = OrchestratorStateV2.EXECUTING
        goal.status = GoalStatus.EXECUTING
        result = await self._execute_goal(goal, graph)

        if not self._cancel_flags.get(goal_id):
            self._state = OrchestratorStateV2.VERIFYING
            goal.status = GoalStatus.VERIFYING
            verification = await self._verify_goal(goal)
            result["verification"] = verification

        if result.get("success"):
            self._state = OrchestratorStateV2.COMPLETED
            goal.status = GoalStatus.COMPLETED
            goal.final_output = result.get("output", "")
        else:
            self._state = OrchestratorStateV2.FAILED
            goal.status = GoalStatus.FAILED

        goal.completed_at = time.time()
        await ws_manager.broadcast("goal_completed", {"goal_id": goal_id, "result": result})
        working_memory.clear_goal(goal_id)
        return result

    def _build_task_graph(self, goal: Goal) -> TaskGraph:
        graph = TaskGraph()
        for task in goal.tasks:
            graph.add_node(GraphNode(task_id=task.task_id, data=task.to_dict()))
        for task in goal.tasks:
            for dep in task.dependencies:
                graph.add_edge(dep, task.task_id)
        return graph

    async def _execute_goal(self, goal: Goal, graph: TaskGraph) -> dict[str, Any]:
        results: dict[str, Any] = {}
        parallel_groups = graph.get_parallel_groups()
        max_parallel = resource_manager.get_max_parallel_agents()

        for group in parallel_groups:
            if self._cancel_flags.get(goal.goal_id):
                return {"success": False, "error": "Goal cancelled", "results": results}

            while self._pause_flags.get(goal.goal_id):
                await asyncio.sleep(0.5)

            group = group[:max_parallel]
            if len(group) == 1:
                task = next(t for t in goal.tasks if t.task_id == group[0])
                result = await self._execute_task(goal, task)
                results[task.task_id] = result
            else:
                group_tasks = [next(t for t in goal.tasks if t.task_id == tid) for tid in group]
                group_results = await asyncio.gather(
                    *[self._execute_task(goal, t) for t in group_tasks],
                    return_exceptions=True,
                )
                for task, result in zip(group_tasks, group_results):
                    if isinstance(result, Exception):
                        results[task.task_id] = {"success": False, "error": str(result)}
                    else:
                        results[task.task_id] = result

        return {"success": all(r.get("success") for r in results.values()), "results": results, "output": goal.final_output}

    async def _execute_task(self, goal: Goal, task: GoalTask) -> dict[str, Any]:
        if self._cancel_flags.get(goal.goal_id):
            return {"success": False, "error": "Cancelled"}

        task.status = GoalStatus.EXECUTING
        task.started_at = time.time()
        await ws_manager.broadcast("task_started", {"goal_id": goal.goal_id, "task_id": task.task_id, "title": task.title})

        working_memory.set(f"current_task_{task.task_id}", task.title, goal_id=goal.goal_id)

        try:
            result = await self._dispatch_task(goal, task)
            if result.get("success"):
                task.status = GoalStatus.COMPLETED
                task.result = result
            else:
                task.status = GoalStatus.FAILED
                task.error = result.get("error")
                recovery = await self._recover_task(goal, task, result)
                if recovery.get("recovered"):
                    task.status = GoalStatus.COMPLETED
                    task.result = recovery
                    result = recovery
        except Exception as exc:
            logger.error("Task %s failed: %s", task.task_id, exc)
            task.status = GoalStatus.FAILED
            task.error = str(exc)
            result = {"success": False, "error": str(exc)}

        task.finished_at = time.time()
        await ws_manager.broadcast("task_finished", {"goal_id": goal.goal_id, "task_id": task.task_id, "result": result})
        return result

    async def _dispatch_task(self, goal: Goal, task: GoalTask) -> dict[str, Any]:
        if self.tool_execute:
            try:
                result = await self.tool_execute(task.agent, task.arguments or {})
                if hasattr(result, 'to_dict'):
                    result = result.to_dict()
                return {"success": result.get("success", False), "output": result}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "output": f"Task {task.title} completed (simulated)"}

    async def _recover_task(self, goal: Goal, task: GoalTask, result: dict[str, Any]) -> dict[str, Any]:
        recovery = await recovery_engine.attempt_recovery(result.get("error", ""), task.metadata, max_retries=task.max_retries)
        if recovery.recovered:
            await ws_manager.broadcast("task_recovered", {"goal_id": goal.goal_id, "task_id": task.task_id, "recovery": recovery.__dict__})
            return {"success": True, "output": "Recovered", "recovery": recovery.__dict__}
        if task.fallback_agent:
            task.agent = task.fallback_agent
            task.retries = 0
            return await self._dispatch_task(goal, task)
        return result

    async def _verify_goal(self, goal: Goal) -> dict[str, Any]:
        results = []
        for task in goal.tasks:
            if task.status == GoalStatus.COMPLETED and task.result:
                verification = await verification_engine_v2.verify(task.agent, task.result, task.metadata)
                task.verification = verification
                results.append(verification)
        if not results:
            return {"verified": False, "reason": "No completed tasks to verify"}
        passed = sum(1 for r in results if r.get("verified"))
        return {"verified": passed == len(results), "passed": passed, "total": len(results), "details": results}

    async def pause_goal(self, goal_id: str) -> dict[str, Any]:
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = GoalStatus.PAUSED
            self._pause_flags[goal_id] = True
            checkpoint_manager.create(goal_id, "", "Paused", state=goal.to_dict())
            return {"success": True, "goal_id": goal_id}
        return {"success": False, "error": "Goal not found"}

    async def resume_goal(self, goal_id: str) -> dict[str, Any]:
        goal = self._goals.get(goal_id)
        if goal:
            self._pause_flags.pop(goal_id, False)
            goal.status = GoalStatus.EXECUTING
            return {"success": True, "goal_id": goal_id}
        return {"success": False, "error": "Goal not found"}

    async def cancel_goal(self, goal_id: str) -> dict[str, Any]:
        self._cancel_flags[goal_id] = True
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = GoalStatus.CANCELLED
        return {"success": True, "goal_id": goal_id}

    def get_goal(self, goal_id: str) -> dict[str, Any] | None:
        goal = self._goals.get(goal_id)
        return goal.to_dict() if goal else None

    def list_goals(self) -> list[dict[str, Any]]:
        return [g.to_dict() for g in self._goals.values()]


_autonomous_orchestrator: AutonomousOrchestrator | None = None


def get_autonomous_orchestrator(
    tool_execute: Any = None,
    memory: Any = None,
    permission_manager: Any = None,
    ai_service: Any = None,
) -> AutonomousOrchestrator:
    global _autonomous_orchestrator
    if _autonomous_orchestrator is None:
        _autonomous_orchestrator = AutonomousOrchestrator(
            tool_execute=tool_execute,
            memory=memory,
            permission_manager=permission_manager,
            ai_service=ai_service,
        )
    return _autonomous_orchestrator

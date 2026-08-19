"""Agent orchestrator for JARVIS Phase 20."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agent.models import AgentContext, AgentPlan, AgentTask, AutonomyLevel
from agent.context_manager import agent_context_manager
from agent.result_aggregator import result_aggregator
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.agent.orchestrator")


class OrchestratorState(StrEnum):
    IDLE = "idle"
    PLANNING = "planning"
    DISPATCHING = "dispatching"
    RUNNING = "running"
    WAITING_PERMISSION = "waiting_permission"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OrchestrationTask:
    task_id: str
    user_request: str
    state: OrchestratorState = OrchestratorState.IDLE
    plan: AgentPlan | None = None
    results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    agent_assignments: dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "user_request": self.user_request,
            "state": self.state.value,
            "plan": self.plan.to_dict() if self.plan else None,
            "results": self.results,
            "errors": self.errors,
            "agent_assignments": self.agent_assignments,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


class AgentOrchestrator:
    def __init__(self, tool_execute: Any, memory: Any | None = None, permission_manager: Any | None = None, ai_service: Any | None = None):
        self._tool_execute = tool_execute
        self._memory = memory
        self._permission_manager = permission_manager
        self._ai_service = ai_service
        self._tasks: dict[str, OrchestrationTask] = {}
        self._max_parallel = 3
        self._max_agents = 5
        self._active_count = 0


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator(tool_execute: Any | None = None, memory: Any | None = None, permission_manager: Any | None = None, ai_service: Any | None = None) -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(tool_execute=tool_execute, memory=memory, permission_manager=permission_manager, ai_service=ai_service)
    return _orchestrator

    def _create_task(self, user_request: str) -> OrchestrationTask:
        task_id = str(uuid.uuid4())[:8]
        task = OrchestrationTask(task_id=task_id, user_request=user_request)
        self._tasks[task_id] = task
        return task

    async def orchestrate(self, user_request: str, autonomy_level: str = "assisted") -> dict[str, Any]:
        task = self._create_task(user_request)
        task.state = OrchestratorState.PLANNING
        await ws_manager.broadcast("orchestrator_started", {"task_id": task.task_id, "request": user_request})

        context = AgentContext(
            user_request=user_request,
            autonomy_level=AutonomyLevel(autonomy_level),
            metadata={"orchestrator_task_id": task.task_id},
        )

        # Inject adaptive personalization context if memory is available.
        if self._memory:
            try:
                personalization = self._memory.get_personalization_context(profile="jarvis")
                if personalization:
                    context.metadata["personalization"] = personalization
            except Exception:
                pass

        plan = self._create_plan(context)
        task.plan = plan
        task.state = OrchestratorState.DISPATCHING
        await ws_manager.broadcast("orchestrator_plan_created", {"task_id": task.task_id, "plan": plan.to_dict()})

        if self._is_simple_task(plan):
            result = await self._run_simple(context, plan)
            task.state = OrchestratorState.COMPLETED
            task.completed_at = time.time()
            task.results["final"] = result
            await ws_manager.broadcast("orchestrator_completed", {"task_id": task.task_id, "result": result})
            return result

        result = await self._run_multi_agent(task, plan, context)
        task.state = OrchestratorState.COMPLETED if result.get("success") else OrchestratorState.FAILED
        task.completed_at = time.time()
        task.results["final"] = result
        await ws_manager.broadcast("orchestrator_completed", {"task_id": task.task_id, "result": result})
        return result

    def _create_plan(self, context: AgentContext) -> AgentPlan:
        from agent.planner import AgentPlanner
        planner = AgentPlanner(memory=self._memory, ai_service=self._ai_service)
        return planner.create_plan(context)

    def _is_simple_task(self, plan: AgentPlan) -> bool:
        return len(plan.tasks) <= 2 and all(t.risk == "low" for t in plan.tasks)

    async def _run_simple(self, context: AgentContext, plan: AgentPlan) -> dict[str, Any]:
        from agent.executor import AgentExecutor
        executor = AgentExecutor(
            tool_execute=self._tool_execute,
            memory=self._memory,
            permission_manager=self._permission_manager,
            ai_service=self._ai_service,
        )
        session_id = f"simple_{uuid.uuid4().hex[:8]}"
        from agent.state import get_state_manager
        session = await get_state_manager().create_session(context)
        async for event in executor.execute_plan(session.session_id, plan):
            await ws_manager.broadcast(event.get("event", "agent_step"), event.get("data", {}))
        session = await get_state_manager().get_session(session.session_id)
        return {"success": True, "session_id": session_id, "plan": plan.to_dict()}

    async def _run_multi_agent(self, task: OrchestrationTask, plan: AgentPlan, context: AgentContext) -> dict[str, Any]:
        results = []
        parallel_groups = self._group_parallel(plan.tasks)
        for group in parallel_groups:
            if task.state == OrchestratorState.CANCELLED:
                break
            if len(group) == 1:
                result = await self._run_single_agent(task, group[0], context)
                results.append(result)
            else:
                group_results = await asyncio.gather(
                    *[self._run_single_agent(task, t, context) for t in group],
                    return_exceptions=True,
                )
                for r in group_results:
                    if isinstance(r, Exception):
                        results.append({"success": False, "error": str(r)})
                    else:
                        results.append(r)
        return result_aggregator.aggregate(results)

    def _group_parallel(self, tasks: list[AgentTask]) -> list[list[AgentTask]]:
        groups: list[list[AgentTask]] = []
        current: list[AgentTask] = []
        completed_deps: set[str] = set()
        pending = list(tasks)
        while pending:
            ready = [t for t in pending if all(d in completed_deps for d in (t.arguments.get("dependencies") or []))]
            if not ready:
                if current:
                    groups.append(current)
                    for t in current:
                        completed_deps.add(t.task_id)
                    current = []
                ready = pending
            current.extend(ready)
            pending = [t for t in pending if t not in ready]
            if len(current) >= self._max_parallel:
                groups.append(current)
                for t in current:
                    completed_deps.add(t.task_id)
                current = []
        if current:
            groups.append(current)
        return groups

    async def _run_single_agent(self, task: OrchestrationTask, agent_task: AgentTask, context: AgentContext) -> dict[str, Any]:
        agent_id = self._select_agent(agent_task)
        task.agent_assignments[agent_task.task_id] = agent_id
        agent_context = agent_context_manager.build_context(agent_task.to_dict(), agent_id)
        agent_context = agent_context_manager.redact_secrets(agent_context)
        await ws_manager.broadcast("agent_started", {"task_id": task.task_id, "agent_id": agent_id, "sub_task": agent_task.to_dict()})
        try:
            result = await self._execute_agent_task(agent_id, agent_context, agent_task)
            await ws_manager.broadcast("agent_result", {"task_id": task.task_id, "agent_id": agent_id, "result": result})
            return result
        except Exception as exc:
            logger.error("Agent %s failed: %s", agent_id, exc)
            error_result = {"success": False, "error": str(exc), "agent_id": agent_id}
            await ws_manager.broadcast("agent_failed", {"task_id": task.task_id, "agent_id": agent_id, "error": str(exc)})
            return error_result

    def _select_agent(self, agent_task: AgentTask) -> str:
        task_type = agent_task.type.value if hasattr(agent_task.type, 'value') else str(agent_task.type)
        mapping = {
            "web_search": "research",
            "browser_navigate": "browser",
            "browser_click": "browser",
            "browser_type": "browser",
            "computer_mouse": "computer",
            "computer_keyboard": "computer",
            "filesystem_read": "file",
            "filesystem_write": "file",
            "filesystem_delete": "file",
            "terminal": "terminal",
            "vision_capture": "vision",
            "vision_analyze": "vision",
            "vision_find": "vision",
            "vision_ocr": "vision",
            "code_edit": "coding",
            "test": "coding",
            "build": "coding",
            "server_start": "terminal",
            "server_stop": "terminal",
            "send_message": "communication",
            "memory": "memory",
            "observe": "system",
            "plan": "planning",
            "form_submit": "browser",
            "download_file": "browser",
        }
        return mapping.get(task_type, "general")

    async def _execute_agent_task(self, agent_id: str, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        if agent_id == "general":
            return await self._run_general_agent(context, agent_task)
        if agent_id == "research":
            return await self._run_research_agent(context, agent_task)
        if agent_id == "coding":
            return await self._run_coding_agent(context, agent_task)
        if agent_id == "browser":
            return await self._run_browser_agent(context, agent_task)
        if agent_id == "computer":
            return await self._run_computer_agent(context, agent_task)
        if agent_id == "vision":
            return await self._run_vision_agent(context, agent_task)
        if agent_id == "file":
            return await self._run_file_agent(context, agent_task)
        if agent_id == "terminal":
            return await self._run_terminal_agent(context, agent_task)
        if agent_id == "system":
            return await self._run_system_agent(context, agent_task)
        if agent_id == "communication":
            return await self._run_communication_agent(context, agent_task)
        if agent_id == "memory":
            return await self._run_memory_agent(context, agent_task)
        if agent_id == "document":
            return await self._run_document_agent(context, agent_task)
        if agent_id == "planning":
            return await self._run_planning_agent(context, agent_task)
        if agent_id == "verification":
            return await self._run_verification_agent(context, agent_task)
        return {"success": False, "error": f"Unknown agent: {agent_id}"}

    async def _run_general_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        if self._ai_service:
            try:
                response = await self._ai_service.chat(context.get("description", ""), context=context)
                return {"success": True, "output": response, "agent": "general"}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "output": "General agent processed request.", "agent": "general"}

    async def _run_research_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        if self._ai_service:
            try:
                response = await self._ai_service.chat(f"Research: {context.get('description', '')}", context=context)
                return {"success": True, "output": response, "agent": "research"}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "output": "Research agent processed request.", "agent": "research"}

    async def _run_coding_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("coding_agent", context, agent_task)

    async def _run_browser_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("browser_agent", context, agent_task)

    async def _run_computer_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("computer_agent", context, agent_task)

    async def _run_vision_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("vision_agent", context, agent_task)

    async def _run_file_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("file_agent", context, agent_task)

    async def _run_terminal_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("terminal_agent", context, agent_task)

    async def _run_system_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("system_agent", context, agent_task)

    async def _run_communication_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("communication_agent", context, agent_task)

    async def _run_memory_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("memory_agent", context, agent_task)

    async def _run_document_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        return await self._dispatch_tool("document_agent", context, agent_task)

    async def _run_planning_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        if self._ai_service:
            try:
                response = await self._ai_service.chat(f"Plan: {context.get('description', '')}", context=context)
                return {"success": True, "output": response, "agent": "planning"}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "output": "Planning agent processed request.", "agent": "planning"}

    async def _run_verification_agent(self, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        from agent.verifier import verification_engine
        tool_name = context.get("arguments", {}).get("tool_name", "")
        result = context.get("arguments", {}).get("result", {})
        ok, confidence, reason = verification_engine.verify(tool_name, result)
        return {"success": ok, "output": {"verified": ok, "confidence": confidence.value, "reason": reason}, "agent": "verification"}

    async def _dispatch_tool(self, agent_name: str, context: dict[str, Any], agent_task: AgentTask) -> dict[str, Any]:
        if not self._tool_execute:
            return {"success": False, "error": "No tool executor available", "agent": agent_name}
        try:
            arguments = agent_task.arguments or {}
            if context.get("input"):
                arguments.update(context["input"])
            result = await self._tool_execute(agent_name, arguments)
            if hasattr(result, 'to_dict'):
                result = result.to_dict()
            return {"success": result.get("success", False), "output": result, "agent": agent_name}
        except Exception as exc:
            return {"success": False, "error": str(exc), "agent": agent_name}

    async def cancel(self, task_id: str) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if task:
            task.state = OrchestratorState.CANCELLED
            await ws_manager.broadcast("orchestrator_cancelled", {"task_id": task_id})
            return {"success": True, "task_id": task_id}
        return {"success": False, "error": "Task not found"}

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def list_tasks(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._tasks.values()]


agent_orchestrator = AgentOrchestrator

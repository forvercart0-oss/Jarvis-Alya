"""Agent executor for JARVIS Phase 2."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from agent.models import AgentContext, AgentPlan, AgentState, AgentTask, TaskStatus, TaskType
from agent.observer import get_observer
from agent.state import get_state_manager
from agent.validator import validate_task_arguments
from permissions.manager import PermissionManager
from safety import classify_request, get_refusal_response
from safety.checker import SafetyChecker, SafetyVerdict
from safety.classifier import SafetyCategory
from safety.confirmation import get_confirmation_manager
from safety.policy import PolicyAction, get_policy_engine
from tools.registry import ToolResult

logger = logging.getLogger("jarvis.agent.executor")


class AgentExecutor:
    def __init__(
        self,
        tool_execute: Any,
        memory: Any | None = None,
        permission_manager: PermissionManager | None = None,
    ):
        self._tool_execute = tool_execute
        self._memory = memory
        self._permission_manager = permission_manager
        self._checker = SafetyChecker()
        self._policy_engine = get_policy_engine()

    async def execute_plan(self, session_id: str, plan: AgentPlan) -> AsyncGenerator[dict[str, Any], None]:
        state_mgr = get_state_manager()
        await state_mgr.set_state(session_id, AgentState.EXECUTING)

        for idx, task in enumerate(plan.tasks):
            session = await state_mgr.get_session(session_id)
            if session and session.state == AgentState.CANCELLED:
                task.status = TaskStatus.CANCELLED
                yield {"event": "agent_cancelled", "data": {"session_id": session_id}}
                return

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            get_observer().record("task_started", {"task_id": task.task_id, "title": task.title})
            yield {"event": "agent_step_started", "data": {"task": task.to_dict(), "index": idx}}

            allowed, message = await self._check_task_allowed(task)
            if not allowed:
                task.status = TaskStatus.FAILED
                task.error = message
                get_observer().record("task_denied", {"task_id": task.task_id, "reason": message})
                yield {"event": "agent_step_completed", "data": {"task": task.to_dict(), "success": False}}
                continue

            if task.risk == "high" or self._policy_engine.check_tool_policy(task.type.value).requires_confirmation:
                confirm = get_confirmation_manager().create_request(
                    tool_name=task.type.value,
                    arguments=task.arguments,
                    risk_level=task.risk,
                )
                get_observer().record("confirmation_required", {"task_id": task.task_id, "request_id": confirm.id})
                yield {"event": "agent_confirmation_required", "data": {"request_id": confirm.id, "task": task.to_dict()}}
                confirmed = await get_confirmation_manager().wait_for_confirmation(confirm.id)
                if not confirmed:
                    task.status = TaskStatus.CANCELLED
                    task.error = "User cancelled the operation."
                    yield {"event": "agent_step_completed", "data": {"task": task.to_dict(), "success": False}}
                    continue

            try:
                task.arguments = validate_task_arguments(task.type.value, task.arguments or {})
                result = await self._dispatch(task, plan.project)
                task.result = result.output
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                task.error = result.error
                get_observer().record("task_completed", {"task_id": task.task_id, "success": result.success})
            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                get_observer().record("task_failed", {"task_id": task.task_id, "error": str(exc)})

            task.finished_at = datetime.utcnow()
            yield {"event": "agent_step_completed", "data": {"task": task.to_dict()}}

        final_state = AgentState.COMPLETED if all(t.status == TaskStatus.COMPLETED for t in plan.tasks) else AgentState.FAILED
        await state_mgr.set_state(session_id, final_state)
        yield {"event": "agent_completed", "data": {"session_id": session_id, "state": final_state.value, "plan": plan.to_dict()}}

    async def _check_task_allowed(self, task: AgentTask) -> tuple[bool, str]:
        text = task.title + " " + json.dumps(task.arguments or {})
        classification = classify_request(text)
        if classification.category == SafetyCategory.HARMFUL:
            return False, "Task blocked by safety policy."
        policy = self._policy_engine.check_tool_policy(task.type.value)
        action, message = self._policy_engine.evaluate_request(task.type.value, task.arguments or {})
        if action == PolicyAction.DENY:
            return False, message or "Task not permitted."
        return True, ""

    async def _dispatch(self, task: AgentTask, project: str | None) -> ToolResult:
        if self._tool_execute is None:
            raise RuntimeError("No tool executor configured.")

        tool_map = {
            TaskType.FILESYSTEM_READ: "read_project_file" if project else "read_file",
            TaskType.FILESYSTEM_WRITE: "write_project_file" if project else "write_file",
            TaskType.FILESYSTEM_DELETE: "delete_project_file" if project else "delete_file",
            TaskType.TERMINAL: "terminal",
            TaskType.WEB_SEARCH: "web_search",
            TaskType.GIT: "git_status",
            TaskType.TEST: "run_project_command" if project else "terminal",
            TaskType.OBSERVE: "system_info",
            TaskType.MEMORY: "recall_memories",
            TaskType.VISION_CAPTURE: "vision_capture_screen",
            TaskType.VISION_ANALYZE: "vision_analyze_screen",
            TaskType.VISION_FIND: "vision_find_target",
            TaskType.VISION_OCR: "vision_ocr",
            TaskType.COMPUTER_MOUSE: "computer_mouse_click",
            TaskType.COMPUTER_KEYBOARD: "computer_keyboard_type",
        }

        tool_name = tool_map.get(task.type, "system_info")
        args = dict(task.arguments or {})

        if project and task.type in (TaskType.FILESYSTEM_READ, TaskType.FILESYSTEM_WRITE, TaskType.FILESYSTEM_DELETE, TaskType.TEST):
            args["name"] = project

        if task.type == TaskType.GIT:
            if project:
                args["name"] = project
            args.setdefault("action", "status")

        try:
            result = await self._tool_execute(tool_name, confirmed=False, **args)
            if isinstance(result, ToolResult):
                return result
            if hasattr(result, "_data"):
                return ToolResult(success=True, result=result._data)
            return ToolResult(success=True, result=str(result))
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

"""Agent executor for JARVIS Phase 15."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from agent.models import AgentPlan, AgentState, AgentTask, AutonomyLevel, TaskStatus, TaskType
from agent.observer import get_observer
from agent.state import get_state_manager
from agent.validator import validate_task_arguments
from permissions.manager import PermissionManager
from safety import classify_request
from safety.checker import SafetyChecker
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
        ai_service: Any | None = None,
    ):
        self._tool_execute = tool_execute
        self._memory = memory
        self._permission_manager = permission_manager
        self._ai_service = ai_service
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

            if task.requires_approval and plan.autonomy_level != AutonomyLevel.AUTONOMOUS:
                confirm = get_confirmation_manager().create_request(
                    tool_name=task.type.value,
                    arguments=task.arguments,
                    risk_level=task.risk,
                )
                get_observer().record("confirmation_required", {"task_id": task.task_id, "request_id": confirm.id})
                yield {
                    "event": "agent_confirmation_required",
                    "data": {"request_id": confirm.id, "task": task.to_dict()},
                }
                await state_mgr.set_state(session_id, AgentState.WAITING_FOR_USER)
                confirmed = await get_confirmation_manager().wait_for_confirmation(confirm.id)
                await state_mgr.set_state(session_id, AgentState.EXECUTING)
                if not confirmed:
                    task.status = TaskStatus.CANCELLED
                    task.error = "User cancelled the operation."
                    yield {"event": "agent_step_completed", "data": {"task": task.to_dict(), "success": False}}
                    continue

            if plan.dry_run:
                task.status = TaskStatus.COMPLETED
                task.result = {"dry_run": True, "output": "Dry run - no side effects"}
                task.finished_at = datetime.utcnow()
                yield {"event": "agent_step_completed", "data": {"task": task.to_dict(), "success": True}}
                continue

            try:
                task.arguments = validate_task_arguments(task.type.value, task.arguments or {})
                result = await self._dispatch(task, plan.project)
                task.result = result.output if hasattr(result, "output") else str(result)
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                task.error = result.error if hasattr(result, "error") else None
                get_observer().record("task_completed", {"task_id": task.task_id, "success": result.success})

                if result.success and task.type in (TaskType.TEST, TaskType.BUILD):
                    verified = await self._self_test(task, plan.project)
                    if not verified:
                        task.status = TaskStatus.FAILED
                        task.error = "Self-test failed after execution."
            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                get_observer().record("task_failed", {"task_id": task.task_id, "error": str(exc)})

            task.finished_at = datetime.utcnow()
            yield {"event": "agent_step_completed", "data": {"task": task.to_dict()}}

        final_state = (
            AgentState.COMPLETED
            if all(t.status == TaskStatus.COMPLETED for t in plan.tasks)
            else AgentState.FAILED
        )
        await state_mgr.set_state(session_id, final_state)
        yield {
            "event": "agent_completed",
            "data": {"session_id": session_id, "state": final_state.value, "plan": plan.to_dict()},
        }

    async def _check_task_allowed(self, task: AgentTask) -> tuple[bool, str]:
        text = task.title + " " + json.dumps(task.arguments or {})
        classification = classify_request(text)
        if classification.category == SafetyCategory.HARMFUL:
            return False, "Task blocked by safety policy."
        action, message = self._policy_engine.evaluate_request(task.type.value, task.arguments or {})
        if action == PolicyAction.DENY:
            return False, message or "Task not permitted."
        return True, ""

    async def _self_test(self, task: AgentTask, project: str | None) -> bool:
        if not self._ai_service or task.type != TaskType.TEST:
            return True
        try:
            prompt = (
                "You are a verification assistant. Given a test result, determine if tests passed.\n"
                f"Task: {task.title}\n"
                f"Output: {task.result}\n"
                f"Respond with PASS or FAIL and one short reason."
            )
            messages = [{"role": "user", "content": prompt}]
            result = await self._ai_service.chat_with_tools(messages, tools_spec=[])
            content = result.get("content", "").strip().upper()
            return content.startswith("PASS")
        except Exception:
            return True

    async def _dispatch(self, task: AgentTask, project: str | None) -> ToolResult:
        if self._tool_execute is None:
            raise RuntimeError("No tool executor configured.")

        tool_map = {
            TaskType.FILESYSTEM_READ: "read_project_file" if project else "read_file",
            TaskType.FILESYSTEM_WRITE: "write_project_file" if project else "write_file",
            TaskType.FILESYSTEM_DELETE: "delete_project_file" if project else "delete_file",
            TaskType.CODE_EDIT: "write_project_file" if project else "write_file",
            TaskType.TERMINAL: "terminal",
            TaskType.WEB_SEARCH: "web_search",
            TaskType.GIT: "git_status",
            TaskType.TEST: "run_project_command" if project else "terminal",
            TaskType.BUILD: "run_project_command" if project else "terminal",
            TaskType.SERVER_START: "run_project_command" if project else "terminal",
            TaskType.SERVER_STOP: "terminal",
            TaskType.OBSERVE: "system_info",
            TaskType.MEMORY: "recall_memories",
            TaskType.VISION_CAPTURE: "vision_capture_screen",
            TaskType.VISION_ANALYZE: "vision_analyze_screen",
            TaskType.VISION_FIND: "vision_find_target",
            TaskType.VISION_OCR: "vision_ocr",
            TaskType.COMPUTER_MOUSE: "computer_mouse_click",
            TaskType.COMPUTER_KEYBOARD: "computer_keyboard_type",
            TaskType.BROWSER_NAVIGATE: "open_browser",
            TaskType.BROWSER_CLICK: "browser_click",
            TaskType.BROWSER_TYPE: "browser_type",
            TaskType.FORM_SUBMIT: "browser_click",
            TaskType.SEND_MESSAGE: "system_info",
            TaskType.DOWNLOAD_FILE: "download_file",
        }

        tool_name = tool_map.get(task.type, "system_info")
        args = dict(task.arguments or {})

        if project and task.type in (
            TaskType.FILESYSTEM_READ,
            TaskType.FILESYSTEM_WRITE,
            TaskType.FILESYSTEM_DELETE,
            TaskType.CODE_EDIT,
            TaskType.TEST,
            TaskType.BUILD,
            TaskType.SERVER_START,
        ):
            args["name"] = project

        if task.type == TaskType.GIT:
            if project:
                args["name"] = project
            args.setdefault("action", "status")

        if task.type == TaskType.TERMINAL:
            args.setdefault("timeout", 120)

        if task.type == TaskType.BUILD:
            if project:
                args["name"] = project
            args.setdefault("command", self._guess_build_command(project))

        if task.type == TaskType.TEST:
            if project:
                args["name"] = project
            args.setdefault("command", self._guess_test_command(project))

        if task.type == TaskType.SERVER_START:
            if project:
                args["name"] = project
            args.setdefault("command", self._guess_dev_command(project))

        if task.type == TaskType.COMPUTER_MOUSE:
            args.setdefault("action", "click")
            args.setdefault("x", 0)
            args.setdefault("y", 0)

        if task.type == TaskType.COMPUTER_KEYBOARD:
            args.setdefault("action", "type")
            args.setdefault("text", "")

        try:
            result = await self._tool_execute(tool_name, confirmed=False, **args)
            if isinstance(result, ToolResult):
                return result
            if hasattr(result, "_data"):
                return ToolResult(success=True, result=result._data)
            return ToolResult(success=True, result=str(result))
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def _guess_test_command(self, project_root: str | None) -> str:
        if not project_root:
            return "pytest"
        root = _coerce_path(project_root)
        if (root / "package.json").exists():
            return "npm test"
        if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
            return "pytest"
        if (root / "Cargo.toml").exists():
            return "cargo test"
        if (root / "go.mod").exists():
            return "go test ./..."
        return "pytest"

    def _guess_build_command(self, project_root: str | None) -> str:
        if not project_root:
            return "echo 'No project specified'"
        root = _coerce_path(project_root)
        if (root / "package.json").exists():
            return "npm run build"
        if (root / "pyproject.toml").exists():
            return "python -m build"
        if (root / "Cargo.toml").exists():
            return "cargo build --release"
        return "echo 'Unknown build system'"

    def _guess_dev_command(self, project_root: str | None) -> str:
        if not project_root:
            return "echo 'No project specified'"
        root = _coerce_path(project_root)
        if (root / "package.json").exists():
            return "npm run dev"
        if (root / "pyproject.toml").exists():
            return "uvicorn main:app --reload"
        return "echo 'Unknown dev server'"


def _coerce_path(value: Any) -> Any:
    from pathlib import Path
    if isinstance(value, str):
        return Path(value)
    return value

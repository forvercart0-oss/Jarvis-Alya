"""Agent planner for JARVIS Phase 15."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent.classifier import CommandCategory, command_classifier
from agent.models import AgentContext, AgentPlan, AgentTask, TaskType
from agent.validator import validate_plan

logger = logging.getLogger("jarvis.agent.planner")


class AgentPlanner:
    def __init__(self, memory=None, ai_service=None):
        self._memory = memory
        self._ai_service = ai_service

    def create_plan(self, context: AgentContext) -> AgentPlan:
        plan_id = _uid()
        title = context.user_request[:80]
        description = context.user_request
        tasks = self._decompose(context)
        plan = AgentPlan(
            plan_id=plan_id,
            title=title,
            description=description,
            tasks=tasks,
            project=context.project,
            autonomy_level=context.autonomy_level,
            dry_run=context.metadata.get("dry_run", False),
        )
        validate_plan(plan.to_dict())
        return plan

    def _decompose(self, context: AgentContext) -> list[AgentTask]:
        if self._ai_service:
            try:
                return self._ai_decompose(context)
            except Exception as exc:
                logger.warning("AI planning failed, falling back to heuristic: %s", exc)
        return self._heuristic_decompose(context)

    def _ai_decompose(self, context: AgentContext) -> list[AgentTask]:
        valid_types = (
            "filesystem_read, filesystem_write, filesystem_delete, code_edit, terminal, "
            "web_search, git, test, build, server_start, server_stop, observe, memory, "
            "vision_capture, vision_analyze, vision_find, vision_ocr, computer_mouse, "
            "computer_keyboard, browser_navigate, browser_click, browser_type, "
            "form_submit, send_message, download_file"
        )
        prompt = (
            "You are a task planner for an autonomous agent. "
            "Break the user request into a sequence of executable tasks. "
            "Return ONLY a JSON array of tasks. Each task must have: title, type, risk, arguments, command_category.\n"
            f"Valid types: {valid_types}.\n"
            "Risk levels: low, medium, high.\n"
            "Command categories: read, analyze, create, modify, delete, communicate, transaction, system, security.\n"
            f"User request: {context.user_request}\n"
            f"Project: {context.project or 'none'}\n"
            f"Project root: {context.project_root or 'none'}\n"
            f"Autonomy level: {context.autonomy_level.value}\n"
        )
        messages = [{"role": "user", "content": prompt}]
        result = self._ai_service.chat_with_tools(messages, tools_spec=[])
        content = result.get("content", "")
        try:
            data = json.loads(content)
            tasks = []
            for item in data:
                task_type = TaskType(item.get("type", "observe"))
                cat = CommandCategory(item.get("command_category", "read"))
                tasks.append(AgentTask(
                    task_id=_uid(),
                    title=item.get("title", "Untitled task"),
                    type=task_type,
                    risk=item.get("risk", "low"),
                    command_category=cat,
                    arguments=item.get("arguments", {}),
                    requires_approval=command_classifier.requires_approval(cat, context.autonomy_level.value),
                ))
            if tasks:
                return tasks
        except Exception as exc:
            logger.warning("AI planning JSON parse failed: %s", exc)
        return self._heuristic_decompose(context)

    def _heuristic_decompose(self, context: AgentContext) -> list[AgentTask]:
        text = context.user_request.lower()
        autonomy = context.autonomy_level.value
        tasks: list[AgentTask] = []

        if any(k in text for k in ["open firefox", "open chrome", "browse", "search web", "google"]):
            tasks.append(self._make_task(
                "Open browser and navigate", TaskType.BROWSER_NAVIGATE, "medium",
                {"url": self._guess_url(text)}, autonomy,
            ))

        if any(k in text for k in ["test", "run tests", "pytest", "npm test"]):
            tasks.append(self._make_task(
                "Run project tests", TaskType.TEST, "low",
                {"command": self._guess_test_command(context.project_root)}, autonomy,
            ))

        if any(k in text for k in ["git status", "status", "changes"]):
            tasks.append(self._make_task("Inspect git status", TaskType.GIT, "low", {"action": "status"}, autonomy))

        if any(k in text for k in ["commit", "save changes"]):
            tasks.append(self._make_task("Prepare commit", TaskType.GIT, "medium", {"action": "diff"}, autonomy))

        if any(k in text for k in ["inspect", "read", "show", "list", "check", "analyze"]):
            tasks.append(self._make_task(
                "Inspect project structure", TaskType.FILESYSTEM_READ, "low",
                {"path": context.project_root or "."}, autonomy,
            ))

        if any(k in text for k in ["create", "add", "build", "make", "write", "generate"]):
            tasks.append(self._make_task(
                "Create requested files", TaskType.FILESYSTEM_WRITE, "medium",
                {"path": context.project_root or "."}, autonomy,
            ))

        if any(k in text for k in ["fix", "debug", "repair", "error", "bug"]):
            tasks.extend([
                self._make_task(
                    "Inspect and analyze code", TaskType.FILESYSTEM_READ, "low",
                    {"path": context.project_root or "."}, autonomy,
                ),
                self._make_task(
                    "Run tests to verify fix", TaskType.TEST, "low",
                    {"command": self._guess_test_command(context.project_root)}, autonomy,
                ),
            ])

        if any(k in text for k in ["screenshot", "capture", "what is on screen", "what am i looking at"]):
            tasks.append(self._make_task(
                "Capture and analyze screen", TaskType.VISION_CAPTURE, "low",
                {"mode": "full"}, autonomy,
            ))

        if any(k in text for k in ["click", "type", "press", "scroll", "mouse", "keyboard"]):
            tasks.append(self._make_task(
                "Perform computer action", TaskType.COMPUTER_MOUSE, "medium",
                {"action": "click", "x": 0, "y": 0}, autonomy,
            ))

        if not tasks:
            tasks.append(self._make_task(
                "Process user request", TaskType.OBSERVE, "low",
                {"target": context.user_request}, autonomy,
            ))

        return tasks

    def _make_task(
        self, title: str, task_type: TaskType, risk: str,
        arguments: dict[str, Any], autonomy: str,
    ) -> AgentTask:
        cat = self._classify_task(task_type, arguments)
        return AgentTask(
            task_id=_uid(),
            title=title,
            type=task_type,
            risk=risk,
            command_category=cat,
            arguments=arguments,
            requires_approval=command_classifier.requires_approval(cat, autonomy),
        )

    def _classify_task(self, task_type: TaskType, arguments: dict[str, Any]) -> CommandCategory:
        mapping = {
            TaskType.FILESYSTEM_READ: CommandCategory.READ,
            TaskType.FILESYSTEM_WRITE: CommandCategory.CREATE,
            TaskType.FILESYSTEM_DELETE: CommandCategory.DELETE,
            TaskType.CODE_EDIT: CommandCategory.MODIFY,
            TaskType.TERMINAL: CommandCategory.SYSTEM,
            TaskType.WEB_SEARCH: CommandCategory.READ,
            TaskType.GIT: CommandCategory.MODIFY,
            TaskType.TEST: CommandCategory.READ,
            TaskType.BUILD: CommandCategory.SYSTEM,
            TaskType.SERVER_START: CommandCategory.SYSTEM,
            TaskType.SERVER_STOP: CommandCategory.SYSTEM,
            TaskType.PLAN: CommandCategory.ANALYZE,
            TaskType.OBSERVE: CommandCategory.ANALYZE,
            TaskType.MEMORY: CommandCategory.READ,
            TaskType.VISION_CAPTURE: CommandCategory.READ,
            TaskType.VISION_ANALYZE: CommandCategory.ANALYZE,
            TaskType.VISION_FIND: CommandCategory.ANALYZE,
            TaskType.VISION_OCR: CommandCategory.READ,
            TaskType.COMPUTER_MOUSE: CommandCategory.SYSTEM,
            TaskType.COMPUTER_KEYBOARD: CommandCategory.SYSTEM,
            TaskType.BROWSER_NAVIGATE: CommandCategory.READ,
            TaskType.BROWSER_CLICK: CommandCategory.SYSTEM,
            TaskType.BROWSER_TYPE: CommandCategory.SYSTEM,
            TaskType.FORM_SUBMIT: CommandCategory.COMMUNICATE,
            TaskType.SEND_MESSAGE: CommandCategory.COMMUNICATE,
            TaskType.DOWNLOAD_FILE: CommandCategory.CREATE,
        }
        return mapping.get(task_type, CommandCategory.READ)

    def _guess_url(self, text: str) -> str:
        import re
        match = re.search(r"https?://\S+", text)
        if match:
            return match.group(0)
        if "github" in text:
            return "https://github.com"
        if "linux" in text:
            return "https://news.ycombinator.com"
        return "https://www.google.com"

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

    def _guess_url(self, text: str) -> str:
        import re
        match = re.search(r"https?://\S+", text)
        if match:
            return match.group(0)
        if "github" in text:
            return "https://github.com"
        if "linux" in text:
            return "https://news.ycombinator.com"
        return "https://www.google.com"


def _uid() -> str:
    import uuid
    return str(uuid.uuid4())[:8]


def _coerce_path(value: Any) -> Any:
    from pathlib import Path
    if isinstance(value, str):
        return Path(value)
    return value

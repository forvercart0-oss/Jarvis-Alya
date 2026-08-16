"""Agent planner for JARVIS Phase 2."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agent.models import AgentContext, AgentPlan, AgentTask, TaskStatus, TaskType
from agent.validator import validate_plan
from tools.registry import build_registry

logger = logging.getLogger("jarvis.agent.planner")


class AgentPlanner:
    def __init__(self, memory=None):
        self._memory = memory

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
        )
        validate_plan(plan.to_dict())
        return plan

    def _decompose(self, context: AgentContext) -> list[AgentTask]:
        text = context.user_request.lower()
        tasks: list[AgentTask] = []

        if any(k in text for k in ["test", "run tests", "pytest", "npm test"]):
            tasks.append(AgentTask(
                task_id=_uid(), title="Run project tests", type=TaskType.TEST,
                arguments={"command": self._guess_test_command(context.project_root)}, risk="low",
            ))

        if any(k in text for k in ["git status", "status", "changes"]):
            tasks.append(AgentTask(
                task_id=_uid(), title="Inspect git status", type=TaskType.GIT,
                arguments={"action": "status"}, risk="low",
            ))

        if any(k in text for k in ["commit", "save changes"]):
            tasks.append(AgentTask(
                task_id=_uid(), title="Prepare commit", type=TaskType.GIT,
                arguments={"action": "diff"}, risk="medium",
            ))

        if any(k in text for k in ["inspect", "read", "show", "list", "check"]):
            tasks.append(AgentTask(
                task_id=_uid(), title="Inspect project structure", type=TaskType.FILESYSTEM_READ,
                arguments={"path": "."}, risk="low",
            ))

        if any(k in text for k in ["create", "add", "build", "make", "write"]):
            tasks.append(AgentTask(
                task_id=_uid(), title="Create requested files", type=TaskType.FILESYSTEM_WRITE,
                arguments={"path": "."}, risk="medium",
            ))

        if any(k in text for k in ["fix", "debug", "repair", "error", "bug"]):
            tasks.append(AgentTask(
                task_id=_uid(), title="Inspect and analyze code", type=TaskType.FILESYSTEM_READ,
                arguments={"path": "."}, risk="low",
            ))

        if not tasks:
            tasks.append(AgentTask(
                task_id=_uid(), title="Process user request", type=TaskType.OBSERVE,
                arguments={"target": context.user_request}, risk="low",
            ))

        return tasks

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


def _uid() -> str:
    import uuid
    return str(uuid.uuid4())[:8]


def _coerce_path(value: Any) -> Any:
    from pathlib import Path
    if isinstance(value, str):
        return Path(value)
    return value

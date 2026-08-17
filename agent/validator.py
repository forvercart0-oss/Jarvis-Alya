"""Agent validator for JARVIS Phase 2."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.agent.validator")


class AgentValidationError(Exception):
    pass


def validate_plan(plan: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise AgentValidationError("Plan must be a JSON object.")
    if "tasks" not in plan or not isinstance(plan["tasks"], list):
        raise AgentValidationError("Plan must contain a 'tasks' array.")
    for task in plan["tasks"]:
        if not isinstance(task, dict):
            raise AgentValidationError("Each task must be an object.")
        if "title" not in task or not str(task["title"]).strip():
            raise AgentValidationError("Each task must have a non-empty 'title'.")
        if "type" not in task:
            raise AgentValidationError("Each task must have a 'type'.")


def validate_task_arguments(task_type: str, arguments: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "filesystem_read": {"path"},
        "filesystem_write": {"path", "content"},
        "filesystem_delete": {"path"},
        "terminal": {"command", "cwd"},
        "web_search": {"query"},
        "git_status": {"path"},
        "git_diff": {"path"},
        "git_log": {"path"},
        "test": {"command", "cwd"},
        "observe": {"target"},
        "memory": {"action", "key", "value"},
    }
    permitted = allowed.get(task_type, set())
    cleaned = {k: v for k, v in arguments.items() if k in permitted}
    return cleaned

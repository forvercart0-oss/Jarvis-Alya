"""Task planner for JARVIS Phase 27."""

from __future__ import annotations

import logging
from typing import Any

from coding.models import CodingTask

logger = logging.getLogger("jarvis.coding.task_planner")


class CodingTaskPlanner:
    def __init__(self):
        self._tasks: dict[str, CodingTask] = {}

    def create_task(self, goal: str, project: str = "") -> CodingTask:
        task = CodingTask(goal=goal, project=project)
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> CodingTask | None:
        return self._tasks.get(task_id)

    def plan_steps(self, task: CodingTask, project_info: Any) -> list[dict[str, Any]]:
        steps = []
        goal_lower = task.goal.lower()
        if any(k in goal_lower for k in ["create", "build", "scaffold", "new"]):
            steps.extend([
                {"type": "analyze", "description": "Analyze requirements and environment"},
                {"type": "create_project", "description": "Initialize project structure"},
                {"type": "create_files", "description": "Generate source files"},
                {"type": "install_deps", "description": "Install dependencies"},
                {"type": "run_tests", "description": "Run tests"},
                {"type": "verify", "description": "Verify build and functionality"},
            ])
        elif any(k in goal_lower for k in ["fix", "debug", "error", "bug"]):
            steps.extend([
                {"type": "analyze", "description": "Analyze error or issue"},
                {"type": "locate", "description": "Locate affected code"},
                {"type": "reproduce", "description": "Reproduce the issue"},
                {"type": "fix", "description": "Apply fix"},
                {"type": "test", "description": "Run tests to verify fix"},
            ])
        elif any(k in goal_lower for k in ["refactor", "improve", "clean"]):
            steps.extend([
                {"type": "analyze", "description": "Analyze current code structure"},
                {"type": "plan", "description": "Plan refactoring changes"},
                {"type": "modify", "description": "Apply refactoring"},
                {"type": "test", "description": "Run tests to verify behavior"},
            ])
        elif any(k in goal_lower for k in ["test", "tests"]):
            steps.extend([
                {"type": "discover", "description": "Discover test framework"},
                {"type": "run_tests", "description": "Run tests"},
                {"type": "analyze", "description": "Analyze test results"},
            ])
        else:
            steps.extend([
                {"type": "analyze", "description": "Analyze request"},
                {"type": "plan", "description": "Plan implementation"},
                {"type": "implement", "description": "Implement changes"},
                {"type": "test", "description": "Run tests"},
                {"type": "verify", "description": "Verify result"},
            ])
        task.steps = steps
        return steps

    def update_status(self, task: CodingTask, status: str) -> None:
        task.status = status
        task.updated_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    def record_step_result(self, task: CodingTask, step_index: int, result: dict[str, Any]) -> None:
        if 0 <= step_index < len(task.steps):
            task.steps[step_index]["result"] = result
        task.current_step = step_index + 1


coding_task_planner = CodingTaskPlanner()

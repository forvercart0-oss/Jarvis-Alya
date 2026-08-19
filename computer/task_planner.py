"""Computer task planner for JARVIS Phase 19."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("jarvis.computer.planner")


class ComputerTaskState(StrEnum):
    IDLE = "idle"
    OBSERVING = "observing"
    PLANNING = "planning"
    WAITING_PERMISSION = "waiting_permission"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    PAUSED = "paused"
    USER_CONTROL = "user_control"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ComputerTask:
    goal: str
    state: ComputerTaskState = ComputerTaskState.IDLE
    steps: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    session_id: str = "default"
    action_count: int = 0
    retry_count: int = 0
    max_actions: int = 20
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "state": self.state.value,
            "steps": self.steps,
            "current_step": self.current_step,
            "checkpoints": self.checkpoints,
            "result": self.result,
            "error": self.error,
            "session_id": self.session_id,
            "action_count": self.action_count,
            "retry_count": self.retry_count,
            "max_actions": self.max_actions,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }


class ComputerTaskPlanner:
    def __init__(self):
        self._tasks: dict[str, ComputerTask] = {}
        self._takeover: dict[str, bool] = {}

    def create_task(self, goal: str, session_id: str = "default", max_actions: int = 20) -> ComputerTask:
        task = ComputerTask(goal=goal, session_id=session_id, max_actions=max_actions)
        self._tasks[session_id] = task
        return task

    def get_task(self, session_id: str = "default") -> ComputerTask | None:
        return self._tasks.get(session_id)

    def set_takeover(self, session_id: str, enabled: bool) -> None:
        self._takeover[session_id] = enabled

    def is_takeover(self, session_id: str) -> bool:
        return self._takeover.get(session_id, False)

    def can_act(self, task: ComputerTask) -> bool:
        if self._takeover.get(task.session_id, False):
            return False
        if task.state in (ComputerTaskState.PAUSED, ComputerTaskState.FAILED, ComputerTaskState.COMPLETED, ComputerTaskState.CANCELLED, ComputerTaskState.USER_CONTROL):
            return False
        if task.action_count >= task.max_actions:
            task.state = ComputerTaskState.FAILED
            task.error = "Maximum actions exceeded"
            return False
        return True

    def record_action(self, task: ComputerTask, action: str, result: dict[str, Any]) -> None:
        task.action_count += 1
        task.steps.append({"action": action, "result": result, "count": task.action_count})

    def add_checkpoint(self, task: ComputerTask, name: str, result: dict[str, Any]) -> None:
        task.checkpoints.append({"name": name, "result": result, "step": task.current_step})

    def should_retry(self, task: ComputerTask) -> bool:
        return task.retry_count < task.max_retries

    def increment_retry(self, task: ComputerTask) -> None:
        task.retry_count += 1

    def reset_retry(self, task: ComputerTask) -> None:
        task.retry_count = 0


computer_planner = ComputerTaskPlanner()

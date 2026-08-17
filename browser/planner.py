"""Browser action planner for JARVIS Phase 18."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("jarvis.browser.planner")


class BrowserTaskState(StrEnum):
    IDLE = "idle"
    OPENING = "opening"
    NAVIGATING = "navigating"
    INSPECTING = "inspecting"
    PLANNING = "planning"
    WAITING_PERMISSION = "waiting_permission"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class BrowserTask:
    goal: str
    state: BrowserTaskState = BrowserTaskState.IDLE
    steps: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    session_id: str = "default"
    action_count: int = 0
    retry_count: int = 0
    max_actions: int = 10
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "state": self.state.value,
            "steps": self.steps,
            "current_step": self.current_step,
            "result": self.result,
            "error": self.error,
            "session_id": self.session_id,
            "action_count": self.action_count,
            "retry_count": self.retry_count,
            "max_actions": self.max_actions,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }


class BrowserActionPlanner:
    """Plans and verifies browser actions."""

    def __init__(self):
        self._tasks: dict[str, BrowserTask] = {}
        self._takeover: dict[str, bool] = {}

    def create_task(self, goal: str, session_id: str = "default", max_actions: int = 10) -> BrowserTask:
        task = BrowserTask(goal=goal, session_id=session_id, max_actions=max_actions)
        self._tasks[session_id] = task
        return task

    def get_task(self, session_id: str = "default") -> BrowserTask | None:
        return self._tasks.get(session_id)

    def set_takeover(self, session_id: str, enabled: bool) -> None:
        self._takeover[session_id] = enabled

    def is_takeover(self, session_id: str) -> bool:
        return self._takeover.get(session_id, False)

    def can_act(self, task: BrowserTask) -> bool:
        if self._takeover.get(task.session_id, False):
            return False
        if task.state in (BrowserTaskState.PAUSED, BrowserTaskState.FAILED, BrowserTaskState.COMPLETED):
            return False
        if task.action_count >= task.max_actions:
            task.state = BrowserTaskState.FAILED
            task.error = "Maximum actions exceeded"
            return False
        return True

    def record_action(self, task: BrowserTask, action: str, result: dict[str, Any]) -> None:
        task.action_count += 1
        task.steps.append({"action": action, "result": result, "count": task.action_count})

    def should_retry(self, task: BrowserTask) -> bool:
        return task.retry_count < task.max_retries

    def increment_retry(self, task: BrowserTask) -> None:
        task.retry_count += 1

    def reset_retry(self, task: BrowserTask) -> None:
        task.retry_count = 0

    async def verify_action(self, page: Any, expected: dict[str, Any]) -> dict[str, Any]:
        try:
            actual_url = page.url if hasattr(page, 'url') else ""
            actual_title = await page.title() if hasattr(page, 'title') else ""
            success = True
            if expected.get("url") and expected["url"] not in actual_url:
                success = False
            if expected.get("title") and expected["title"] not in actual_title:
                success = False
            return {"success": success, "actual_url": actual_url, "actual_title": actual_title}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


browser_planner = BrowserActionPlanner()

"""Task recovery: retry logic and fallback strategies."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from automation.task_state import TaskState

logger = logging.getLogger("jarvis.automation.recovery")


class RecoveryStrategy:
    """Defines how to recover from a failed step."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_factor: float = 2.0,
        fallback_tools: list[str] | None = None,
    ):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.fallback_tools = fallback_tools or []

    def get_backoff(self, attempt: int) -> float:
        return self.backoff_base * (self.backoff_factor**attempt)

    async def attempt(self, func, *args, attempt: int = 0, **kwargs):
        """Attempt a function with retry logic."""
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            if attempt >= self.max_retries - 1:
                raise
            backoff = self.get_backoff(attempt)
            logger.warning(
                "Attempt %d failed for %s: %s. Retrying in %.1fs",
                attempt + 1,
                func.__name__,
                exc,
                backoff,
            )
            await asyncio.sleep(backoff)
            return await self.attempt(func, *args, attempt=attempt + 1, **kwargs)


class FallbackRouter:
    """Routes to alternative tools when primary fails."""

    FALLBACK_MAP: dict[str, list[str]] = {
        "browser_click": [
            "browser_screenshot",
            "vision_find_target",
            "computer_mouse_click",
        ],
        "browser_type": ["browser_click", "vision_keyboard_type"],
        "browser_navigate": ["open_browser"],
        "terminal": ["run_project_command"],
        "write_file": ["edit_file", "terminal"],
        "read_file": ["terminal", "browser_read"],
    }

    @classmethod
    def get_fallbacks(cls, tool_name: str) -> list[str]:
        return cls.FALLBACK_MAP.get(tool_name, [])

    @classmethod
    def has_fallback(cls, tool_name: str) -> bool:
        return len(cls.FALLBACK_MAP.get(tool_name, [])) > 0


class TaskRecovery:
    """Manages task recovery after failures."""

    def __init__(self, tool_execute: Any):
        self._tool_execute = tool_execute

    async def recover_step(self, step: dict, previous_error: str) -> tuple[bool, Any]:
        """Attempt to recover from a failed step.

        Returns (recovered, result_or_error).
        """
        tool_name = step.get("tool") or step.get("action", "")
        fallbacks = FallbackRouter.get_fallbacks(tool_name)

        for fallback_tool in fallbacks:
            try:
                result = await self._tool_execute(
                    fallback_tool, **step.get("arguments", {})
                )
                if hasattr(result, "_data") and result._data.get("success"):
                    return True, result
                if isinstance(result, dict) and result.get("success"):
                    return True, result
            except Exception as exc:
                logger.warning("Fallback %s also failed: %s", fallback_tool, exc)
                continue

        return False, previous_error

    def should_retry(self, task: dict, error: str) -> bool:
        """Determine if a task should be retried."""
        retries = task.get("retries", 0)
        max_retries = task.get("max_retries", 3)
        if retries >= max_retries:
            return False
        status = task.get("status")
        return status != TaskState.CANCELLED.value

    def increment_retry(self, task: dict) -> dict:
        """Increment retry count on a task."""
        retries = task.get("retries", 0) + 1
        task["retries"] = retries
        return task

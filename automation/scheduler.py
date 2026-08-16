"""Task scheduler: schedule recurring and one-time tasks."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from automation.task_state import TaskState

logger = logging.getLogger("jarvis.automation.scheduler")


class ScheduledTask:
    """Represents a scheduled task."""

    def __init__(self, task_id: str, cron: str, enabled: bool = True, last_run: str | None = None):
        self.task_id = task_id
        self.cron = cron
        self.enabled = enabled
        self.last_run = last_run

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "cron": self.cron,
            "enabled": self.enabled,
            "last_run": self.last_run,
        }


class TaskScheduler:
    """Schedules and triggers tasks based on time-based rules."""

    def __init__(self, task_store: Any, execute_callback: Any | None = None):
        self._store = task_store
        self._execute = execute_callback
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._tick())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _tick(self) -> None:
        while self._running:
            try:
                now = datetime.now(UTC)
                for task in self._store.get_tasks():
                    if task.get("status") != TaskState.PENDING.value:
                        continue
                    schedule = task.get("schedule")
                    if not schedule:
                        continue
                    if self._is_due(schedule, now, task.get("last_run")):
                        if self._execute:
                            self._execute(task["id"])
                        self._store.update_task(task["id"], last_run=now.isoformat())
            except Exception as exc:
                logger.warning("Scheduler tick failed: %s", exc)
            await asyncio.sleep(30)

    def _is_due(self, cron: str, now: datetime, last_run: str | None) -> bool:
        """Check if a cron-like schedule is due."""
        try:
            hour_min = cron.strip()
            if ":" in hour_min:
                parts = hour_min.split(":")
                target_hour = int(parts[0])
                target_min = int(parts[1])
                current = now.strftime("%H:%M")
                expected = f"{target_hour:02d}:{target_min:02d}"
                if current == expected and (last_run or "") != current:
                    return True
        except Exception as exc:
            logger.debug("Schedule parse failed: %s", exc)
        return False

    def schedule_task(self, task_id: str, cron: str) -> None:
        self._store.update_task(task_id, schedule=cron)

    def unschedule_task(self, task_id: str) -> None:
        self._store.update_task(task_id, schedule=None)

    def get_scheduled_tasks(self) -> list[dict[str, Any]]:
        return self._store.get_scheduled_tasks()

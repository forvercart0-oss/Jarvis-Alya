"""Task monitor: track running tasks, timeouts, and progress."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from automation.task_state import TaskState

logger = logging.getLogger("jarvis.automation.monitor")


@dataclass
class MonitorEntry:
    task_id: str
    started_at: float
    timeout: float
    last_heartbeat: float
    pid: int | None = None
    cancelled: bool = False

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at

    @property
    def remaining(self) -> float:
        return max(0.0, self.timeout - self.elapsed)


class TaskMonitor:
    """Monitors running tasks for timeouts and progress."""

    def __init__(self):
        self._entries: dict[str, MonitorEntry] = {}
        self._lock = asyncio.Lock()

    def register(self, task_id: str, timeout: float = 300.0, pid: int | None = None) -> None:
        entry = MonitorEntry(
            task_id=task_id,
            started_at=time.time(),
            timeout=timeout,
            last_heartbeat=time.time(),
            pid=pid,
        )
        self._entries[task_id] = entry

    def heartbeat(self, task_id: str) -> None:
        entry = self._entries.get(task_id)
        if entry:
            entry.last_heartbeat = time.time()

    def cancel(self, task_id: str) -> None:
        entry = self._entries.get(task_id)
        if entry:
            entry.cancelled = True

    def unregister(self, task_id: str) -> None:
        self._entries.pop(task_id, None)

    async def wait_for_completion(self, task_id: str, check_interval: float = 1.0) -> TaskState:
        """Wait for a task to complete, checking for timeout and cancellation."""
        entry = self._entries.get(task_id)
        if not entry:
            return TaskState.COMPLETED

        while True:
            if entry.cancelled:
                self.unregister(task_id)
                return TaskState.CANCELLED

            if entry.remaining <= 0:
                logger.warning("Task %s timed out after %.1fs", task_id, entry.elapsed)
                self.unregister(task_id)
                return TaskState.FAILED

            await asyncio.sleep(check_interval)

    def get_entry(self, task_id: str) -> MonitorEntry | None:
        return self._entries.get(task_id)

    def get_running_tasks(self) -> list[str]:
        return list(self._entries.keys())


_task_monitor: TaskMonitor | None = None


def get_task_monitor() -> TaskMonitor:
    global _task_monitor
    if _task_monitor is None:
        _task_monitor = TaskMonitor()
    return _task_monitor

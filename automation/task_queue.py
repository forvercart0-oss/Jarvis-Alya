"""Task queue for JARVIS Phase 13."""

from __future__ import annotations

import logging

logger = logging.getLogger("jarvis.automation.queue")


class TaskQueue:
    def __init__(self):
        self._queue: list[dict] = []

    def enqueue(self, task: dict, priority: str = "normal") -> None:
        priority_map = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        self._queue.append({
            "task": task,
            "priority": priority,
            "sort_key": priority_map.get(priority, 2),
        })
        self._queue.sort(key=lambda x: x["sort_key"])

    def dequeue(self) -> dict | None:
        if not self._queue:
            return None
        return self._queue.pop(0)["task"]

    def peek(self) -> dict | None:
        if not self._queue:
            return None
        return self._queue[0]["task"]

    def remove(self, task_id: str) -> bool:
        for i, item in enumerate(self._queue):
            if item["task"].get("id") == task_id:
                self._queue.pop(i)
                return True
        return False

    def __len__(self) -> int:
        return len(self._queue)

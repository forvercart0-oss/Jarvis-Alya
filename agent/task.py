"""Agent task utilities for JARVIS Phase 2."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agent.models import TaskStatus, TaskType


@dataclass
class TaskResult:
    success: bool
    output: Any = None
    error: str | None = None
    changed_files: list[str] = field(default_factory=list)
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


def create_task(
    title: str,
    task_type: TaskType,
    arguments: dict[str, Any] | None = None,
    risk: str = "low",
    max_retries: int = 3,
) -> dict[str, Any]:
    return {
        "task_id": str(uuid.uuid4())[:8],
        "title": title,
        "type": task_type.value,
        "status": TaskStatus.PENDING.value,
        "risk": risk,
        "arguments": arguments or {},
        "retries": 0,
        "max_retries": max_retries,
        "created_at": datetime.utcnow().isoformat(),
    }

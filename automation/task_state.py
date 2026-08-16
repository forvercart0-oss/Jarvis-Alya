"""Task states for JARVIS Phase 5 automation system."""

from __future__ import annotations

from enum import StrEnum


class TaskState(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    WAITING_PERMISSION = "waiting_permission"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_USER = "waiting_user"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskComplexity(StrEnum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# States that indicate a task is still active/needs attention
ACTIVE_STATES = {
    TaskState.PENDING,
    TaskState.PLANNING,
    TaskState.WAITING_PERMISSION,
    TaskState.RUNNING,
    TaskState.PAUSED,
    TaskState.WAITING_USER,
    TaskState.VERIFYING,
}

# States that indicate a task has finished
TERMINAL_STATES = {
    TaskState.COMPLETED,
    TaskState.FAILED,
    TaskState.CANCELLED,
}

# States that allow pause/resume
RESUMABLE_STATES = {
    TaskState.RUNNING,
    TaskState.PAUSED,
    TaskState.WAITING_USER,
}

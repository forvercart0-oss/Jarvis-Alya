"""Task states for JARVIS Phase 5 automation system."""

from __future__ import annotations

from enum import StrEnum


class TaskState(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    VERIFYING = "verifying"
    NEEDS_APPROVAL = "needs_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


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
    TaskState.READY,
    TaskState.RUNNING,
    TaskState.WAITING,
    TaskState.PAUSED,
    TaskState.VERIFYING,
    TaskState.NEEDS_APPROVAL,
    TaskState.BLOCKED,
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
    TaskState.WAITING,
    TaskState.NEEDS_APPROVAL,
}

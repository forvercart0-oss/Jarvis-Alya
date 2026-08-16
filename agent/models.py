"""Shared agent models for JARVIS Phase 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    WAITING_CONFIRMATION = "waiting_confirmation"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class TaskType(str, Enum):
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    FILESYSTEM_DELETE = "filesystem_delete"
    TERMINAL = "terminal"
    WEB_SEARCH = "web_search"
    GIT = "git"
    TEST = "test"
    PLAN = "plan"
    OBSERVE = "observe"
    MEMORY = "memory"
    VISION_CAPTURE = "vision_capture"
    VISION_ANALYZE = "vision_analyze"
    VISION_FIND = "vision_find"
    VISION_OCR = "vision_ocr"
    COMPUTER_MOUSE = "computer_mouse"
    COMPUTER_KEYBOARD = "computer_keyboard"


@dataclass
class AgentTask:
    task_id: str
    title: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    risk: str = "low"
    arguments: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "type": self.type.value,
            "status": self.status.value,
            "risk": self.risk,
            "arguments": self.arguments,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "retries": self.retries,
            "max_retries": self.max_retries,
        }


@dataclass
class AgentPlan:
    plan_id: str
    title: str
    description: str
    tasks: list[AgentTask] = field(default_factory=list)
    approved: bool = False
    project: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "approved": self.approved,
            "project": self.project,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentContext:
    user_request: str
    project: str | None = None
    project_root: str | None = None
    language: str = "en"
    persona: str = "jarvis"
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_request": self.user_request,
            "project": self.project,
            "project_root": self.project_root,
            "language": self.language,
            "persona": self.persona,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

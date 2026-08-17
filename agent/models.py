"""Shared agent models for JARVIS Phase 15."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    WAITING_FOR_PERMISSION = "waiting_for_permission"
    WAITING_FOR_USER = "waiting_for_user"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    PAUSED = "paused"
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
    VERIFYING = "verifying"
    OBSERVING = "observing"
    RECOVERING = "recovering"


class TaskType(str, Enum):
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    FILESYSTEM_DELETE = "filesystem_delete"
    CODE_EDIT = "code_edit"
    TERMINAL = "terminal"
    WEB_SEARCH = "web_search"
    GIT = "git"
    TEST = "test"
    BUILD = "build"
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"
    PLAN = "plan"
    OBSERVE = "observe"
    MEMORY = "memory"
    VISION_CAPTURE = "vision_capture"
    VISION_ANALYZE = "vision_analyze"
    VISION_FIND = "vision_find"
    VISION_OCR = "vision_ocr"
    COMPUTER_MOUSE = "computer_mouse"
    COMPUTER_KEYBOARD = "computer_keyboard"
    BROWSER_NAVIGATE = "browser_navigate"
    BROWSER_CLICK = "browser_click"
    BROWSER_TYPE = "browser_type"
    FORM_SUBMIT = "form_submit"
    SEND_MESSAGE = "send_message"
    DOWNLOAD_FILE = "download_file"


class CommandCategory(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    COMMUNICATE = "communicate"
    TRANSACTION = "transaction"
    SYSTEM = "system"
    SECURITY = "security"


class AutonomyLevel(str, Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentTask:
    task_id: str
    title: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    risk: str = "low"
    command_category: CommandCategory = CommandCategory.READ
    arguments: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3
    output: str = ""
    command: str = ""
    files_changed: list[str] = field(default_factory=list)
    checkpoint_id: str = ""
    duration_ms: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    observation: str = ""
    verification: str = ""
    requires_approval: bool = False
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "type": self.type.value,
            "status": self.status.value,
            "risk": self.risk,
            "command_category": self.command_category.value,
            "arguments": self.arguments,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "output": self.output,
            "command": self.command,
            "files_changed": self.files_changed,
            "checkpoint_id": self.checkpoint_id,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence.value,
            "observation": self.observation,
            "verification": self.verification,
            "requires_approval": self.requires_approval,
            "dry_run": self.dry_run,
        }


@dataclass
class AgentPlan:
    plan_id: str
    title: str
    description: str
    tasks: list[AgentTask] = field(default_factory=list)
    approved: bool = False
    project: str | None = None
    autonomy_level: AutonomyLevel = AutonomyLevel.ASSISTED
    dry_run: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "approved": self.approved,
            "project": self.project,
            "autonomy_level": self.autonomy_level.value,
            "dry_run": self.dry_run,
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
    autonomy_level: AutonomyLevel = AutonomyLevel.ASSISTED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_request": self.user_request,
            "project": self.project,
            "project_root": self.project_root,
            "language": self.language,
            "persona": self.persona,
            "max_retries": self.max_retries,
            "autonomy_level": self.autonomy_level.value,
            "metadata": self.metadata,
        }


@dataclass
class AgentArtifacts:
    task_id: str
    files_changed: list[str] = field(default_factory=list)
    commands_run: list[dict[str, Any]] = field(default_factory=list)
    tests_run: list[dict[str, Any]] = field(default_factory=list)
    checkpoints: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    duration_ms: int = 0
    summary: str = ""
    timeline: list[dict[str, Any]] = field(default_factory=list)
    background_tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "files_changed": self.files_changed,
            "commands_run": self.commands_run,
            "tests_run": self.tests_run,
            "checkpoints": self.checkpoints,
            "errors": self.errors,
            "fixes_applied": self.fixes_applied,
            "duration_ms": self.duration_ms,
            "summary": self.summary,
            "timeline": self.timeline[-50:],
            "background_tasks": self.background_tasks,
        }

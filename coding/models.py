"""Core models for JARVIS Phase 27 Coding Agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class ChangeStatus(StrEnum):
    PENDING = "pending"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class AgentType(StrEnum):
    ARCHITECT = "architect"
    CODER = "coder"
    TESTER = "tester"
    DEBUGGER = "debugger"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodingTask:
    task_id: str = ""
    goal: str = ""
    status: str = TaskStatus.PENDING
    steps: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    project: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status,
            "steps": self.steps,
            "current_step": self.current_step,
            "result": self.result,
            "error": self.error,
            "project": self.project,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ChangeCheckpoint:
    checkpoint_id: str = ""
    task_id: str = ""
    project: str = ""
    files: list[str] = field(default_factory=list)
    git_ref: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.checkpoint_id:
            self.checkpoint_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "task_id": self.task_id,
            "project": self.project,
            "files": self.files,
            "git_ref": self.git_ref,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class FileDiff:
    path: str
    change_type: str
    old_content: str = ""
    new_content: str = ""
    diff: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "diff": self.diff,
        }


@dataclass
class CodeReviewIssue:
    severity: str = Severity.INFO
    category: str = ""
    file: str = ""
    line: int = 0
    message: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class ProjectInfo:
    name: str = ""
    path: str = ""
    language: str = ""
    framework: str = ""
    package_manager: str = ""
    build_system: str = ""
    database: str = ""
    frontend: str = ""
    backend: str = ""
    tests: str = ""
    configuration: list[str] = field(default_factory=list)
    docker: bool = False
    ci_cd: bool = False
    git: bool = False
    environment_files: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "language": self.language,
            "framework": self.framework,
            "package_manager": self.package_manager,
            "build_system": self.build_system,
            "database": self.database,
            "frontend": self.frontend,
            "backend": self.backend,
            "tests": self.tests,
            "configuration": self.configuration,
            "docker": self.docker,
            "ci_cd": self.ci_cd,
            "git": self.git,
            "environment_files": self.environment_files,
            "metadata": self.metadata,
        }

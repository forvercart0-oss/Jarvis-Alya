"""Workflow models for JARVIS Phase 11."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class WorkflowStatus(str):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(str):
    ONE_TIME = "one_time"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"
    EVENT_BASED = "event_based"
    MANUAL = "manual"
    CONDITIONAL = "conditional"


class StepType(str):
    ACTION = "action"
    CONDITION = "condition"
    BROWSER = "browser"
    COMPUTER = "computer"
    AGENT = "agent"
    RESEARCH = "research"
    DOCUMENT = "document"
    NOTIFICATION = "notification"
    DELAY = "delay"
    VARIABLE = "variable"


@dataclass
class WorkflowStep:
    step_id: str
    type: str
    name: str
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    next_step_id: str | None = None
    condition: dict[str, Any] | None = None
    retry_policy: dict[str, Any] | None = None
    timeout_seconds: int = 300
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "next_step_id": self.next_step_id,
            "condition": self.condition,
            "retry_policy": self.retry_policy,
            "timeout_seconds": self.timeout_seconds,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStep:
        return cls(
            step_id=data.get("step_id", str(uuid.uuid4())),
            type=data.get("type", StepType.ACTION),
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
            next_step_id=data.get("next_step_id"),
            condition=data.get("condition"),
            retry_policy=data.get("retry_policy"),
            timeout_seconds=data.get("timeout_seconds", 300),
            order=data.get("order", 0),
        )


@dataclass
class Workflow:
    workflow_id: str
    name: str
    description: str = ""
    trigger: dict[str, Any] = field(default_factory=dict)
    steps: list[WorkflowStep] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    permissions: dict[str, Any] = field(default_factory=dict)
    status: str = WorkflowStatus.DRAFT
    enabled: bool = False
    created_at: str = ""
    updated_at: str = ""
    last_run: str | None = None
    next_run: str | None = None
    tags: list[str] = field(default_factory=list)
    project: str | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "steps": [s.to_dict() for s in self.steps],
            "variables": self.variables,
            "permissions": self.permissions,
            "status": self.status,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "tags": self.tags,
            "project": self.project,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workflow:
        steps = [WorkflowStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            workflow_id=data.get("workflow_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            trigger=data.get("trigger", {}),
            steps=steps,
            variables=data.get("variables", {}),
            permissions=data.get("permissions", {}),
            status=data.get("status", WorkflowStatus.DRAFT),
            enabled=data.get("enabled", False),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            last_run=data.get("last_run"),
            next_run=data.get("next_run"),
            tags=data.get("tags", []),
            project=data.get("project"),
        )


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    status: str = WorkflowStatus.RUNNING
    started_at: str = ""
    finished_at: str | None = None
    duration_seconds: float = 0.0
    steps: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "steps": self.steps,
            "errors": self.errors,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowRun:
        return cls(
            run_id=data.get("run_id", str(uuid.uuid4())),
            workflow_id=data.get("workflow_id", ""),
            status=data.get("status", WorkflowStatus.RUNNING),
            started_at=data.get("started_at", datetime.utcnow().isoformat()),
            finished_at=data.get("finished_at"),
            duration_seconds=data.get("duration_seconds", 0.0),
            steps=data.get("steps", []),
            errors=data.get("errors", []),
            result=data.get("result"),
        )


@dataclass
class Approval:
    approval_id: str
    workflow_id: str
    run_id: str
    step_id: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"
    status: str = "pending"
    created_at: str = ""
    resolved_at: str | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "action": self.action,
            "arguments": self.arguments,
            "risk_level": self.risk_level,
            "status": self.status,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

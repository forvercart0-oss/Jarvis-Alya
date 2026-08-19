"""Advanced task models for JARVIS Phase 13."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TaskDependency:
    dependency_id: str
    task_id: str
    depends_on_task_id: str
    status: str = "pending"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class TaskArtifact:
    artifact_id: str
    task_id: str
    type: str
    path: str = ""
    url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class TaskTemplate:
    template_id: str
    name: str
    description: str
    category: str = "general"
    steps: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class TaskAudit:
    audit_id: str
    task_id: str
    event: str
    detail: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

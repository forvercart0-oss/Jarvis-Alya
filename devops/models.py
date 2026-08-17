"""Core models for JARVIS Phase 28 DevOps Agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class DeploymentStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    BUILDING = "building"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    REMOTE = "remote"


class ContainerStatus(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    RESTARTING = "restarting"
    UNHEALTHY = "unhealthy"
    PENDING = "pending"


class IncidentStatus(StrEnum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    FAILED = "failed"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DeploymentTask:
    task_id: str = ""
    goal: str = ""
    environment: str = Environment.LOCAL
    status: str = DeploymentStatus.PENDING
    project: str = ""
    version: str = ""
    commit: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
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
            "environment": self.environment,
            "status": self.status,
            "project": self.project,
            "version": self.version,
            "commit": self.commit,
            "steps": self.steps,
            "current_step": self.current_step,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DeploymentPlan:
    plan_id: str = ""
    task_id: str = ""
    project: str = ""
    environment: str = Environment.LOCAL
    steps: list[dict[str, Any]] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    environment_vars: dict[str, str] = field(default_factory=dict)
    database_migrations: list[str] = field(default_factory=list)
    health_checks: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.plan_id:
            self.plan_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "project": self.project,
            "environment": self.environment,
            "steps": self.steps,
            "services": self.services,
            "ports": self.ports,
            "environment_vars": self.environment_vars,
            "database_migrations": self.database_migrations,
            "health_checks": self.health_checks,
            "metadata": self.metadata,
        }


@dataclass
class DeploymentCheckpoint:
    checkpoint_id: str = ""
    task_id: str = ""
    project: str = ""
    environment: str = Environment.LOCAL
    version: str = ""
    commit: str = ""
    image: str = ""
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
            "environment": self.environment,
            "version": self.version,
            "commit": self.commit,
            "image": self.image,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ContainerInfo:
    name: str = ""
    image: str = ""
    status: str = ContainerStatus.PENDING
    ports: list[str] = field(default_factory=list)
    cpu: str = ""
    memory: str = ""
    uptime: str = ""
    restarts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "image": self.image,
            "status": self.status,
            "ports": self.ports,
            "cpu": self.cpu,
            "memory": self.memory,
            "uptime": self.uptime,
            "restarts": self.restarts,
            "metadata": self.metadata,
        }


@dataclass
class ServerInfo:
    name: str = ""
    host: str = ""
    port: int = 22
    username: str = ""
    os: str = ""
    architecture: str = ""
    cpu: str = ""
    memory: str = ""
    disk: str = ""
    network: str = ""
    status: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "os": self.os,
            "architecture": self.architecture,
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "network": self.network,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class HealthCheck:
    name: str = ""
    type: str = "http"
    target: str = ""
    expected_status: int = 200
    timeout: int = 10
    interval: int = 30
    status: str = "unknown"
    last_check: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.last_check:
            self.last_check = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "target": self.target,
            "expected_status": self.expected_status,
            "timeout": self.timeout,
            "interval": self.interval,
            "status": self.status,
            "last_check": self.last_check,
            "metadata": self.metadata,
        }


@dataclass
class Incident:
    incident_id: str = ""
    task_id: str = ""
    service: str = ""
    status: str = IncidentStatus.DETECTED
    severity: str = Severity.HIGH
    description: str = ""
    cause: str = ""
    actions: list[str] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    resolved_at: str = ""

    def __post_init__(self):
        if not self.incident_id:
            self.incident_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "task_id": self.task_id,
            "service": self.service,
            "status": self.status,
            "severity": self.severity,
            "description": self.description,
            "cause": self.cause,
            "actions": self.actions,
            "timeline": self.timeline,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

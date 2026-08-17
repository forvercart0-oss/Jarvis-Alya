"""Artifact Manager for JARVIS Phase 23.

Tracks files, documents, images, reports, code, builds, logs,
and screenshots produced during task execution.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("jarvis.agent.artifacts")


class ArtifactType(str, Enum):
    FILE = "file"
    DOCUMENT = "document"
    IMAGE = "image"
    REPORT = "report"
    CODE = "code"
    BUILD = "build"
    LOG = "log"
    SCREENSHOT = "screenshot"
    URL = "url"
    DATA = "data"


@dataclass
class Artifact:
    artifact_id: str
    type: str
    name: str
    path: str = ""
    url: str = ""
    content: Any = None
    created_by: str = ""
    task_id: str = ""
    goal_id: str = ""
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.artifact_id:
            self.artifact_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "url": self.url,
            "created_by": self.created_by,
            "task_id": self.task_id,
            "goal_id": self.goal_id,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ArtifactManager:
    """Manages artifacts produced during goal execution."""

    def __init__(self):
        self._artifacts: dict[str, Artifact] = {}

    def create(self, type: str, name: str, path: str = "", url: str = "", content: Any = None, created_by: str = "", task_id: str = "", goal_id: str = "", metadata: dict[str, Any] | None = None) -> Artifact:
        artifact = Artifact(
            artifact_id=str(uuid.uuid4())[:8],
            type=type,
            name=name,
            path=path,
            url=url,
            content=content,
            created_by=created_by,
            task_id=task_id,
            goal_id=goal_id,
            metadata=metadata or {},
        )
        self._artifacts[artifact.artifact_id] = artifact
        logger.debug("Created artifact: %s (%s)", artifact.artifact_id, name)
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def list_by_goal(self, goal_id: str) -> list[Artifact]:
        return [a for a in self._artifacts.values() if a.goal_id == goal_id]

    def list_by_task(self, task_id: str) -> list[Artifact]:
        return [a for a in self._artifacts.values() if a.task_id == task_id]

    def update_status(self, artifact_id: str, status: str) -> bool:
        artifact = self._artifacts.get(artifact_id)
        if artifact:
            artifact.status = status
            artifact.updated_at = time.time()
            return True
        return False

    def search(self, query: str, goal_id: str = "") -> list[Artifact]:
        results = []
        query_lower = query.lower()
        for artifact in self._artifacts.values():
            if goal_id and artifact.goal_id != goal_id:
                continue
            if query_lower in artifact.name.lower() or query_lower in artifact.type.lower():
                results.append(artifact)
        return results

    def summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for a in self._artifacts.values():
            by_type[a.type] = by_type.get(a.type, 0) + 1
        return {"total": len(self._artifacts), "by_type": by_type}


artifact_manager = ArtifactManager()

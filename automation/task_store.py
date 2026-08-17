"""Task persistence: create, read, update, delete, and query tasks."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from automation.task_state import TaskState

logger = logging.getLogger("jarvis.automation.store")


class TaskStore:
    """Persistence layer for automation tasks using SQLiteMemory."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    # ------------------------------------------------------------- helpers
    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _sanitize_result(self, result: Any) -> str | None:
        if result is None:
            return None
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result, default=str)
        except Exception:
            return str(result)

    # ------------------------------------------------------------- crud
    def create_task(
        self,
        description: str,
        task_type: str = "general",
        complexity: str = "moderate",
        metadata: dict | None = None,
    ) -> dict:
        task_id = str(uuid.uuid4())[:8]
        record = {
            "id": task_id,
            "description": description,
            "status": TaskState.PENDING.value,
            "task_type": task_type,
            "complexity": complexity,
            "created_at": self._now(),
            "updated_at": self._now(),
            "result": None,
            "metadata": json.dumps(metadata or {}),
            "retries": 0,
            "max_retries": 3,
            "current_step": 0,
            "total_steps": 0,
            "elapsed_seconds": 0.0,
            "pid": None,
            "checkpoints": json.dumps([]),
            "logs": json.dumps([]),
        }
        try:
            return self._memory.store.add_task(record)
        except Exception as exc:
            logger.error("Failed to create task: %s", exc)
            record["id"] = task_id
            return record

    def get_task(self, task_id: str) -> dict | None:
        tasks = self._memory.store.get_tasks()
        for t in tasks:
            if t.get("id") == task_id:
                return self._parse(t)
        return None

    def get_tasks(self, status: str | None = None, limit: int = 50) -> list[dict]:
        tasks = self._memory.store.get_tasks(status=status)
        parsed = [self._parse(t) for t in tasks[:limit]]
        return parsed

    def get_active_tasks(self) -> list[dict]:
        active = []
        for t in self.get_tasks():
            if t.get("status") in (
                TaskState.PENDING.value,
                TaskState.PLANNING.value,
                TaskState.WAITING_PERMISSION.value,
                TaskState.RUNNING.value,
                TaskState.PAUSED.value,
                TaskState.WAITING_USER.value,
                TaskState.VERIFYING.value,
            ):
                active.append(t)
        return active

    def get_scheduled_tasks(self) -> list[dict]:
        scheduled = []
        for t in self.get_tasks():
            if t.get("status") == TaskState.PENDING.value and t.get("schedule"):
                scheduled.append(t)
        return scheduled

    def update_task(self, task_id: str, **kwargs) -> dict | None:
        task = self.get_task(task_id)
        if not task:
            return None
        sanitized = {}
        for key, value in kwargs.items():
            if key in {"result", "metadata", "checkpoints", "logs"}:
                sanitized[key] = self._sanitize_result(value)
            else:
                sanitized[key] = value
        sanitized["updated_at"] = self._now()
        try:
            self._memory.store.update_task(task_id, sanitized)
            return self.get_task(task_id)
        except Exception as exc:
            logger.error("Failed to update task %s: %s", task_id, exc)
            return None

    def delete_task(self, task_id: str) -> bool:
        try:
            self._memory.store.delete_task(task_id)
            return True
        except Exception as exc:
            logger.error("Failed to delete task %s: %s", task_id, exc)
            return False

    def append_log(self, task_id: str, action: str, result: str, duration_ms: float = 0.0) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        logs = task.get("logs") or []
        if isinstance(logs, str):
            try:
                logs = json.loads(logs)
            except Exception:
                logs = []
        logs.append(
            {
                "timestamp": self._now(),
                "action": action,
                "result": result,
                "duration_ms": duration_ms,
            }
        )
        self.update_task(task_id, logs=logs)

    def add_checkpoint(self, task_id: str, step: int, status: str, result: str) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        checkpoints = task.get("checkpoints") or []
        if isinstance(checkpoints, str):
            try:
                checkpoints = json.loads(checkpoints)
            except Exception:
                checkpoints = []
        checkpoints.append(
            {
                "step": step,
                "status": status,
                "result": result,
                "timestamp": self._now(),
            }
        )
        self.update_task(task_id, checkpoints=checkpoints)

    def get_checkpoints(self, task_id: str) -> list[dict]:
        task = self.get_task(task_id)
        if not task:
            return []
        raw = task.get("checkpoints") or []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                return []
        return raw

    def add_artifact(self, task_id: str, artifact_type: str, path: str = "", url: str = "", metadata: dict | None = None) -> dict:
        from automation.task_models import TaskArtifact
        artifact = TaskArtifact(
            artifact_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            type=artifact_type,
            path=path,
            url=url,
            metadata=metadata or {},
        )
        task = self.get_task(task_id)
        if not task:
            return artifact.to_dict()
        artifacts = task.get("artifacts") or []
        if isinstance(artifacts, str):
            try:
                artifacts = json.loads(artifacts)
            except Exception:
                artifacts = []
        artifacts.append(artifact.to_dict())
        self.update_task(task_id, artifacts=artifacts)
        return artifact.to_dict()

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> dict:
        from automation.task_models import TaskDependency
        dep = TaskDependency(
            dependency_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )
        task = self.get_task(task_id)
        if not task:
            return dep.to_dict()
        deps = task.get("dependencies") or []
        if isinstance(deps, str):
            try:
                deps = json.loads(deps)
            except Exception:
                deps = []
        deps.append(dep.to_dict())
        self.update_task(task_id, dependencies=deps)
        return dep.to_dict()

    def add_audit(self, task_id: str, event: str, detail: dict | None = None) -> dict:
        from automation.task_models import TaskAudit
        audit = TaskAudit(
            audit_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            event=event,
            detail=detail or {},
        )
        return audit.to_dict()

    def get_task_history(self, limit: int = 50) -> list[dict]:
        return self.get_tasks()[:limit]

    def get_tasks_by_project(self, project: str) -> list[dict]:
        tasks = self.get_tasks()
        return [t for t in tasks if t.get("project") == project][:50]

    def _parse(self, record: dict) -> dict:
        parsed = dict(record)
        for key in ("metadata", "checkpoints", "logs"):
            value = parsed.get(key)
            if isinstance(value, str):
                try:
                    parsed[key] = json.loads(value)
                except Exception:
                    parsed[key] = None if key == "metadata" else []
        return parsed

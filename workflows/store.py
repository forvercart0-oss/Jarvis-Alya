"""Workflow persistence for JARVIS Phase 11."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("jarvis.workflows.store")


class WorkflowStore:
    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def create_workflow(self, workflow: Any) -> dict:
        workflow_id = str(uuid.uuid4())[:8]
        workflow.workflow_id = workflow_id
        workflow.created_at = self._now()
        workflow.updated_at = self._now()
        try:
            return self._memory.store.add_workflow(workflow.to_dict())
        except Exception as exc:
            logger.error("Failed to create workflow: %s", exc)
            return workflow.to_dict()

    def get_workflow(self, workflow_id: str) -> dict | None:
        try:
            return self._memory.store.get_workflow(workflow_id)
        except Exception as exc:
            logger.error("Failed to get workflow: %s", exc)
            return None

    def get_workflows(self, status: str | None = None, limit: int = 50) -> list[dict]:
        try:
            return self._memory.store.get_workflows(status=status, limit=limit)
        except Exception as exc:
            logger.error("Failed to get workflows: %s", exc)
            return []

    def update_workflow(self, workflow_id: str, updates: dict) -> dict | None:
        updates["updated_at"] = self._now()
        try:
            return self._memory.store.update_workflow(workflow_id, updates)
        except Exception as exc:
            logger.error("Failed to update workflow: %s", exc)
            return None

    def delete_workflow(self, workflow_id: str) -> bool:
        try:
            return self._memory.store.delete_workflow(workflow_id)
        except Exception as exc:
            logger.error("Failed to delete workflow: %s", exc)
            return False

    def add_run(self, workflow_id: str, run: Any) -> dict:
        try:
            return self._memory.store.add_workflow_run(run.to_dict())
        except Exception as exc:
            logger.error("Failed to add workflow run: %s", exc)
            return run.to_dict()

    def get_runs(self, workflow_id: str, limit: int = 50) -> list[dict]:
        try:
            return self._memory.store.get_workflow_runs(workflow_id, limit=limit)
        except Exception as exc:
            logger.error("Failed to get workflow runs: %s", exc)
            return []

    def add_approval(self, approval: Approval) -> dict:
        try:
            return self._memory.store.add_workflow_approval(approval.to_dict())
        except Exception as exc:
            logger.error("Failed to add approval: %s", exc)
            return approval.to_dict()

    def get_approvals(self, status: str | None = None) -> list[dict]:
        try:
            return self._memory.store.get_workflow_approvals(status=status)
        except Exception as exc:
            logger.error("Failed to get approvals: %s", exc)
            return []

    def update_approval(self, approval_id: str, updates: dict) -> dict | None:
        updates["resolved_at"] = self._now()
        try:
            return self._memory.store.update_workflow_approval(approval_id, updates)
        except Exception as exc:
            logger.error("Failed to update approval: %s", exc)
            return None

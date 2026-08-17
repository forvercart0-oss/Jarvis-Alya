"""Workflow approval queue for JARVIS Phase 11."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.workflows.approval")


class ApprovalQueue:
    def __init__(self, store: Any):
        self._store = store

    def request_approval(self, workflow_id: str, run_id: str, step_id: str, action: str, arguments: dict[str, Any], risk_level: str = "medium") -> dict:
        from workflows.models import Approval
        approval = Approval(
            approval_id=str(__import__("uuid").uuid4())[:8],
            workflow_id=workflow_id,
            run_id=run_id,
            step_id=step_id,
            action=action,
            arguments=arguments,
            risk_level=risk_level,
        )
        return self._store.add_approval(approval)

    def approve(self, approval_id: str) -> dict | None:
        return self._store.update_approval(approval_id, {"status": "approved"})

    def deny(self, approval_id: str) -> dict | None:
        return self._store.update_approval(approval_id, {"status": "denied"})

    def get_pending(self) -> list[dict]:
        return self._store.get_approvals(status="pending")

    def get_all(self, status: str | None = None) -> list[dict]:
        return self._store.get_approvals(status=status)

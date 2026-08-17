"""Audit logger for JARVIS Phase 13."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.automation.audit")


class AuditLogger:
    def __init__(self, store: Any | None = None):
        self._store = store

    def log(self, task_id: str, event: str, detail: dict | None = None) -> None:
        detail = detail or {}
        safe_detail = self._redact(detail)
        logger.info("AUDIT task=%s event=%s detail=%s", task_id, event, safe_detail)
        if self._store:
            try:
                self._store.add_audit(task_id, event, safe_detail)
            except Exception:
                pass

    def _redact(self, data: dict) -> dict:
        redacted = dict(data)
        secret_keys = {"api_key", "secret", "token", "password", "passwd", "pwd", "authorization", "bearer", "private_key"}
        for key, value in redacted.items():
            if any(s in key.lower() for s in secret_keys):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact(value)
        return redacted

"""Vision audit logger for JARVIS Phase 14."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("jarvis.vision.audit")


class VisionAuditLogger:
    def __init__(self):
        self._events: list[dict[str, Any]] = []
        self._max_events: int = 500

    def log(self, event: str, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        safe = self._redact(data)
        entry = {
            "ts": time.time(),
            "event": event,
            "data": safe,
        }
        self._events.append(entry)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]
        logger.info("VISION_AUDIT %s %s", event, safe)

    def events(self) -> list[dict[str, Any]]:
        return self._events

    def clear(self) -> None:
        self._events = []

    def _redact(self, data: dict[str, Any]) -> dict[str, Any]:
        redacted = dict(data)
        secret_keys = {
            "api_key", "secret", "token", "password", "passwd", "pwd",
            "authorization", "bearer", "private_key",
        }
        for key, value in redacted.items():
            if any(s in key.lower() for s in secret_keys):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact(value)
            elif isinstance(value, str) and len(value) > 512:
                redacted[key] = value[:512] + "..."
        return redacted


vision_audit = VisionAuditLogger()

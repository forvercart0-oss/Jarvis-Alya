"""Action log for JARVIS Phase 24.

Logs visual actions for debugging and auditing.
Never logs passwords or sensitive content.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.action_log")


@dataclass
class ActionLogEntry:
    action: str
    target: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    confidence: float = 0.0
    duration_ms: float = 0.0
    success: bool = False
    timestamp: str = ""
    application: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self._redact(self.target),
            "arguments": self._redact_dict(self.arguments),
            "result": self._redact(self.result),
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "timestamp": self.timestamp,
            "application": self.application,
            "metadata": self.metadata,
        }

    @staticmethod
    def _redact(value: str) -> str:
        if not value:
            return value
        import re
        patterns = [
            r"(?i)password\s*[:=]\s*\S+",
            r"(?i)api[_-]?key\s*[:=]\s*\S+",
            r"(?i)token\s*[:=]\s*\S+",
            r"(?i)secret\s*[:=]\s*\S+",
            r"sk-[A-Za-z0-9]{20,}",
            r"ghp_[A-Za-z0-9]{36}",
            r"AIza[A-Za-z0-9_-]{35}",
        ]
        redacted = value
        for p in patterns:
            redacted = re.sub(p, "[REDACTED]", redacted)
        return redacted

    @staticmethod
    def _redact_dict(d: dict[str, Any]) -> dict[str, Any]:
        out = {}
        for k, v in d.items():
            if isinstance(v, str):
                out[k] = ActionLogEntry._redact(v)
            else:
                out[k] = v
        return out


class ActionLogger:
    def __init__(self, max_entries: int = 200):
        self._entries: list[ActionLogEntry] = []
        self._max_entries = max_entries

    def log(self, entry: ActionLogEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        logger.debug("Action log: %s %s -> %s", entry.action, entry.target, entry.result)

    def get_entries(self, limit: int = 50) -> list[dict[str, Any]]:
        entries = self._entries[-limit:]
        return [e.to_dict() for e in entries]

    def get_recent_failures(self, limit: int = 20) -> list[dict[str, Any]]:
        entries = [e for e in self._entries if not e.success]
        entries = entries[-limit:]
        return [e.to_dict() for e in entries]

    def clear(self) -> None:
        self._entries = []


action_logger = ActionLogger()

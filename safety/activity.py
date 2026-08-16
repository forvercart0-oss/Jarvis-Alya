"""Safe activity logging for JARVIS 2.0.

Logs skill/tool/permission activity to a JSONL file. Never logs passwords,
API keys, tokens, or private secrets - any suspicious value is masked.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.activity")

_SENSITIVE_HINTS = ("password", "passwd", "secret", "token", "api_key", "apikey", "authorization", "bearer", "private key")
_KEYLIKE_RE = re.compile(r"\b(sk|pk|ghp|gho|xox[baprs]|AKIA)[-_][A-Za-z0-9_-]{10,}\b")
_BEGIN_PRIVATE_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


def mask_sensitive(value: Any) -> Any:
    """Return a copy of value with anything secret-like masked to '***'."""
    if isinstance(value, dict):
        masked = {}
        for key, item in value.items():
            if any(hint in str(key).lower() for hint in _SENSITIVE_HINTS):
                masked[key] = "***"
            else:
                masked[key] = mask_sensitive(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    if isinstance(value, str):
        text = value
        if _KEYLIKE_RE.search(text) or _BEGIN_PRIVATE_RE.search(text):
            return "***"
        for hint in _SENSITIVE_HINTS:
            if hint in text.lower():
                return "***"
        if len(text) > 500:
            return text[:500] + "..."
        return text
    return value


class ActivityLogger:
    """Append-only JSONL activity log with automatic secret masking."""

    def __init__(self, path: str | Path = "logs/activity.jsonl", max_lines: int = 5000):
        self._path = Path(path)
        self._max_lines = max_lines
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def log(
        self,
        *,
        skill: str | None = None,
        action: str,
        permission: str | None = None,
        result: str | None = None,
        risk: str | None = None,
        detail: dict | None = None,
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "skill": skill,
            "action": action,
            "permission": permission,
            "result": result,
            "risk": risk,
        }
        if detail:
            entry["detail"] = mask_sensitive(detail)
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
            self._trim()
        except OSError as exc:
            logger.error("Failed to write activity log: %s", exc)
        return entry

    def _trim(self) -> None:
        if not self._path.exists():
            return
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                lines = fh.readlines()
            if len(lines) > self._max_lines:
                with self._path.open("w", encoding="utf-8") as fh:
                    fh.writelines(lines[-self._max_lines:])
        except OSError:
            pass

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except OSError:
            return []
        entries: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries


_logger_instance: ActivityLogger | None = None


def get_activity_logger(path: str | Path | None = None) -> ActivityLogger:
    global _logger_instance
    if _logger_instance is None or path is not None:
        _logger_instance = ActivityLogger(path or "logs/activity.jsonl")
    return _logger_instance


def reset_activity_logger() -> None:
    global _logger_instance
    _logger_instance = None

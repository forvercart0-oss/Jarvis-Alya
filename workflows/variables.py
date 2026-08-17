"""Workflow variable resolver for JARVIS Phase 11."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("jarvis.workflows.variables")


class VariableResolver:
    """Resolves workflow variables including built-in templates."""

    BUILTINS = {
        "date": lambda ctx: datetime.now(UTC).strftime("%Y-%m-%d"),
        "time": lambda ctx: datetime.now(UTC).strftime("%H:%M:%S"),
        "datetime": lambda ctx: datetime.now(UTC).isoformat(),
        "user": lambda ctx: ctx.get("user", ""),
        "project": lambda ctx: ctx.get("project", ""),
        "workspace": lambda ctx: ctx.get("workspace", ""),
        "last_result": lambda ctx: ctx.get("last_result", ""),
        "timestamp": lambda ctx: str(int(datetime.now(UTC).timestamp())),
    }

    def __init__(self, context: dict[str, Any] | None = None):
        self.context = context or {}
        self._variables: dict[str, Any] = dict(self.context)

    def set(self, key: str, value: Any) -> None:
        self._variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._variables:
            return self._variables[key]
        if key in self.BUILTINS:
            return self.BUILTINS[key](self.context)
        return default

    def resolve(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._resolve_string(value)
        if isinstance(value, list):
            return [self.resolve(item) for item in value]
        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        return value

    def _resolve_string(self, value: str) -> str:
        import re
        pattern = re.compile(r"\{\{(\w+)\}\}")

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            resolved = self.get(key)
            if resolved is None:
                return match.group(0)
            return str(resolved)

        result = pattern.sub(replacer, value)
        return result

    def to_dict(self) -> dict[str, Any]:
        return dict(self._variables)

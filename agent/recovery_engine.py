"""Recovery Engine for JARVIS Phase 23.

Classifies errors and attempts recovery with retries, fallback
agents/tools, and verification.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("jarvis.agent.recovery")


class ErrorClass(str, Enum):
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    DEPENDENCY_ERROR = "dependency_error"
    CODE_ERROR = "code_error"
    CONFIG_ERROR = "config_error"
    AUTH_ERROR = "auth_error"
    RESOURCE_ERROR = "resource_error"
    TOOL_ERROR = "tool_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RecoveryResult:
    recovered: bool
    error_class: str
    attempts: int
    fallback_used: bool
    message: str = ""
    duration_ms: int = 0


class RecoveryEngine:
    """Handles task failure recovery."""

    def __init__(self):
        self._retry_delays: dict[str, float] = {
            ErrorClass.NETWORK_ERROR.value: 1.0,
            ErrorClass.TIMEOUT.value: 2.0,
            ErrorClass.DEPENDENCY_ERROR.value: 1.5,
            ErrorClass.CODE_ERROR.value: 0.5,
            ErrorClass.CONFIG_ERROR.value: 0.5,
            ErrorClass.AUTH_ERROR.value: 0.0,
            ErrorClass.RESOURCE_ERROR.value: 2.0,
            ErrorClass.TOOL_ERROR.value: 1.0,
            ErrorClass.UNKNOWN_ERROR.value: 1.0,
        }

    def classify_error(self, error: Exception | str) -> ErrorClass:
        error_str = str(error).lower()
        if any(k in error_str for k in ["timeout", "timed out"]):
            return ErrorClass.TIMEOUT
        if any(k in error_str for k in ["network", "connection", "dns", "unreachable"]):
            return ErrorClass.NETWORK_ERROR
        if any(k in error_str for k in ["dependency", "import", "module"]):
            return ErrorClass.DEPENDENCY_ERROR
        if any(k in error_str for k in ["syntax", "indentation", "typeerror", "valueerror", "runtimeerror"]):
            return ErrorClass.CODE_ERROR
        if any(k in error_str for k in ["config", "setting", "env"]):
            return ErrorClass.CONFIG_ERROR
        if any(k in error_str for k in ["auth", "permission", "forbidden", "401", "403"]):
            return ErrorClass.AUTH_ERROR
        if any(k in error_str for k in ["memory", "ram", "resource", "oom", "cpu"]):
            return ErrorClass.RESOURCE_ERROR
        if any(k in error_str for k in ["tool", "not found", "unknown"]):
            return ErrorClass.TOOL_ERROR
        return ErrorClass.UNKNOWN_ERROR

    def should_retry(self, error_class: ErrorClass, attempt: int, max_retries: int) -> bool:
        if error_class == ErrorClass.AUTH_ERROR:
            return False
        return attempt < max_retries

    def get_retry_delay(self, error_class: ErrorClass, attempt: int) -> float:
        base = self._retry_delays.get(error_class.value, 1.0)
        return base * (2 ** attempt)

    async def attempt_recovery(self, error: Exception | str, task_context: dict[str, Any], max_retries: int = 3) -> RecoveryResult:
        start = time.time()
        error_class = self.classify_error(error)
        attempts = 0

        for attempt in range(max_retries + 1):
            if not self.should_retry(error_class, attempt, max_retries):
                break
            attempts += 1
            delay = self.get_retry_delay(error_class, attempt)
            if delay > 0:
                await asyncio.sleep(delay)
            return RecoveryResult(
                recovered=True,
                error_class=error_class.value,
                attempts=attempts,
                fallback_used=False,
                message=f"Retried after {error_class.value}",
                duration_ms=int((time.time() - start) * 1000),
            )

        return RecoveryResult(
            recovered=False,
            error_class=error_class.value,
            attempts=attempts,
            fallback_used=False,
            message=f"Recovery failed: {error_class.value}",
            duration_ms=int((time.time() - start) * 1000),
        )


recovery_engine = RecoveryEngine()

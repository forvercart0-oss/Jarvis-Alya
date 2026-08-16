"""Confirmation handling for dangerous operations in JARVIS 2.0.

Manages tool confirmation flow, shows permission summaries before execution,
and tracks confirmation state.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

logger = logging.getLogger("jarvis.safety.confirmation")


@dataclass
class ConfirmationRequest:
    """Represents a pending confirmation request."""
    id: str
    tool_name: str
    arguments: dict
    summary: str
    risk_level: str
    timestamp: datetime = field(default_factory=datetime.now)
    confirmed: Optional[bool] = None
    timeout_seconds: int = 120


class ConfirmationManager:
    """Manages dangerous command confirmations.

    Tracks pending confirmations, generates summaries, and handles
    the confirmation flow for tool execution.
    """

    def __init__(self):
        self._pending: dict[str, ConfirmationRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._results: dict[str, bool] = {}
        self._lock = asyncio.Lock()

    def create_request(
        self,
        tool_name: str,
        arguments: dict,
        risk_level: str = "medium",
        timeout_seconds: int = 120,
    ) -> ConfirmationRequest:
        """Create a new confirmation request."""
        import uuid
        request_id = str(uuid.uuid4())[:8]
        summary = self._build_summary(tool_name, arguments)
        request = ConfirmationRequest(
            id=request_id,
            tool_name=tool_name,
            arguments=arguments,
            summary=summary,
            risk_level=risk_level,
            timeout_seconds=timeout_seconds,
        )
        self._pending[request_id] = request
        self._events[request_id] = asyncio.Event()
        return request

    def _build_summary(self, tool_name: str, arguments: dict) -> str:
        """Build a human-readable summary of the tool call."""
        if not arguments:
            return f"Execute tool: {tool_name}"

        # Mask sensitive arguments
        safe_args = self._mask_sensitive_arguments(arguments)

        parts = [f"Execute: {tool_name}"]
        for key, value in safe_args.items():
            parts.append(f"  {key}: {value}")
        return "\n".join(parts)

    def _mask_sensitive_arguments(self, arguments: dict) -> dict:
        """Mask sensitive arguments in the summary."""
        sensitive_keys = {"password", "secret", "token", "api_key", "key"}
        masked = {}
        for key, value in arguments.items():
            if any(s in key.lower() for s in sensitive_keys):
                masked[key] = "***"
            elif isinstance(value, str) and len(value) > 50:
                masked[key] = value[:50] + "..."
            else:
                masked[key] = value
        return masked

    async def wait_for_confirmation(
        self,
        request_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[bool]:
        """Wait for the user to confirm or deny the request.

        Returns True if confirmed, False if denied, None if timed out.
        """
        event = self._events.get(request_id)
        if not event:
            return None

        try:
            timeout_val = timeout or 120.0
            await asyncio.wait_for(event.wait(), timeout=timeout_val)
            result = self._results.get(request_id, None)
            return result
        except asyncio.TimeoutError:
            logger.warning("Confirmation request %s timed out", request_id)
            self._pending.pop(request_id, None)
            self._events.pop(request_id, None)
            self._results.pop(request_id, None)
            return None

    def confirm(self, request_id: str, confirmed: bool) -> bool:
        """Record the user's confirmation decision.

        Returns True if the request was found and processed.
        """
        event = self._events.get(request_id)
        if not event:
            logger.warning("Confirmation request %s not found", request_id)
            return False

        self._results[request_id] = confirmed
        event.set()

        request = self._pending.get(request_id)
        if request:
            request.confirmed = confirmed
            logger.info(
                "Confirmation request %s for %s: %s",
                request_id,
                request.tool_name,
                "confirmed" if confirmed else "denied",
            )

        return True

    def get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """Get a pending confirmation request."""
        return self._pending.get(request_id)

    def get_pending_requests(self) -> list[ConfirmationRequest]:
        """Get all pending confirmation requests."""
        return list(self._pending.values())

    def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending confirmation request."""
        if request_id in self._pending:
            del self._pending[request_id]
            event = self._events.get(request_id)
            if event:
                event.set()
            self._results[request_id] = False
            self._events.pop(request_id, None)
            return True
        return False

    def cleanup_expired(self, max_age_seconds: int = 300) -> None:
        """Clean up expired confirmation requests."""
        now = datetime.now()
        expired = []
        for request_id, request in self._pending.items():
            age = (now - request.timestamp).total_seconds()
            if age > max_age_seconds:
                expired.append(request_id)

        for request_id in expired:
            self._events.get(request_id) and self._events.pop(request_id).set()
            self._results[request_id] = False
            self._pending.pop(request_id, None)


_confirmation_manager: Optional[ConfirmationManager] = None


def get_confirmation_manager() -> ConfirmationManager:
    """Get the global confirmation manager."""
    global _confirmation_manager
    if _confirmation_manager is None:
        _confirmation_manager = ConfirmationManager()
    return _confirmation_manager


def get_confirmation_summary(tool_name: str, arguments: dict) -> str:
    """Generate a human-readable confirmation summary."""
    manager = get_confirmation_manager()
    request = manager.create_request(tool_name, arguments, timeout_seconds=0)
    return request.summary

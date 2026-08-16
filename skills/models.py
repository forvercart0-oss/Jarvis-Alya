"""Shared skill data models and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_PRIORITIES: tuple[str, ...] = ("high", "normal", "low")

# Canonical phase-1 permission ids that may appear in a skill's permission
# requests (either dotted ids or their legacy snake_case aliases).
CANONICAL_PERMISSION_IDS: tuple[str, ...] = (
    "filesystem.read",
    "filesystem.write",
    "terminal.read",
    "terminal.execute",
    "network.request",
    "microphone",
    "camera",
    "clipboard.read",
    "clipboard.write",
    "notifications",
    "memory.read",
    "memory.write",
)

# Legacy skill permission keys still accepted (mapped to canonical ids).
LEGACY_PERMISSION_KEYS: tuple[str, ...] = (
    "filesystem_read",
    "filesystem_write",
    "terminal",
    "terminal_read",
    "terminal_execute",
    "network",
    "microphone",
    "camera",
    "clipboard_read",
    "clipboard_write",
    "notifications",
    "memory_read",
    "memory_write",
)


@dataclass
class SkillMatch:
    """A skill that matched a user message, with relevance metadata."""

    skill_id: str
    name: str
    priority: str = "normal"
    triggers: list[str] = field(default_factory=list)
    relevance: int = 0
    source: str = "custom"

    def as_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "priority": self.priority,
            "triggers": list(self.triggers),
            "relevance": self.relevance,
            "source": self.source,
        }

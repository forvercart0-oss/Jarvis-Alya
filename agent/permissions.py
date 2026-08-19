"""Agent permissions for JARVIS Phase 8."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.agent.permissions")


@dataclass
class AgentPermissions:
    filesystem_read: bool = True
    filesystem_write: bool = True
    filesystem_delete: str = "ask"
    terminal: str = "ask"
    network: str = "ask"
    git: str = "ask"
    browser: str = "ask"
    auto_execute: bool = False
    auto_fix: bool = True
    max_retries: int = 3
    confirmation_level: str = "risky_only"
    trusted_directories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "filesystem_read": self.filesystem_read,
            "filesystem_write": self.filesystem_write,
            "filesystem_delete": self.filesystem_delete,
            "terminal": self.terminal,
            "network": self.network,
            "git": self.git,
            "browser": self.browser,
            "auto_execute": self.auto_execute,
            "auto_fix": self.auto_fix,
            "max_retries": self.max_retries,
            "confirmation_level": self.confirmation_level,
            "trusted_directories": self.trusted_directories,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentPermissions:
        return cls(
            filesystem_read=data.get("filesystem_read", True),
            filesystem_write=data.get("filesystem_write", True),
            filesystem_delete=data.get("filesystem_delete", "ask"),
            terminal=data.get("terminal", "ask"),
            network=data.get("network", "ask"),
            git=data.get("git", "ask"),
            browser=data.get("browser", "ask"),
            auto_execute=data.get("auto_execute", False),
            auto_fix=data.get("auto_fix", True),
            max_retries=data.get("max_retries", 3),
            confirmation_level=data.get("confirmation_level", "risky_only"),
            trusted_directories=data.get("trusted_directories", []),
        )

    def requires_confirmation(self, task_type: str, risk: str = "low") -> bool:
        if self.confirmation_level == "never":
            return False
        if self.confirmation_level == "always":
            return True
        if risk in ("high", "destructive"):
            return True
        if task_type == "filesystem_delete" and self.filesystem_delete == "ask":
            return True
        if task_type == "terminal" and self.terminal == "ask":
            return True
        if task_type == "git" and self.git == "ask":
            return True
        return False

    def is_trusted_path(self, path: str) -> bool:
        if not self.trusted_directories:
            return True
        resolved = os.path.abspath(path)
        for trusted in self.trusted_directories:
            if resolved.startswith(os.path.abspath(trusted)):
                return True
        return False

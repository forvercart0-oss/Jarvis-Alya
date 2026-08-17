"""Updater models for JARVIS Phase 31."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class UpdateState(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    UPDATE_AVAILABLE = "update_available"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    VERIFYING = "verifying"
    READY_TO_INSTALL = "ready_to_install"
    INSTALLING = "installing"
    RESTARTING = "restarting"
    UPDATED = "updated"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    UP_TO_DATE = "up_to_date"
    OFFLINE = "offline"
    DISABLED = "disabled"
    DEVELOPMENT = "development"


@dataclass
class UpdateInfo:
    commit_sha: str = ""
    commit_message: str = ""
    commit_author: str = ""
    committed_at: str = ""
    url: str = ""
    branch: str = "main"
    repository: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_sha": self.commit_sha,
            "commit_message": self.commit_message,
            "commit_author": self.commit_author,
            "committed_at": self.committed_at,
            "url": self.url,
            "branch": self.branch,
            "repository": self.repository,
            "metadata": self.metadata,
        }


@dataclass
class UpdaterConfig:
    enabled: bool = True
    auto_check: bool = True
    check_interval_hours: int = 6
    auto_download: bool = True
    auto_install: bool = False
    install_on_metered: bool = False
    require_confirmation: bool = True
    last_check: str = ""
    last_update: str = ""
    current_commit: str = ""
    installation_type: str = "source"  # source | desktop | package

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "auto_check": self.auto_check,
            "check_interval_hours": self.check_interval_hours,
            "auto_download": self.auto_download,
            "auto_install": self.auto_install,
            "install_on_metered": self.install_on_metered,
            "require_confirmation": self.require_confirmation,
            "last_check": self.last_check,
            "last_update": self.last_update,
            "current_commit": self.current_commit,
            "installation_type": self.installation_type,
        }


@dataclass
class UpdateProgress:
    state: UpdateState = UpdateState.IDLE
    current: int = 0
    total: int = 0
    message: str = ""
    error: str = ""
    available_update: UpdateInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "current": self.current,
            "total": self.total,
            "message": self.message,
            "error": self.error,
            "available_update": self.available_update.to_dict() if self.available_update else None,
            "progress_percent": round((self.current / self.total) * 100) if self.total > 0 else 0,
        }

"""Download manager for JARVIS Phase 25.

Track: filename, URL, size, progress, status, destination
Events: download_started, download_progress, download_complete, download_failed
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.browser.download_manager")


@dataclass
class DownloadTask:
    id: str = ""
    filename: str = ""
    url: str = ""
    size: int = 0
    progress: float = 0.0
    status: str = "pending"
    destination: str = ""
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "url": self.url,
            "size": self.size,
            "progress": self.progress,
            "status": self.status,
            "destination": self.destination,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


class BrowserDownloadManager:
    def __init__(self, download_dir: str = ""):
        self._downloads: dict[str, DownloadTask] = {}
        self._download_dir = download_dir or str(Path.home() / "Downloads" / "JARVIS-Browser")
        Path(self._download_dir).mkdir(parents=True, exist_ok=True)

    def register(self, task: DownloadTask) -> None:
        self._downloads[task.id] = task
        logger.info("Download registered: %s -> %s", task.url, task.filename)

    def update(self, task_id: str, **kwargs: Any) -> DownloadTask | None:
        task = self._downloads.get(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            if kwargs.get("status") == "complete" and not task.completed_at:
                task.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        return task

    def get(self, task_id: str) -> DownloadTask | None:
        return self._downloads.get(task_id)

    def list_active(self) -> list[DownloadTask]:
        return [t for t in self._downloads.values() if t.status in ("pending", "downloading")]

    def list_completed(self) -> list[DownloadTask]:
        return [t for t in self._downloads.values() if t.status == "complete"]

    def get_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        tasks = sorted(self._downloads.values(), key=lambda t: t.started_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]


browser_download_manager = BrowserDownloadManager()

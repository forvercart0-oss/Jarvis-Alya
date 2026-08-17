"""Updater manager for JARVIS Phase 31."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from updater.github import GitHubClient
from updater.downloader import UpdateDownloader
from updater.verifier import UpdateVerifier
from updater.installer import UpdateInstaller
from updater.models import UpdaterConfig, UpdateInfo, UpdateProgress, UpdateState

logger = logging.getLogger("jarvis.updater.manager")


class UpdaterManager:
    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent
        self.config = UpdaterConfig()
        self.progress = UpdateProgress()
        self._github = GitHubClient()
        self._downloader = UpdateDownloader()
        self._verifier = UpdateVerifier()
        self._installer = UpdateInstaller(self.repo_root)
        self._check_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._current_commit = self._detect_current_commit()
        self.config.current_commit = self._current_commit

    def _detect_current_commit(self) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()[:12]
        except Exception:
            pass
        return os.environ.get("JARVIS_COMMIT", "unknown")

    async def start(self) -> None:
        if not self.config.enabled:
            self.progress.state = UpdateState.DISABLED
            return
        if self.config.auto_check:
            self._schedule_check()

    async def stop(self) -> None:
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
            with suppress(Exception):
                await self._check_task
        await self._github.close()
        await self._downloader.close()

    def _schedule_check(self) -> None:
        if self._check_task and not self._check_task.done():
            return
        self._check_task = asyncio.create_task(self._periodic_check())

    async def _periodic_check(self) -> None:
        while True:
            try:
                await self.check_for_update()
            except Exception as exc:
                logger.warning("Periodic update check failed: %s", exc)
            await asyncio.sleep(self.config.check_interval_hours * 3600)

    async def check_for_update(self, force: bool = False) -> UpdateProgress:
        async with self._lock:
            self.progress.state = UpdateState.CHECKING
            self.progress.message = "Checking for updates..."
            self.progress.error = ""
            self.config.last_check = datetime.now(UTC).isoformat()
            latest = await self._github.get_latest_commit()
            if latest is None:
                self.progress.state = UpdateState.OFFLINE
                self.progress.message = "GitHub unavailable"
                return self.progress
            if latest.commit_sha == self._current_commit:
                self.progress.state = UpdateState.UP_TO_DATE
                self.progress.message = "You're up to date"
                self.progress.available_update = None
                return self.progress
            self.progress.state = UpdateState.UPDATE_AVAILABLE
            self.progress.message = "Update available"
            self.progress.available_update = latest
            if self.config.auto_download:
                await self._download_update(latest)
            return self.progress

    async def _download_update(self, update_info: UpdateInfo) -> None:
        self.progress.state = UpdateState.DOWNLOADING
        self.progress.message = "Downloading update..."
        zip_path = await self._downloader.download_commit(
            update_info.commit_sha,
            self.progress,
        )
        if zip_path is None:
            return
        self.progress.state = UpdateState.VERIFYING
        self.progress.message = "Verifying update..."
        if not self._verifier.verify_zip(zip_path, update_info.commit_sha):
            self.progress.error = "Update verification failed"
            self.progress.state = UpdateState.FAILED
            return
        self.progress.state = UpdateState.READY_TO_INSTALL
        self.progress.message = "Update ready to install"
        if self._installer.is_development():
            self.progress.error = "Development installation detected. Automatic update skipped."
            self.progress.state = UpdateState.DEVELOPMENT
            return
        if self.config.auto_install:
            await self._install_update(zip_path, update_info)

    async def _install_update(self, zip_path: Path, update_info: UpdateInfo) -> None:
        self.progress.state = UpdateState.INSTALLING
        self.progress.message = "Installing update..."
        success = await self._installer.install(zip_path, update_info.commit_sha, self.progress)
        if success:
            self.config.last_update = datetime.now(UTC).isoformat()
            self.progress.state = UpdateState.RESTARTING
            self.progress.message = "Restarting..."
        else:
            self.progress.state = UpdateState.FAILED

    def get_status(self) -> dict[str, Any]:
        return {
            "progress": self.progress.to_dict(),
            "config": self.config.to_dict(),
            "current_commit": self._current_commit,
        }

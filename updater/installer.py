"""Platform-specific installer for JARVIS updater."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
from pathlib import Path

from updater.models import UpdateProgress, UpdateState

logger = logging.getLogger("jarvis.updater.installer")


class UpdateInstaller:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.system = platform.system().lower()

    def detect_installation_type(self) -> str:
        if self.repo_root.name == "src-tauri":
            return "desktop"
        if (self.repo_root / ".git").exists():
            return "source"
        return "package"

    def is_development(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
        except Exception:
            pass
        return False

    async def install(self, update_dir: Path, commit_sha: str, progress: UpdateProgress) -> bool:
        progress.state = UpdateState.INSTALLING
        progress.message = "Preparing update..."
        try:
            if self.system == "linux":
                return await self._install_linux(update_dir, commit_sha, progress)
            elif self.system == "windows":
                return await self._install_windows(update_dir, commit_sha, progress)
            elif self.system == "darwin":
                return await self._install_macos(update_dir, commit_sha, progress)
            else:
                progress.error = f"Unsupported platform: {self.system}"
                progress.state = UpdateState.FAILED
                return False
        except Exception as exc:
            progress.error = str(exc)
            progress.state = UpdateState.FAILED
            logger.warning("Installation failed: %s", exc)
            return False

    async def _install_linux(self, update_dir: Path, commit_sha: str, progress: UpdateProgress) -> bool:
        return await self._install_generic(update_dir, commit_sha, progress)

    async def _install_windows(self, update_dir: Path, commit_sha: str, progress: UpdateProgress) -> bool:
        return await self._install_generic(update_dir, commit_sha, progress)

    async def _install_macos(self, update_dir: Path, commit_sha: str, progress: UpdateProgress) -> bool:
        return await self._install_generic(update_dir, commit_sha, progress)

    async def _install_generic(self, update_dir: Path, commit_sha: str, progress: UpdateProgress) -> bool:
        install_type = self.detect_installation_type()
        if install_type == "source" and self.is_development():
            progress.error = "Development installation detected. Automatic update skipped."
            progress.state = UpdateState.FAILED
            return False
        backup_dir = self.repo_root.parent / f"{self.repo_root.name}_backup_{commit_sha[:7]}"
        try:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(self.repo_root, backup_dir, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "dist", ".venv", "tts-venv", "logs", "data"))
        except Exception as exc:
            logger.warning("Backup failed: %s", exc)
        progress.message = "Replacing application files..."
        try:
            extracted = update_dir
            for item in extracted.iterdir():
                if item.name == "__pycache__":
                    continue
                dest = self.repo_root / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            progress.state = UpdateState.UPDATED
            progress.message = "Update installed successfully"
            return True
        except Exception as exc:
            progress.error = str(exc)
            progress.state = UpdateState.FAILED
            if backup_dir.exists():
                shutil.copytree(backup_dir, self.repo_root, dirs_exist_ok=True)
            return False

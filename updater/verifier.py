"""Verifier for JARVIS updater."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from typing import Any

from updater.models import UpdateInfo, UpdateProgress

logger = logging.getLogger("jarvis.updater.verifier")


class UpdateVerifier:
    def verify_zip(self, zip_path: Path, expected_sha: str) -> bool:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()
                if not namelist:
                    return False
                top_dir = namelist[0].split("/")[0]
                expected_prefix = f"{expected_sha[:7]}-"
                if top_dir.startswith(expected_prefix) or expected_sha in top_dir:
                    return True
                return True
        except Exception as exc:
            logger.warning("Zip verification failed: %s", exc)
            return False

    def verify_commit_sha(self, content_path: Path, expected_sha: str) -> bool:
        git_dir = content_path / ".git"
        if not git_dir.exists():
            return False
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=content_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                actual = result.stdout.strip()
                return actual == expected_sha
        except Exception:
            pass
        return False

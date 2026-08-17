"""Agent checkpoint system using Git."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("jarvis.agent.checkpoint")


class AgentCheckpoint:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def create(self, message: str) -> dict[str, Any]:
        try:
            import subprocess
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            full_message = f"[agent-checkpoint] {ts} - {message}"
            result = subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            result = subprocess.run(
                ["git", "commit", "-m", full_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            commit_hash = result.stdout.strip().split()[-1] if result.stdout.strip() else ""
            return {"success": True, "commit_hash": commit_hash, "message": full_message}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def rollback(self, commit_hash: str) -> dict[str, Any]:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "revert", "--no-commit", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            result = subprocess.run(
                ["git", "commit", "-m", f"[agent-rollback] Revert {commit_hash}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            return {"success": True, "message": f"Rolled back to {commit_hash}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def list(self) -> list[dict[str, Any]]:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "-20", "--grep", "agent-checkpoint"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return []
            entries = []
            for line in result.stdout.strip().splitlines():
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    entries.append({"hash": parts[0], "message": parts[1]})
            return entries
        except Exception:
            return []

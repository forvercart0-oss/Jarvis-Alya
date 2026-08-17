"""Extended Git manager for JARVIS Phase 27."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from coding.models import ChangeCheckpoint, CodingTask

logger = logging.getLogger("jarvis.coding.git_manager")


class CodingGitManager:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir

    def status(self, project: str) -> dict[str, Any]:
        try:
            from git.status import get_status
            result = get_status(str(self._base_dir / project))
            return {"success": True, "status": result.to_dict()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def diff(self, project: str, target: str = "") -> dict[str, Any]:
        try:
            from git.diff import get_diff
            diffs = get_diff(str(self._base_dir / project), target)
            return {"success": True, "diffs": [d.__dict__ for d in diffs]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def log(self, project: str, limit: int = 20) -> dict[str, Any]:
        try:
            from git.operations import git_log
            commits = git_log(str(self._base_dir / project), limit=limit)
            return {"success": True, "commits": commits}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def branch(self, project: str) -> dict[str, Any]:
        try:
            from git.operations import git_branch
            result = git_branch(str(self._base_dir / project))
            return {"success": True, "branches": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def create_branch(self, project: str, branch_name: str) -> dict[str, Any]:
        try:
            import subprocess
            root = self._base_dir / project
            result = subprocess.run(["git", "checkout", "-b", branch_name], cwd=root, capture_output=True, text=True)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def commit(self, project: str, message: str, files: list[str] | None = None) -> dict[str, Any]:
        try:
            from git.operations import git_add, git_commit
            root = str(self._base_dir / project)
            if files:
                add_result = git_add(root, files)
            else:
                add_result = git_add(root, ["."])
            if not add_result.get("success"):
                return add_result
            result = git_commit(root, message)
            return result
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def push(self, project: str) -> dict[str, Any]:
        try:
            import subprocess
            root = self._base_dir / project
            result = subprocess.run(["git", "push"], cwd=root, capture_output=True, text=True)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def create_checkpoint(self, task: CodingTask, project: str) -> ChangeCheckpoint:
        try:
            import subprocess
            root = self._base_dir / project
            result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
            git_ref = result.stdout.strip() if result.returncode == 0 else ""
            return ChangeCheckpoint(task_id=task.task_id, project=project, git_ref=git_ref)
        except Exception:
            return ChangeCheckpoint(task_id=task.task_id, project=project)


coding_git_manager = CodingGitManager

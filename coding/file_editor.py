"""File editor for JARVIS Phase 27."""

from __future__ import annotations

import difflib
import logging
from pathlib import Path
from typing import Any

from coding.models import ChangeCheckpoint, FileDiff

logger = logging.getLogger("jarvis.coding.file_editor")


class FileEditor:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._checkpoints: dict[str, ChangeCheckpoint] = {}

    def _resolve(self, project: str, rel_path: str) -> Path:
        root = self._base_dir / project
        path = (root / rel_path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Path escapes project directory.")
        return path

    def create_checkpoint(self, task_id: str, project: str, files: list[str]) -> ChangeCheckpoint:
        checkpoint = ChangeCheckpoint(task_id=task_id, project=project, files=files)
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint
        return checkpoint

    def read(self, project: str, rel_path: str) -> dict[str, Any]:
        try:
            path = self._resolve(project, rel_path)
            if not path.exists():
                return {"success": False, "error": f"File not found: {rel_path}"}
            content = path.read_text(errors="replace")
            return {"success": True, "path": rel_path, "content": content, "size": len(content)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def write(self, project: str, rel_path: str, content: str) -> dict[str, Any]:
        try:
            path = self._resolve(project, rel_path)
            old_content = ""
            if path.exists():
                old_content = path.read_text(errors="replace")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            diff = "\n".join(difflib.unified_diff(old_content.splitlines(), content.splitlines(), lineterm=""))
            return {
                "success": True,
                "path": rel_path,
                "diff": diff,
                "added": len(diff.splitlines()) if diff else 0,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def diff(self, project: str, rel_path: str, old_content: str, new_content: str) -> FileDiff:
        diff = "\n".join(difflib.unified_diff(old_content.splitlines(), new_content.splitlines(), lineterm=""))
        return FileDiff(path=rel_path, change_type="modified", old_content=old_content, new_content=new_content, diff=diff)

    def rollback(self, checkpoint_id: str) -> dict[str, Any]:
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            return {"success": False, "error": "Checkpoint not found"}
        try:
            from git.operations import git_reset_hard
            result = git_reset_hard(checkpoint.git_ref, str(self._base_dir / checkpoint.project))
            return {"success": True, "result": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def delete(self, project: str, rel_path: str) -> dict[str, Any]:
        try:
            path = self._resolve(project, rel_path)
            if path.exists():
                path.unlink()
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


file_editor = FileEditor

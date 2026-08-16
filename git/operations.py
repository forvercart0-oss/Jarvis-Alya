"""Git operations for JARVIS Phase 2."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def git_log(repo_path: str, limit: int = 20) -> list[dict[str, Any]]:
    path = str(Path(repo_path).resolve())
    try:
        proc = _run(["git", "log", f"-{limit}", "--oneline", "--decorate"], path)
        if proc.returncode != 0:
            return [{"error": proc.stderr.strip()}]
        commits = []
        for line in proc.stdout.splitlines():
            parts = line.split(" ", 1)
            commits.append({"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""})
        return commits
    except Exception as exc:
        return [{"error": str(exc)}]


def git_branch(repo_path: str) -> dict[str, Any]:
    path = str(Path(repo_path).resolve())
    try:
        proc = _run(["git", "branch", "-a"], path)
        if proc.returncode != 0:
            return {"error": proc.stderr.strip()}
        branches = [b.strip().lstrip("* ").strip() for b in proc.stdout.splitlines() if b.strip()]
        current = next((b.lstrip("* ").strip() for b in proc.stdout.splitlines() if b.startswith("*")), None)
        return {"current": current, "all": branches}
    except Exception as exc:
        return {"error": str(exc)}


def git_add(repo_path: str, files: list[str]) -> dict[str, Any]:
    path = str(Path(repo_path).resolve())
    try:
        proc = _run(["git", "add", *files], path)
        return {"success": proc.returncode == 0, "output": proc.stdout.strip(), "error": proc.stderr.strip() or None}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def git_commit(repo_path: str, message: str) -> dict[str, Any]:
    path = str(Path(repo_path).resolve())
    try:
        proc = _run(["git", "commit", "-m", message], path)
        return {"success": proc.returncode == 0, "output": proc.stdout.strip(), "error": proc.stderr.strip() or None}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

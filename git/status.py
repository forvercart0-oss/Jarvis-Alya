"""Git status detection for JARVIS Phase 2."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GitStatus:
    path: str
    branch: str | None = None
    ahead: int = 0
    behind: int = 0
    modified: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    clean: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "branch": self.branch,
            "ahead": self.ahead,
            "behind": self.behind,
            "modified": self.modified,
            "added": self.added,
            "deleted": self.deleted,
            "untracked": self.untracked,
            "clean": self.clean,
            "error": self.error,
        }


def _run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def get_status(repo_path: str) -> GitStatus:
    path = str(Path(repo_path).resolve())
    try:
        proc = _run(["git", "status", "--porcelain", "-b"], path)
        if proc.returncode != 0:
            return GitStatus(path=path, error=proc.stderr.strip() or "Not a git repository")

        status = GitStatus(path=path)
        for line in proc.stdout.splitlines():
            if line.startswith("##"):
                status.branch = line[3:].split("...")[0].strip()
            elif len(line) >= 4:
                kind = line[:2].strip()
                file_path = line[3:]
                if kind == "M":
                    status.modified.append(file_path)
                elif kind == "A":
                    status.added.append(file_path)
                elif kind == "D":
                    status.deleted.append(file_path)
                elif kind == "??":
                    status.untracked.append(file_path)

        status.clean = not (status.modified or status.added or status.deleted or status.untracked)
        return status
    except FileNotFoundError:
        return GitStatus(path=path, error="Git not installed.")
    except subprocess.TimeoutExpired:
        return GitStatus(path=path, error="Git command timed out.")
    except Exception as exc:
        return GitStatus(path=path, error=str(exc))

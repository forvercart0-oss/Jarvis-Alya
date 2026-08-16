"""Git diff utilities for JARVIS Phase 2."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FileDiff:
    path: str
    old_path: str | None = None
    added: bool = False
    deleted: bool = False
    renamed: bool = False
    hunks: list[dict[str, Any]] = None

    def __post_init__(self):
        if self.hunks is None:
            self.hunks = []


def _run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def get_diff(repo_path: str, target: str = "") -> list[FileDiff]:
    path = str(Path(repo_path).resolve())
    try:
        args = ["git", "diff", "--no-color"]
        if target:
            args.append(target)
        proc = _run(args, path)
        if proc.returncode != 0:
            return [FileDiff(path="", hunks=[{"error": proc.stderr.strip()}])]
        return _parse_diff(proc.stdout)
    except Exception as exc:
        return [FileDiff(path="", hunks=[{"error": str(exc)}])]


def get_diff_staged(repo_path: str) -> list[FileDiff]:
    path = str(Path(repo_path).resolve())
    try:
        proc = _run(["git", "diff", "--cached", "--no-color"], path)
        if proc.returncode != 0:
            return [FileDiff(path="", hunks=[{"error": proc.stderr.strip()}])]
        return _parse_diff(proc.stdout)
    except Exception as exc:
        return [FileDiff(path="", hunks=[{"error": str(exc)}])]


def _parse_diff(text: str) -> list[FileDiff]:
    diffs: list[FileDiff] = []
    current: FileDiff | None = None
    current_hunk: dict[str, Any] | None = None

    for line in text.splitlines():
        if line.startswith("diff --git "):
            if current:
                diffs.append(current)
            parts = line.split(" ")
            old_path = parts[2][2:] if len(parts) > 2 else ""
            new_path = parts[3][2:] if len(parts) > 3 else ""
            current = FileDiff(path=new_path, old_path=old_path)
            current_hunk = None
        elif line.startswith("rename from ") or line.startswith("rename to "):
            if current:
                current.renamed = True
        elif line.startswith("new file mode"):
            if current:
                current.added = True
        elif line.startswith("deleted file mode"):
            if current:
                current.deleted = True
        elif line.startswith("@@"):
            if current:
                current_hunk = {"header": line, "lines": []}
                current.hunks.append(current_hunk)
        elif current_hunk is not None:
            current_hunk["lines"].append(line)

    if current:
        diffs.append(current)
    return diffs

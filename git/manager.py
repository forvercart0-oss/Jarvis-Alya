"""Git manager facade for JARVIS Phase 2."""

from __future__ import annotations

from typing import Any

from git.diff import get_diff, get_diff_staged
from git.operations import git_add, git_branch, git_commit, git_log
from git.status import get_status


class GitManager:
    def __init__(self):
        pass

    def status(self, repo_path: str) -> dict[str, Any]:
        return get_status(repo_path).to_dict()

    def diff(self, repo_path: str, target: str = "") -> list[dict[str, Any]]:
        diffs = get_diff(repo_path, target)
        return [d.__dict__ for d in diffs]

    def diff_staged(self, repo_path: str) -> list[dict[str, Any]]:
        diffs = get_diff_staged(repo_path)
        return [d.__dict__ for d in diffs]

    def log(self, repo_path: str, limit: int = 20) -> list[dict[str, Any]]:
        return git_log(repo_path, limit=limit)

    def branch(self, repo_path: str) -> dict[str, Any]:
        return git_branch(repo_path)

    def add(self, repo_path: str, files: list[str]) -> dict[str, Any]:
        return git_add(repo_path, files)

    def commit(self, repo_path: str, message: str) -> dict[str, Any]:
        return git_commit(repo_path, message)

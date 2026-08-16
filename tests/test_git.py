"""Tests for the Phase 2 Git system."""

from __future__ import annotations

import pytest

from git.status import get_status
from git.diff import get_diff, get_diff_staged
from git.operations import git_log, git_branch, git_add, git_commit
from git.manager import GitManager


@pytest.fixture
def git_manager():
    return GitManager()


def test_git_manager_initializes():
    mgr = GitManager()
    assert mgr is not None


def test_git_status_outside_repo(tmp_path):
    status = get_status(str(tmp_path))
    assert status.error is not None


def test_git_log_outside_repo(tmp_path):
    result = git_log(str(tmp_path))
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "error" in result[0]


def test_git_branch_outside_repo(tmp_path):
    result = git_branch(str(tmp_path))
    assert "error" in result


def test_git_add_outside_repo(tmp_path):
    result = git_add(str(tmp_path), ["file.txt"])
    assert result["success"] is False


def test_git_commit_outside_repo(tmp_path):
    result = git_commit(str(tmp_path), "test")
    assert result["success"] is False


def test_get_diff_outside_repo(tmp_path):
    diffs = get_diff(str(tmp_path))
    assert isinstance(diffs, list)
    assert len(diffs) >= 1


def test_get_diff_staged_outside_repo(tmp_path):
    diffs = get_diff_staged(str(tmp_path))
    assert isinstance(diffs, list)

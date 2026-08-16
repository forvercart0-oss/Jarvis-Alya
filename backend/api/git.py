"""Git API for JARVIS 2.0 Phase 2."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from git.manager import GitManager

router = APIRouter()
git_manager = GitManager()


class GitCommitRequest(BaseModel):
    message: str


@router.get("/git/status")
async def git_status(path: str):
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    return git_manager.status(path)


@router.get("/git/diff")
async def git_diff(path: str, target: str = ""):
    return git_manager.diff(path, target)


@router.get("/git/diff/staged")
async def git_diff_staged(path: str):
    return git_manager.diff_staged(path)


@router.get("/git/log")
async def git_log(path: str, limit: int = 20):
    return git_manager.log(path, limit=limit)


@router.get("/git/branch")
async def git_branch(path: str):
    return git_manager.branch(path)


@router.post("/git/add")
async def git_add(path: str, files: list[str]):
    return git_manager.add(path, files)


@router.post("/git/commit")
async def git_commit(path: str, body: GitCommitRequest):
    return git_manager.commit(path, body.message)

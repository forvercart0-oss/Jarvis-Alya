"""Coding Phase 27 API routes for JARVIS."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ws_manager import ws_manager
from coding.agent import CodingAgent
from coding.debugger import debugger
from coding.repository_analyzer import RepositoryAnalyzer
from coding.secret_scanner import secret_scanner

logger = logging.getLogger("jarvis.api.coding")

router = APIRouter(prefix="/coding", tags=["coding"])

_base_dir = Path(__import__("config.settings", fromlist=["get_settings"]).get_settings().data_dir) / "projects"
_coding_agent = CodingAgent(_base_dir)


def _inject_memory():
    try:
        from backend.main import memory_manager
        _coding_agent.set_memory(memory_manager)
    except Exception:
        pass


class CodingGoalRequest(BaseModel):
    goal: str
    project: str = ""


class CodeReviewRequest(BaseModel):
    project: str
    path: str | None = None


@router.get("/projects")
async def list_coding_projects():
    try:
        from tools.projects import ListProjectsTool
        tool = ListProjectsTool()
        result = await tool.execute()
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects")
async def create_coding_project(request: dict):
    try:
        from tools.projects import CreateProjectTool
        tool = CreateProjectTool()
        result = await tool.execute(**request)
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/projects/{name}")
async def delete_coding_project(name: str):
    try:
        from tools.projects import DeleteProjectTool
        tool = DeleteProjectTool()
        result = await tool.execute(name=name, confirmed=True)
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/projects/{name}/files")
async def list_project_files(name: str):
    try:
        from tools.projects import ListProjectFilesTool
        tool = ListProjectFilesTool()
        result = await tool.execute(name=name)
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/projects/{name}/files/{path:path}")
async def read_project_file(name: str, path: str):
    try:
        from tools.projects import ReadProjectFileTool
        tool = ReadProjectFileTool()
        result = await tool.execute(name=name, path=path)
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/projects/{name}/files/{path:path}")
async def write_project_file(name: str, path: str, request: dict):
    try:
        from tools.projects import WriteProjectFileTool
        tool = WriteProjectFileTool()
        content = request.get("content", "")
        result = await tool.execute(name=name, path=path, content=content)
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/analyze")
async def analyze_project(name: str):
    try:
        analyzer = RepositoryAnalyzer(_base_dir)
        import asyncio
        info = asyncio.run(analyzer.analyze(str(_base_dir / name)))
        return {"success": True, "project": info.to_dict()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/projects/{name}/index")
async def get_project_index(name: str):
    try:
        _inject_memory()
        result = _coding_agent.get_index(name)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/task")
async def create_coding_task(name: str, request: CodingGoalRequest):
    try:
        _inject_memory()
        task = await _coding_agent.execute_goal(request.goal, name)
        await ws_manager.broadcast("coding_task_started", {"goal": request.goal, "project": name})
        return task
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/run")
async def run_project_command(name: str, request: dict):
    try:
        from tools.projects import RunProjectCommandTool
        tool = RunProjectCommandTool()
        result = await tool.execute(name=name, command=request.get("command", ""))
        return result._data if hasattr(result, "_data") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/test")
async def run_project_tests(name: str, request: dict | None = None):
    try:
        result = await _coding_agent._tester.run(name)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/debug")
async def debug_project(name: str, request: dict):
    try:
        output = request.get("output", "")
        result = debugger.parse_traceback(output)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/projects/{name}/git/status")
async def git_status(name: str):
    try:
        result = _coding_agent._git.status(name)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/projects/{name}/git/log")
async def git_log(name: str, limit: int = 20):
    try:
        result = _coding_agent._git.log(name, limit=limit)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/git/commit")
async def git_commit(name: str, request: dict):
    try:
        result = _coding_agent._git.commit(name, request.get("message", ""), request.get("files"))
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/git/branch")
async def git_create_branch(name: str, request: dict):
    try:
        result = _coding_agent._git.create_branch(name, request.get("branch_name", ""))
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/projects/{name}/secrets/scan")
async def scan_secrets(name: str):
    try:
        from pathlib import Path
        findings = secret_scanner.scan_directory(Path(name))
        return {"success": True, "findings": findings, "count": len(findings)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

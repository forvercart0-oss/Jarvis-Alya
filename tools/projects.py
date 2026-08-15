"""Project builder / coding agent tools.

Projects are sandboxed under ``data/projects`` so the coding agent can only
touch files it is allowed to create. Terminal access from a project is scoped
to that project's directory.
"""

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from config.settings import get_settings
from tools.registry import ToolResult

_PROJECTS_DIR = Path(get_settings().data_dir) / "projects"

_UNSAFE_RE = re.compile(
    r"(rm\s+-rf|rm\s+-fr|mkfs|dd\s+of=.*/dev|:\(\)|fork\s*bomb|"
    r"wipefs|shred|>.*/dev/(sda|sdb|nvme)|curl.*\|\s*(sudo\s+)?(sh|bash)|"
    r"wget.*\|\s*(sudo\s+)?(sh|bash)|git\s+clone.*\|\s*(sudo\s+)?(sh|bash))",
    re.IGNORECASE,
)


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    return slug or "project"


def _project_path(name: str) -> Path:
    safe = _slug(name)
    path = (_PROJECTS_DIR / safe).resolve()
    if not path.is_relative_to(_PROJECTS_DIR.resolve()):
        raise ValueError("Invalid project path.")
    return path


def _read_allowed(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Path escapes the project directory.")
    return path


class ProjectBaseTool:
    def _ensure_dir(self):
        _PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


class ListProjectsTool(ProjectBaseTool):
    name = "list_projects"
    description = "List all JARVIS coding projects with metadata."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        self._ensure_dir()
        projects = []
        for entry in sorted(_PROJECTS_DIR.iterdir()):
            if not entry.is_dir():
                continue
            meta = {"name": entry.name, "files": 0, "updated": None, "stack": None}
            meta_file = entry / ".jarvis.json"
            if meta_file.exists():
                try:
                    meta.update(json.loads(meta_file.read_text()))
                except Exception:
                    pass
            meta["files"] = sum(1 for _ in entry.rglob("*") if _.is_file() and not _.name.startswith("."))
            if meta["updated"] is None:
                try:
                    mtime = os.path.getmtime(meta_file if meta_file.exists() else entry)
                    meta["updated"] = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
                except OSError:
                    pass
            projects.append(meta)
        return ToolResult(success=True, result={"projects": projects, "base_dir": str(_PROJECTS_DIR)})


class CreateProjectTool(ProjectBaseTool):
    name = "create_project"
    description = "Create a new JARVIS coding project with an optional stack and description."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Project name"},
            "description": {"type": "string", "description": "Optional description"},
            "stack": {"type": "string", "description": "Optional tech stack hint, e.g. 'python fastapi'"},
            "init_files": {"type": "array", "items": {"type": "string"}, "description": "Optional starter files to create"},
        },
        "required": ["name"],
    }

    async def execute(self, name: str, description: str = "", stack: str = "", init_files: list = None, **kwargs) -> ToolResult:
        self._ensure_dir()
        path = _project_path(name)
        if path.exists():
            return ToolResult(success=False, error=f"Project '{name}' already exists.")
        path.mkdir(parents=True)
        meta = {
            "name": name,
            "slug": path.name,
            "description": description,
            "stack": stack,
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        (path / ".jarvis.json").write_text(json.dumps(meta, indent=2))
        for rel in init_files or []:
            f = _read_allowed(path, rel)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("")
        return ToolResult(success=True, result={"project": meta, "path": str(path)})


class DeleteProjectTool(ProjectBaseTool):
    name = "delete_project"
    description = "Delete a JARVIS coding project and all of its files."
    parameters = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }

    async def execute(self, name: str, confirmed: bool = False, **kwargs) -> ToolResult:
        path = _project_path(name)
        if not path.exists():
            return ToolResult(success=False, error=f"Project '{name}' not found.")
        if not confirmed:
            return ToolResult(success=False, confirmation_required=True, confirmation_message=f"Delete the entire project '{name}' and all its files, Sir?")
        import shutil

        shutil.rmtree(path, ignore_errors=True)
        return ToolResult(success=True, result={"deleted": name})


class ListProjectFilesTool(ProjectBaseTool):
    name = "list_project_files"
    description = "List all files in a JARVIS coding project."
    parameters = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }

    async def execute(self, name: str, **kwargs) -> ToolResult:
        path = _project_path(name)
        if not path.exists():
            return ToolResult(success=False, error=f"Project '{name}' not found.")
        files = []
        for f in sorted(path.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                files.append({"path": str(f.relative_to(path)), "size": f.stat().st_size})
        return ToolResult(success=True, result={"project": name, "files": files})


class ReadProjectFileTool(ProjectBaseTool):
    name = "read_project_file"
    description = "Read a file from a JARVIS coding project."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "path": {"type": "string", "description": "Path relative to project root"},
        },
        "required": ["name", "path"],
    }

    async def execute(self, name: str, path: str, **kwargs) -> ToolResult:
        root = _project_path(name)
        if not root.exists():
            return ToolResult(success=False, error=f"Project '{name}' not found.")
        try:
            target = _read_allowed(root, path)
        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))
        if not target.exists():
            return ToolResult(success=False, error=f"File '{path}' not found.")
        try:
            content = target.read_text(errors="replace")
            return ToolResult(success=True, result={"path": path, "content": content, "size": len(content)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class WriteProjectFileTool(ProjectBaseTool):
    name = "write_project_file"
    description = "Create or overwrite a file inside a JARVIS coding project."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "path": {"type": "string", "description": "Path relative to project root"},
            "content": {"type": "string"},
        },
        "required": ["name", "path", "content"],
    }

    async def execute(self, name: str, path: str, content: str, **kwargs) -> ToolResult:
        root = _project_path(name)
        if not root.exists():
            return ToolResult(success=False, error=f"Project '{name}' not found.")
        try:
            target = _read_allowed(root, path)
        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            meta_file = root / ".jarvis.json"
            try:
                meta = json.loads(meta_file.read_text())
                meta["updated"] = datetime.now(timezone.utc).isoformat()
                meta_file.write_text(json.dumps(meta, indent=2))
            except Exception:
                pass
            return ToolResult(success=True, result={"path": path, "written": True})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class RunProjectCommandTool(ProjectBaseTool):
    name = "run_project_command"
    description = "Run a terminal command scoped inside a JARVIS coding project directory."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "command": {"type": "string", "description": "Shell command (runs with the project dir as cwd)"},
        },
        "required": ["name", "command"],
    }

    async def execute(self, name: str, command: str, **kwargs) -> ToolResult:
        root = _project_path(name)
        if not root.exists():
            return ToolResult(success=False, error=f"Project '{name}' not found.")
        if _UNSAFE_RE.search(command):
            return ToolResult(success=False, error="Command blocked: potentially destructive pattern detected.")
        try:
            result = subprocess.run(
                ["bash", "-lc", command],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
            return ToolResult(success=True, result={
                "exit_code": result.returncode,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-2000:],
            })
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Command timed out after 180 seconds.")
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

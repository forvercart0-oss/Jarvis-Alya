import os
from pathlib import Path
from typing import Optional
from tools.registry import ToolResult


PROTECTED_DIRS = {"/", "/etc", "/boot", "/root", "/usr", "/bin", "/sbin", "/lib", "/lib64"}


def normalize_path(path: str) -> str:
    return str(Path(path).resolve())


def is_protected(path: str) -> bool:
    resolved = normalize_path(path)
    for p in PROTECTED_DIRS:
        if resolved == p or resolved.startswith(p + os.sep):
            return True
    return False


class ReadFileTool:
    name = "read_file"
    description = "Read a text file."
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Path to the file"}},
        "required": ["path"],
    }

    async def execute(self, path: str, **kwargs) -> ToolResult:
        if is_protected(path):
            return ToolResult(success=False, error="Access to this protected path is restricted for safety.")
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            if len(text) > 5000:
                text = text[:5000] + "\n... [truncated]"
            return ToolResult(success=True, content=text)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class WriteFileTool:
    name = "write_file"
    description = "Create or overwrite a text file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str, content: str, **kwargs) -> ToolResult:
        if is_protected(path):
            return ToolResult(success=False, error="Access to this protected path is restricted for safety.")
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return ToolResult(success=True, result=f"File created at {path}.")
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class DeleteFileTool:
    name = "delete_file"
    description = "Delete a file."
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    async def execute(self, path: str, confirmed: bool = False, **kwargs) -> ToolResult:
        if is_protected(path):
            if not confirmed:
                return ToolResult(success=False, confirmation_required=True, confirmation_message=f"Confirm deletion of protected path: {path}")
            try:
                p = Path(path)
                if p.is_dir():
                    import shutil as _shutil
                    _shutil.rmtree(p)
                else:
                    p.unlink()
                return ToolResult(success=True, result=f"Deleted {path}.")
            except Exception as exc:
                return ToolResult(success=False, error=str(exc))
        if not confirmed:
            return ToolResult(success=False, confirmation_required=True, confirmation_message=f"Confirm deletion of {path}")
        try:
            p = Path(path)
            if not p.exists():
                return ToolResult(success=False, error=f"No such file: {path}")
            if p.is_dir():
                import shutil as _shutil
                _shutil.rmtree(p)
            else:
                p.unlink()
            return ToolResult(success=True, result=f"Deleted {path}.")
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

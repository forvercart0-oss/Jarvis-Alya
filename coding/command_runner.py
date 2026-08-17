"""Command runner for JARVIS Phase 27."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.coding.command_runner")


class CommandRunner:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._processes: dict[str, subprocess.Popen] = {}

    async def run(self, command: str, project: str, timeout: int = 180) -> dict[str, Any]:
        root = self._base_dir / project
        if not root.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[-4000:],
                "stderr": stderr.decode(errors="replace")[-2000:],
            }
        except TimeoutError:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def cancel(self, command_id: str) -> dict[str, Any]:
        proc = self._processes.pop(command_id, None)
        if proc:
            try:
                proc.terminate()
                return {"success": True, "cancelled": command_id}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": False, "error": "Process not found"}


command_runner = CommandRunner

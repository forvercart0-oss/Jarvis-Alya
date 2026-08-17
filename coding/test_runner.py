"""Test runner for JARVIS Phase 27."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.coding.test_runner")


class TestRunner:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir

    async def run(self, project: str, framework: str = "pytest") -> dict[str, Any]:
        root = self._base_dir / project
        if not root.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        commands = {
            "pytest": "python -m pytest -v",
            "jest": "npx jest",
            "mocha": "npx mocha",
            "go": "go test ./...",
            "cargo": "cargo test",
        }
        command = commands.get(framework, "python -m pytest -v")
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            return {
                "success": proc.returncode == 0,
                "framework": framework,
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[-4000:],
                "stderr": stderr.decode(errors="replace")[-2000:],
            }
        except TimeoutError:
            return {"success": False, "error": "Tests timed out after 300s"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def run_specific(self, project: str, test_path: str, framework: str = "pytest") -> dict[str, Any]:
        root = self._base_dir / project
        if not root.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        commands = {
            "pytest": f"python -m pytest -v {test_path}",
            "jest": f"npx jest {test_path}",
            "mocha": f"npx mocha {test_path}",
        }
        command = commands.get(framework, f"python -m pytest -v {test_path}")
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            return {
                "success": proc.returncode == 0,
                "framework": framework,
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[-4000:],
                "stderr": stderr.decode(errors="replace")[-2000:],
            }
        except TimeoutError:
            return {"success": False, "error": "Test timed out after 120s"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


test_runner = TestRunner

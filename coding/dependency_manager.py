"""Dependency manager for JARVIS Phase 27."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.coding.dependency_manager")


class DependencyManager:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._managers = {
            "package.json": "npm",
            "package-lock.json": "npm",
            "yarn.lock": "yarn",
            "pnpm-lock.yaml": "pnpm",
            "bun.lock": "bun",
            "requirements.txt": "pip",
            "pyproject.toml": "pip/uv",
            "Pipfile": "pipenv",
            "Cargo.toml": "cargo",
            "go.mod": "go",
        }

    def detect_package_manager(self, project: str) -> str:
        root = self._base_dir / project
        for indicator, manager in self._managers.items():
            if (root / indicator).exists():
                return manager
        return "unknown"

    def install(self, project: str, packages: list[str] | None = None) -> dict[str, Any]:
        manager = self.detect_package_manager(project)
        root = self._base_dir / project
        if not root.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        commands = {
            "npm": ["npm", "install"] + (packages or []),
            "yarn": ["yarn"] + (packages or []),
            "pnpm": ["pnpm", "install"] + (packages or []),
            "bun": ["bun", "install"] + (packages or []),
            "pip": ["pip", "install"] + (packages or []),
            "pip/uv": ["uv", "pip", "install"] + (packages or []),
            "pipenv": ["pipenv", "install"] + (packages or []),
            "cargo": ["cargo", "add"] + (packages or []),
            "go": ["go", "get"] + (packages or []),
        }
        command = commands.get(manager)
        if not command:
            return {"success": False, "error": f"Unknown package manager: {manager}"}
        try:
            import asyncio
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)
            return {
                "success": proc.returncode == 0,
                "manager": manager,
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[-2000:],
                "stderr": stderr.decode(errors="replace")[-1000:],
            }
        except TimeoutError:
            return {"success": False, "error": "Installation timed out"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def check_missing(self, project: str) -> dict[str, Any]:
        root = self._base_dir / project
        if not root.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        missing = []
        try:
            import asyncio
            manager = self.detect_package_manager(project)
            if manager == "pip":
                proc = await asyncio.create_subprocess_shell("pip check", cwd=str(root), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                if proc.returncode != 0:
                    missing.extend(stdout.decode(errors="replace").splitlines())
        except Exception as exc:
            return {"success": False, "error": str(exc)}
        return {"success": True, "missing": missing[:20], "manager": manager}


dependency_manager = DependencyManager

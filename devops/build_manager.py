"""Build manager for JARVIS Phase 28."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.devops.build_manager")


class BuildManager:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir

    async def build(self, project: str, build_type: str = "development") -> dict[str, Any]:
        project_path = self._base_dir / project
        if not project_path.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        commands = {
            "frontend": {"npm": "npm run build", "yarn": "yarn build", "pnpm": "pnpm build"},
            "backend": {"python": "python -m build", "pip": "pip install -e ."},
        }
        command = commands.get(build_type, {}).get("npm", "echo 'No build command configured'")
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            return {
                "success": proc.returncode == 0,
                "build_type": build_type,
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[-4000:],
                "stderr": stderr.decode(errors="replace")[-2000:],
            }
        except TimeoutError:
            return {"success": False, "error": "Build timed out after 300s"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


build_manager = BuildManager

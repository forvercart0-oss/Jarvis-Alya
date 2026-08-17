"""Database deployment support for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.database")


class DatabaseDeploymentManager:
    def detect_migrations(self, project_path: str) -> dict[str, Any]:
        path = __import__("pathlib").Path(project_path)
        tools = {
            "alembic": (path / "alembic").exists() or (path / "migrations").exists(),
            "django": (path / "manage.py").exists(),
            "prisma": (path / "prisma" / "migrations").exists(),
            "flyway": (path / "sql").exists(),
            "knex": (path / "knexfile.js").exists() or (path / "knexfile.ts").exists(),
        }
        available = [k for k, v in tools.items() if v]
        return {"success": True, "tools": available, "has_migrations": bool(available)}

    async def run_migrations(self, tool: str, project_path: str, env: str = "development") -> dict[str, Any]:
        commands = {
            "alembic": "alembic upgrade head",
            "django": "python manage.py migrate",
            "prisma": "npx prisma migrate deploy",
            "flyway": "flyway migrate",
            "knex": "npx knex migrate:latest",
        }
        command = commands.get(tool)
        if not command:
            return {"success": False, "error": f"Unknown migration tool: {tool}"}
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode(errors="replace")[-2000:],
                "stderr": stderr.decode(errors="replace")[-1000:],
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def check_backup_capability(self, project_path: str) -> dict[str, Any]:
        backup_tools = {
            "pg_dump": __import__("shutil").which("pg_dump"),
            "mysqldump": __import__("shutil").which("mysqldump"),
            "mongodump": __import__("shutil").which("mongodump"),
        }
        available = [k for k, v in backup_tools.items() if v]
        return {"success": True, "available": available, "configured": bool(available)}


database_manager = DatabaseDeploymentManager()

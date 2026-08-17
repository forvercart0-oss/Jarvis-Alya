"""Deployment diff and supply chain checks for JARVIS Phase 28."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.devops.deployment_diff")


class DeploymentDiff:
    async def compute(self, old_version: str, new_version: str, project_path: str) -> dict[str, Any]:
        old_path = __import__("pathlib").Path(project_path) / old_version if old_version else None
        new_path = __import__("pathlib").Path(project_path) / new_version if new_version else __import__("pathlib").Path(project_path)
        if not new_path.exists():
            return {"success": False, "error": "New version path does not exist"}
        changes = {
            "files_changed": [],
            "config_changes": [],
            "database_migrations": [],
            "infrastructure_changes": [],
        }
        if old_path and old_path.exists():
            try:
                import asyncio
                proc = await asyncio.create_subprocess_shell(
                    f"git diff --name-only {old_version} {new_version}",
                    cwd=project_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                changes["files_changed"] = stdout.decode(errors="replace").strip().splitlines()
            except Exception as exc:
                logger.debug("Git diff failed: %s", exc)
        return {"success": True, "changes": changes}


class SupplyChainChecker:
    def check_dependencies(self, project_path: str) -> dict[str, Any]:
        path = Path(project_path)
        issues = []
        for lockfile in ["package-lock.json", "requirements.txt", "Pipfile.lock", "go.sum", "Cargo.lock"]:
            if not (path / lockfile).exists():
                issues.append({"type": "missing_lockfile", "file": lockfile})
        return {"success": True, "issues": issues, "secure": len(issues) == 0}


class DeploymentAuditLogger:
    def __init__(self):
        self._logs: list[dict[str, Any]] = []

    def log(self, action: str, environment: str, version: str, commit: str, status: str, user: str = "system") -> None:
        entry = {
            "action": action,
            "environment": environment,
            "version": version,
            "commit": commit,
            "status": status,
            "user": user,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        self._logs.append(entry)
        if len(self._logs) > 1000:
            self._logs = self._logs[-1000:]

    def get_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._logs[-limit:]


deployment_diff = DeploymentDiff()
supply_chain_checker = SupplyChainChecker()
deployment_audit_logger = DeploymentAuditLogger()

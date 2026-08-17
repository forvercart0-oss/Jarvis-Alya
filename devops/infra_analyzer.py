"""Infrastructure analyzer for JARVIS Phase 28."""

from __future__ import annotations

import logging
import platform
import shutil
from pathlib import Path
from typing import Any

from devops.models import ServerInfo

logger = logging.getLogger("jarvis.devops.infra_analyzer")


class InfrastructureAnalyzer:
    def analyze_local(self) -> ServerInfo:
        info = ServerInfo(name="local", host="localhost")
        try:
            info.os = platform.system()
            info.architecture = platform.machine()
            info.cpu = platform.processor() or platform.machine()
            mem = shutil.disk_usage("/")
            info.disk = f"{mem.free / (1024**3):.1f}GB free / {mem.total / (1024**3):.1f}GB total"
        except Exception as exc:
            logger.debug("Local infrastructure analysis failed: %s", exc)
        return info

    def analyze_project(self, project_path: str) -> dict[str, Any]:
        path = Path(project_path)
        if not path.exists():
            return {"success": False, "error": "Project path does not exist"}
        info = {
            "path": str(path),
            "has_dockerfile": (path / "Dockerfile").exists(),
            "has_compose": any(
                (path / f).exists()
                for f in ["docker-compose.yml", "compose.yaml", "docker-compose.yaml"]
            ),
            "has_ci": any(
                (path / f).exists()
                for f in [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"]
            ),
            "has_tests": any((path / d).exists() for d in ["tests", "test"]),
            "has_env": any((path / f).exists() for f in [".env", ".env.example"]),
            "package_managers": [],
        }
        for pm_file in ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "Pipfile"]:
            if (path / pm_file).exists():
                info["package_managers"].append(pm_file)
        return {"success": True, "project": info}


infrastructure_analyzer = InfrastructureAnalyzer()

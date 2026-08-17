"""Container manager for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

from devops.models import ContainerInfo, ContainerStatus

logger = logging.getLogger("jarvis.devops.container_manager")


class ContainerManager:
    def __init__(self):
        self._docker_available = False
        try:
            import shutil
            self._docker_available = shutil.which("docker") is not None
        except Exception:
            logger.debug("Docker detection failed")

    @property
    def available(self) -> bool:
        return self._docker_available

    def list_containers(self) -> list[ContainerInfo]:
        if not self._docker_available:
            return []
        try:
            import subprocess
            format_str = "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", format_str],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return []
            containers = []
            for line in result.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    containers.append(ContainerInfo(
                        name=parts[0],
                        image=parts[1],
                        status=self._parse_status(parts[2]),
                        ports=parts[3].split(",") if len(parts) > 3 else [],
                    ))
            return containers
        except Exception as exc:
            logger.debug("List containers failed: %s", exc)
            return []

    def _parse_status(self, raw: str) -> str:
        lower = raw.lower()
        if "up" in lower:
            return ContainerStatus.RUNNING
        if "restarting" in lower:
            return ContainerStatus.RESTARTING
        if "exited" in lower:
            return ContainerStatus.STOPPED
        return ContainerStatus.PENDING

    def build_image(self, project_path: str, tag: str) -> dict[str, Any]:
        if not self._docker_available:
            return {"success": False, "error": "Docker not available"}
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "build", "-t", tag, project_path],
                capture_output=True,
                text=True,
                check=False,
            )
            return {"success": result.returncode == 0, "stdout": result.stdout[-2000:], "stderr": result.stderr[-1000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def start_service(self, service: str) -> dict[str, Any]:
        if not self._docker_available:
            return {"success": False, "error": "Docker not available"}
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "compose", "up", "-d", service],
                capture_output=True,
                text=True,
                check=False,
            )
            return {"success": result.returncode == 0, "stdout": result.stdout[-2000:], "stderr": result.stderr[-1000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def stop_service(self, service: str) -> dict[str, Any]:
        if not self._docker_available:
            return {"success": False, "error": "Docker not available"}
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "compose", "stop", service],
                capture_output=True,
                text=True,
                check=False,
            )
            return {"success": result.returncode == 0, "stdout": result.stdout[-2000:], "stderr": result.stderr[-1000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_logs(self, service: str, tail: int = 100) -> dict[str, Any]:
        if not self._docker_available:
            return {"success": False, "error": "Docker not available"}
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "compose", "logs", "--tail", str(tail), service],
                capture_output=True,
                text=True,
                check=False,
            )
            return {"success": result.returncode == 0, "logs": result.stdout[-4000:] + result.stderr[-2000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


container_manager = ContainerManager()

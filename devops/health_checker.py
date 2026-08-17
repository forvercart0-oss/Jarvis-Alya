"""Health checker for JARVIS Phase 28."""

from __future__ import annotations

import logging
import socket
from typing import Any

from devops.models import HealthCheck

logger = logging.getLogger("jarvis.devops.health_checker")


class HealthChecker:
    async def check_http(self, target: str, expected_status: int = 200, timeout: int = 10) -> dict[str, Any]:
        try:
            import asyncio
            import urllib.request
            loop = asyncio.get_event_loop()
            def fetch():
                req = urllib.request.Request(target, method="GET")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.status
            status = await loop.run_in_executor(None, fetch)
            return {"success": status == expected_status, "status": status, "expected": expected_status, "type": "http"}
        except Exception as exc:
            return {"success": False, "error": str(exc), "type": "http"}

    async def check_tcp(self, host: str, port: int, timeout: int = 10) -> dict[str, Any]:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            def connect():
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            result = await loop.run_in_executor(None, connect)
            return {"success": result, "type": "tcp", "host": host, "port": port}
        except Exception as exc:
            return {"success": False, "error": str(exc), "type": "tcp"}

    async def check_process(self, process_name: str) -> dict[str, Any]:
        try:
            import psutil
            found = any(proc.name().lower() == process_name.lower() for proc in psutil.process_iter(['name']))
            return {"success": found, "process": process_name, "running": found}
        except Exception as exc:
            return {"success": False, "error": str(exc), "type": "process"}

    async def check_container(self, container_name: str) -> dict[str, Any]:
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return {"success": False, "error": "Container not found", "type": "container"}
            return {"success": True, "container": container_name, "type": "container"}
        except Exception as exc:
            return {"success": False, "error": str(exc), "type": "container"}

    async def run_check(self, check: HealthCheck) -> dict[str, Any]:
        if check.type == "http":
            return await self.check_http(check.target, check.expected_status, check.timeout)
        if check.type == "tcp":
            host, port = check.target.split(":")
            return await self.check_tcp(host, int(port), check.timeout)
        if check.type == "process":
            return await self.check_process(check.target)
        if check.type == "container":
            return await self.check_container(check.target)
        return {"success": False, "error": f"Unknown check type: {check.type}"}


health_checker = HealthChecker()

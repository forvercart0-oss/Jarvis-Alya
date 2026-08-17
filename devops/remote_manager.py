"""SSH and remote server manager for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.remote_manager")


class RemoteServerManager:
    def __init__(self):
        self._servers: dict[str, dict[str, Any]] = {}
        self._ssh_available = False
        try:
            import shutil
            self._ssh_available = shutil.which("ssh") is not None
        except Exception:
            logger.debug("SSH detection failed")

    def register_server(self, name: str, host: str, port: int = 22, username: str = "", **kwargs) -> dict[str, Any]:
        server = {
            "name": name,
            "host": host,
            "port": port,
            "username": username,
            "os": kwargs.get("os", ""),
            "status": "registered",
        }
        self._servers[name] = server
        return {"success": True, "server": server}

    def list_servers(self) -> list[dict[str, Any]]:
        return list(self._servers.values())

    async def health_check(self, name: str) -> dict[str, Any]:
        server = self._servers.get(name)
        if not server:
            return {"success": False, "error": "Server not found"}
        if not self._ssh_available:
            return {"success": False, "error": "SSH not available"}
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                f"ssh -o BatchMode=yes -o ConnectTimeout=5 {server['username']}@{server['host']} echo ok",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            return {"success": proc.returncode == 0, "output": stdout.decode(errors="replace").strip()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def execute(self, name: str, command: str) -> dict[str, Any]:
        server = self._servers.get(name)
        if not server:
            return {"success": False, "error": "Server not found"}
        if not self._ssh_available:
            return {"success": False, "error": "SSH not available"}
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                f"ssh -o BatchMode=yes {server['username']}@{server['host']} {command}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode(errors="replace")[-2000:],
                "stderr": stderr.decode(errors="replace")[-1000:],
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def get_logs(self, name: str, service: str, tail: int = 100) -> dict[str, Any]:
        command = f"journalctl -u {service} -n {tail}" if service else "dmesg | tail -n 50"
        return await self.execute(name, command)


remote_server_manager = RemoteServerManager()

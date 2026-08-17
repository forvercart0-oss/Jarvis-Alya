"""Terminal provider for JARVIS Phase 19."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger("jarvis.computer.terminal")


class TerminalProvider:
    def __init__(self):
        self._processes: dict[str, subprocess.Popen] = {}

    def open_terminal(self, command: str = "") -> dict[str, Any]:
        try:
            if subprocess.run(["which", "gnome-terminal"], capture_output=True).returncode == 0:
                proc = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", command or "bash"])
            elif subprocess.run(["which", "konsole"], capture_output=True).returncode == 0:
                proc = subprocess.Popen(["konsole", "-e", "bash", "-c", command or "bash"])
            elif subprocess.run(["which", "xterm"], capture_output=True).returncode == 0:
                proc = subprocess.Popen(["xterm", "-e", command or "bash"])
            else:
                return {"success": False, "error": "No terminal emulator found"}
            return {"success": True, "pid": proc.pid}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def run_command(self, command: str, timeout: int = 30) -> dict[str, Any]:
        try:
            proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "code": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def classify_command(self, command: str) -> str:
        lower = command.lower().strip()
        dangerous = ["rm -rf", "dd ", "mkfs", "fdisk", "sudo", "su ", "chmod 777", "chown", "kill -9", "pkill", "shutdown", "reboot"]
        sensitive = ["sudo", "apt ", "yum ", "pacman ", "dnf ", "brew ", "pip install", "npm install", "systemctl"]
        if any(d in lower for d in dangerous):
            return "DESTRUCTIVE"
        if any(s in lower for s in sensitive):
            return "SENSITIVE"
        return "SAFE"


terminal_provider = TerminalProvider()

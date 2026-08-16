"""Linux-specific computer control for JARVIS Phase 3."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger("jarvis.computer.linux")


def run_command(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"success": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def open_application(app: str) -> dict[str, Any]:
    return run_command(["xdg-open", app])


def type_text(text: str) -> dict[str, Any]:
    return run_command(["wtype", text])


def take_screenshot(path: str) -> dict[str, Any]:
    return run_command(["gnome-screenshot", "-f", path])


def set_volume(level: int) -> dict[str, Any]:
    return run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"])

"""macOS-specific computer control for JARVIS Phase 3."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger("jarvis.computer.macos")


def run_command(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"success": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def open_application(app: str) -> dict[str, Any]:
    return run_command(["open", "-a", app])


def type_text(text: str) -> dict[str, Any]:
    script = f'tell application "System Events" to keystroke "{text}"'
    return run_command(["osascript", "-e", script])


def take_screenshot(path: str) -> dict[str, Any]:
    return run_command(["screencapture", "-x", path])


def set_volume(level: int) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"set volume output volume {level}"])


def mouse_scroll(x: int, y: int, scroll: str, amount: int = 3) -> dict[str, Any]:
    direction = "down" if scroll == "4" else "up"
    return run_command(["osascript", "-e", f"tell application \"System Events\" to key code {126 if direction == 'up' else 125} using {{option down}}"])


def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"tell application \"System Events\" to drag from {{ {x1}, {y1} }} to {{ {x2}, {y2} }}"])


def keyboard_hotkey(keys: str) -> dict[str, Any]:
    key_map = {"ctrl": "control", "alt": "option", "shift": "shift", "cmd": "command", "win": "command"}
    mapped = [key_map.get(k, k) for k in keys.split("+")]
    return run_command(["osascript", "-e", f"tell application \"System Events\" to keystroke \"\" using {{{', '.join(mapped)}}}"])

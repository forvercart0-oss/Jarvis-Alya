"""macOS-specific computer control for JARVIS Phase 10."""

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


def close_application(app: str) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"tell application \"{app}\" to quit"])


def type_text(text: str) -> dict[str, Any]:
    safe = text.replace('"', '\\"')
    script = f'tell application "System Events" to keystroke "{safe}"'
    return run_command(["osascript", "-e", script])


def keyboard_hotkey(keys: str) -> dict[str, Any]:
    key_map = {"ctrl": "control", "alt": "option", "shift": "shift", "cmd": "command", "win": "command"}
    mapped = [key_map.get(k, k) for k in keys.split("+")]
    return run_command(["osascript", "-e", f"tell application \"System Events\" to keystroke \"\" using {{{', '.join(mapped)}}}"])  # noqa: E501


def keyboard_press(key: str) -> dict[str, Any]:
    key_map = {"ctrl": "control", "alt": "option", "shift": "shift", "cmd": "command", "win": "command"}
    mapped = key_map.get(key, key)
    return run_command(["osascript", "-e", f"tell application \"System Events\" to key code {mapped}"])


def mouse_move(x: int, y: int) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"tell application \"System Events\" to set mouse location to {{{x}, {y}}}"])


def mouse_click(x: int, y: int, button: int = 1) -> dict[str, Any]:
    _btn = "left" if button == 1 else "right" if button == 3 else "middle"
    return run_command(["osascript", "-e", f"tell application \"System Events\" to click at {{{x}, {y}}}"])


def mouse_double_click(x: int, y: int) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"tell application \"System Events\" to double click at {{{x}, {y}}}"])


def mouse_right_click(x: int, y: int) -> dict[str, Any]:
    return mouse_click(x, y, 3)


def mouse_scroll(x: int, y: int, direction: str, amount: int = 3) -> dict[str, Any]:
    direction_map = {"up": "up", "down": "down"}
    dir_val = direction_map.get(direction, "down")
    return run_command(["osascript", "-e", f"tell application \"System Events\" to scroll {dir_val} by {amount}"])


def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"tell application \"System Events\" to drag from {{{x1}, {y1}}} to {{{x2}, {y2}}}"])  # noqa: E501


def take_screenshot(path: str) -> dict[str, Any]:
    return run_command(["screencapture", "-x", path])


def get_cursor_position() -> dict[str, Any]:
    result = run_command(["osascript", "-e", "tell application \"System Events\" to return {x, y} of mouse location"])
    if result.get("success"):
        return {"success": True, "x": 0, "y": 0, "raw": result["stdout"]}
    return result


def get_active_window() -> dict[str, Any]:
    result = run_command(["osascript", "-e", "tell application \"System Events\" to get name of front window of first application process whose frontmost is true"])  # noqa: E501
    if result.get("success"):
        return {"success": True, "title": result["stdout"].strip()}
    return result


def list_windows() -> dict[str, Any]:
    result = run_command(["osascript", "-e", "tell application \"System Events\" to get name of every window of every application process"])  # noqa: E501
    if result.get("success"):
        return {"success": True, "windows": result["stdout"].strip().splitlines()}
    return result


def set_volume(level: int) -> dict[str, Any]:
    return run_command(["osascript", "-e", f"set volume output volume {level}"])

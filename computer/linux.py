"""Linux-specific computer control for JARVIS Phase 10."""

from __future__ import annotations

import logging
import os
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


def detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def open_application(app: str) -> dict[str, Any]:
    if detect_wayland():
        return run_command(["gtk-launch", app])
    return run_command(["xdg-open", app])


def close_application(app: str) -> dict[str, Any]:
    return run_command(["pkill", "-f", app])


def type_text(text: str) -> dict[str, Any]:
    if _has_cmd("wtype"):
        return run_command(["wtype", "-s", "25", text])
    if _has_cmd("ydotool"):
        return run_command(["ydotool", "type", text])
    if _has_cmd("xdotool"):
        return run_command(["xdotool", "type", "--delay", "25", text])
    return {"success": False, "error": "No typing tool available (install wtype or ydotool)."}


def keyboard_hotkey(keys: str) -> dict[str, Any]:
    if _has_cmd("ydotool"):
        return run_command(["ydotool", "key", keys])
    if _has_cmd("xdotool"):
        return run_command(["xdotool", "key", keys])
    return {"success": False, "error": "No hotkey tool available."}


def keyboard_press(key: str) -> dict[str, Any]:
    if _has_cmd("ydotool"):
        return run_command(["ydotool", "key", key])
    if _has_cmd("xdotool"):
        return run_command(["xdotool", "key", key])
    return {"success": False, "error": "No key tool available."}


def mouse_move(x: int, y: int) -> dict[str, Any]:
    if _has_cmd("ydotool"):
        return run_command(["ydotool", "mousemove", "--absolute", str(x), str(y)])
    if _has_cmd("xdotool"):
        return run_command(["xdotool", "mousemove", str(x), str(y)])
    return {"success": False, "error": "No mouse tool available."}


def mouse_click(x: int, y: int, button: int = 1) -> dict[str, Any]:
    if _has_cmd("ydotool"):
        run_command(["ydotool", "mousemove", "--absolute", str(x), str(y)])
        return run_command(["ydotool", "click", str(button)])
    if _has_cmd("xdotool"):
        run_command(["xdotool", "mousemove", str(x), str(y)])
        return run_command(["xdotool", "click", str(button)])
    return {"success": False, "error": "No mouse tool available."}


def mouse_double_click(x: int, y: int) -> dict[str, Any]:
    if _has_cmd("ydotool"):
        run_command(["ydotool", "mousemove", "--absolute", str(x), str(y)])
        run_command(["ydotool", "click", "1"])
        return run_command(["ydotool", "click", "1"])
    if _has_cmd("xdotool"):
        run_command(["xdotool", "mousemove", str(x), str(y)])
        return run_command(["xdotool", "click", "1", "click", "1"])
    return {"success": False, "error": "No mouse tool available."}


def mouse_right_click(x: int, y: int) -> dict[str, Any]:
    return mouse_click(x, y, 3)


def mouse_scroll(x: int, y: int, direction: str, amount: int = 3) -> dict[str, Any]:
    scroll_map = {"up": "4", "down": "5", "left": "6", "right": "7"}
    button = scroll_map.get(direction, "5")
    if _has_cmd("ydotool"):
        run_command(["ydotool", "mousemove", "--absolute", str(x), str(y)])
        return run_command(["ydotool", "click", button * str(amount)])
    if _has_cmd("xdotool"):
        run_command(["xdotool", "mousemove", str(x), str(y)])
        return run_command(["xdotool", "click", button * str(amount)])
    return {"success": False, "error": "No scroll tool available."}


def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
    if _has_cmd("ydotool"):
        run_command(["ydotool", "mousemove", "--absolute", str(x1), str(y1)])
        run_command(["ydotool", "mousedown", "1"])
        return run_command(["ydotool", "mousemove", "--absolute", str(x2), str(y2), "mouseup", "1"])
    if _has_cmd("xdotool"):
        return run_command(["xdotool", "mousemove", str(x1), str(y1), "mousedown", "1", "mousemove", str(x2), str(y2), "mouseup", "1"])
    return {"success": False, "error": "No drag tool available."}


def take_screenshot(path: str) -> dict[str, Any]:
    if detect_wayland():
        if _has_cmd("grim"):
            return run_command(["grim", path])
        if _has_cmd("gnome-screenshot"):
            return run_command(["gnome-screenshot", "-f", path])
    else:
        if _has_cmd("scrot"):
            return run_command(["scrot", path])
        if _has_cmd("gnome-screenshot"):
            return run_command(["gnome-screenshot", "-f", path])
        if _has_cmd("xdotool"):
            return run_command(["xdotool", "getdisplaygeometry"])
    return {"success": False, "error": "No screenshot tool available."}


def get_cursor_position() -> dict[str, Any]:
    if _has_cmd("xdotool") and not detect_wayland():
        result = run_command(["xdotool", "getmouselocation"])
        if result.get("success"):
            parts = result["stdout"].split()
            pos = {}
            for part in parts:
                if ":" in part:
                    k, v = part.split(":")
                    pos[k] = int(v)
            return {"success": True, "x": pos.get("x", 0), "y": pos.get("y", 0)}
    return {"success": False, "error": "Cannot get cursor position on this platform."}


def get_active_window() -> dict[str, Any]:
    if _has_cmd("xdotool") and not detect_wayland():
        result = run_command(["xdotool", "getactivewindow", "getwindowname"])
        if result.get("success"):
            return {"success": True, "title": result["stdout"].strip()}
    if _has_cmd("wmctrl"):
        result = run_command(["wmctrl", "-l", "-G"])
        if result.get("success"):
            lines = result["stdout"].strip().splitlines()
            for line in lines:
                if "*" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        return {"success": True, "title": " ".join(parts[4:])}
    return {"success": False, "error": "Cannot get active window."}


def list_windows() -> dict[str, Any]:
    if _has_cmd("xdotool") and not detect_wayland():
        result = run_command(["xdotool", "search", "--onlyvisible", "--class", ""])
        if result.get("success"):
            return {"success": True, "windows": result["stdout"].strip().splitlines()}
    if _has_cmd("wmctrl"):
        result = run_command(["wmctrl", "-l"])
        if result.get("success"):
            return {"success": True, "windows": result["stdout"].strip().splitlines()}
    return {"success": False, "error": "Cannot list windows."}


def set_volume(level: int) -> dict[str, Any]:
    if _has_cmd("pactl"):
        return run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"])
    return {"success": False, "error": "No volume control available."}


def _has_cmd(cmd: str) -> bool:
    return any(
        os.path.isfile(os.path.join(p, cmd))
        for p in os.environ.get("PATH", "").split(os.pathsep)
        if p
    )

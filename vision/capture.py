"""Screen capture utilities for JARVIS Phase 4."""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import tempfile
from typing import Any

logger = logging.getLogger("jarvis.vision.capture")


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


async def _run(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {"success": False, "error": "Command timed out"}
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "code": proc.returncode,
        }
    except FileNotFoundError:
        return {"success": False, "error": f"Command not found: {cmd[0]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def capture_screen(
    mode: str = "full",
    window: str | None = None,
    region: str | None = None,
    monitor: int | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Capture the screen.

    Modes:
        full       - full screen
        window     - active window
        application- specific application window
        region     - selected region (WxH+X+Y)
        monitor    - specific monitor index
    """
    system = platform.system().lower()

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

    if system == "linux":
        return await _capture_linux(mode, window, region, monitor, output_path)
    elif system == "windows":
        return await _capture_windows(mode, window, region, monitor, output_path)
    elif system == "darwin":
        return await _capture_macos(mode, window, region, monitor, output_path)
    else:
        return {"success": False, "error": f"Unsupported platform: {system}"}


async def _capture_linux(
    mode: str, window: str | None, region: str | None, monitor: int | None, output_path: str
) -> dict[str, Any]:
    wayland = _detect_wayland()

    if wayland:
        if mode == "full":
            if _has_cmd("grim"):
                cmd = ["grim", output_path]
                if monitor is not None:
                    cmd = ["grim", "-g", f"\"{monitor}\"", output_path]
                result = await _run(cmd)
                if result.get("success"):
                    return {"ok": True, "path": output_path, "format": "png", "backend": "grim"}
                return result

            if _has_cmd("gnome-screenshot"):
                result = await _run(["gnome-screenshot", "-f", output_path])
                if result.get("success"):
                    return {"ok": True, "path": output_path, "format": "png", "backend": "gnome-screenshot"}
                return result

            return {"success": False, "error": "No Wayland screen capture tool available (grim, gnome-screenshot)."}

        if mode == "region" and region:
            if _has_cmd("grim"):
                result = await _run(["grim", "-g", region.replace("+", ","), output_path])
                if result.get("success"):
                    return {"ok": True, "path": output_path, "format": "png", "backend": "grim"}
                return result

        if mode == "window" and window:
            if _has_cmd("grim"):
                result = await _run(["grim", "-w", window, output_path])
                if result.get("success"):
                    return {"ok": True, "path": output_path, "format": "png", "backend": "grim"}
                return result

        return {"success": False, "error": "Wayland region/window capture requires grim."}

    if mode == "full":
        if _has_cmd("gnome-screenshot"):
            result = await _run(["gnome-screenshot", "-f", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "gnome-screenshot"}
            return result

        if _has_cmd("scrot"):
            result = await _run(["scrot", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "scrot"}
            return result

        if _has_cmd("import"):
            result = await _run(["import", "-window", "root", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "import"}
            return result

        return {"success": False, "error": "No X11 screen capture tool available."}

    if mode == "region" and region:
        if _has_cmd("gnome-screenshot"):
            result = await _run(["gnome-screenshot", "-a", "-f", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "gnome-screenshot"}
            return result

        if _has_cmd("scrot") and region:
            result = await _run(["scrot", "--select", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "scrot"}
            return result

        if _has_cmd("import"):
            result = await _run(["import", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "import"}
            return result

        return {"success": False, "error": "No X11 region capture tool available."}

    if mode == "window" and window:
        if _has_cmd("gnome-screenshot"):
            result = await _run(["gnome-screenshot", "-w", "-f", output_path])
            if result.get("success"):
                return {"ok": True, "path": output_path, "format": "png", "backend": "gnome-screenshot"}
            return result

        return {"success": False, "error": "Window capture requires gnome-screenshot on X11."}

    if mode == "application" and window:
        return await _capture_linux("window", window, region, monitor, output_path)

    return {"success": False, "error": f"Unsupported capture mode on Linux: {mode}"}


async def _capture_windows(
    mode: str, window: str | None, region: str | None, monitor: int | None, output_path: str
) -> dict[str, Any]:
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(output_path)
        return {"ok": True, "path": output_path, "format": "png", "backend": "pillow"}
    except Exception as exc:
        return {"success": False, "error": f"Windows capture failed: {exc}"}


async def _capture_macos(
    mode: str, window: str | None, region: str | None, monitor: int | None, output_path: str
) -> dict[str, Any]:
    cmd = ["screencapture", "-x", output_path]
    if mode == "window" and window:
        cmd = ["screencapture", "-x", "-l", window, output_path]
    elif mode == "region" and region:
        cmd = ["screencapture", "-x", "-R", region.replace("+", ","), output_path]
    elif mode == "monitor" and monitor is not None:
        cmd = ["screencapture", "-x", "-D", str(monitor), output_path]
    result = await _run(cmd)
    if result.get("success"):
        return {"ok": True, "path": output_path, "format": "png", "backend": "screencapture"}
    return result


def _has_cmd(cmd: str) -> bool:
    return any(
        os.path.isfile(os.path.join(p, cmd))
        for p in os.environ.get("PATH", "").split(os.pathsep)
        if p
    )


async def get_active_window() -> dict[str, Any]:
    """Return info about the currently active window."""
    system = platform.system().lower()

    if system == "linux":
        wayland = _detect_wayland()
        if wayland:
            if _has_cmd("hyprctl"):
                result = await _run(["hyprctl", "activewindow"])
                if result.get("success"):
                    lines = result["stdout"].strip().splitlines()
                    info = {}
                    for line in lines:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            info[k.strip()] = v.strip()
                    return {
                        "app": info.get("class", ""),
                        "title": info.get("title", ""),
                        "x": int(info.get("at", "0,0").split(",")[0] or 0),
                        "y": int(info.get("at", "0,0").split(",")[1] or 0),
                        "width": int(info.get("size", "0,0").split(",")[0] or 0),
                        "height": int(info.get("size", "0,0").split(",")[1] or 0),
                    }
            if _has_cmd("xdotool"):
                result = await _run(["xdotool", "getactivewindow"])
                if result.get("success"):
                    wid = result["stdout"].strip()
                    title_result = await _run(["xdotool", "getwindowname", wid])
                    class_result = await _run(["xdotool", "getwindowclassname", wid])
                    geom_result = await _run(["xdotool", "getwindowgeometry", wid])
                    title = title_result.get("stdout", "").strip() if title_result.get("success") else ""
                    cls = class_result.get("stdout", "").strip() if class_result.get("success") else ""
                    geom = geom_result.get("stdout", "").strip() if geom_result.get("success") else ""
                    pos = ""
                    size = ""
                    for line in geom.splitlines():
                        if "Position" in line:
                            pos = line.split(":", 1)[1].strip() if ":" in line else ""
                        if "Geometry" in line:
                            size = line.split(":", 1)[1].strip() if ":" in line else ""
                    x, y = 0, 0
                    w, h = 0, 0
                    if pos:
                        parts = pos.strip("()").split(",")
                        x, y = int(parts[0]) if len(parts) > 0 else 0, int(parts[1]) if len(parts) > 1 else 0
                    if size:
                        parts = size.strip("()").split("x")
                        w, h = int(parts[0]) if len(parts) > 0 else 0, int(parts[1]) if len(parts) > 1 else 0
                    return {"app": cls, "title": title, "x": x, "y": y, "width": w, "height": h}
            return {"error": "No active window info tool available (hyprctl, xdotool)."}
        if _has_cmd("xdotool"):
            result = await _run(["xdotool", "getactivewindow"])
            if result.get("success"):
                wid = result["stdout"].strip()
                title_result = await _run(["xdotool", "getwindowname", wid])
                class_result = await _run(["xdotool", "getwindowclassname", wid])
                title = title_result.get("stdout", "").strip() if title_result.get("success") else ""
                cls = class_result.get("stdout", "").strip() if class_result.get("success") else ""
                return {"app": cls, "title": title, "x": 0, "y": 0, "width": 0, "height": 0}
        return {"error": "No active window info tool available (xdotool)."}

    if system == "windows":
        try:
            import win32gui
            import win32process
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            return {
                "app": str(pid),
                "title": title,
                "x": rect[0],
                "y": rect[1],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1],
            }
        except Exception as exc:
            return {"error": f"Windows active window failed: {exc}"}

    if system == "darwin":
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        result = await _run(["osascript", "-e", script])
        if result.get("success"):
            return {"app": result["stdout"].strip(), "title": "", "x": 0, "y": 0, "width": 0, "height": 0}
        return result

    return {"error": f"Unsupported platform: {system}"}


async def get_screen_info() -> dict[str, Any]:
    """Return screen dimensions."""
    system = platform.system().lower()

    if system == "linux":
        if _detect_wayland():
            if _has_cmd("grim"):
                result = await _run(["grim", "-g", "all", "-"])
                if result.get("success"):
                    return {"width": 0, "height": 0, "backend": "grim"}
            result = await _run(["xdpyinfo"])
            if result.get("success"):
                for line in result["stdout"].splitlines():
                    if "dimensions:" in line:
                        parts = line.split("dimensions:")[1].strip().split("x")[0].strip().split()
                        w = int(parts[0]) if parts else 0
                        h = int(parts[1]) if len(parts) > 1 else 0
                        return {"width": w, "height": h}
        else:
            result = await _run(["xdpyinfo"])
            if result.get("success"):
                for line in result["stdout"].splitlines():
                    if "dimensions:" in line:
                        parts = line.split("dimensions:")[1].strip().split("x")[0].strip().split()
                        w = int(parts[0]) if parts else 0
                        h = int(parts[1]) if len(parts) > 1 else 0
                        return {"width": w, "height": h}

    if system == "windows":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            return {"width": user32.GetSystemMetrics(0), "height": user32.GetSystemMetrics(1)}
        except Exception:
            pass

    if system == "darwin":
        try:
            from AppKit import NSScreen
            frame = NSScreen.mainScreen().frame()
            return {"width": int(frame.size.width), "height": int(frame.size.height)}
        except Exception:
            pass

    return {"width": 0, "height": 0}


async def list_monitors() -> list[dict[str, Any]]:
    """List available monitors."""
    system = platform.system().lower()

    if system == "linux":
        if _detect_wayland() and _has_cmd("grim"):
            result = await _run(["grim", "-l", "info"])
            if result.get("success"):
                monitors = []
                for line in result["stdout"].splitlines():
                    if ":" in line:
                        name, rest = line.split(":", 1)
                        monitors.append({"name": name.strip(), "info": rest.strip()})
                if monitors:
                    return monitors

        if not _detect_wayland():
            result = await _run(["xrandr", "--query"])
            if result.get("success"):
                monitors = []
                for line in result["stdout"].splitlines():
                    if " connected" in line and "disconnected" not in line:
                        parts = line.split()
                        name = parts[0]
                        monitors.append({"name": name, "info": line.strip()})
                return monitors

    if system == "windows":
        try:
            import win32api
            monitors = []
            i = 0
            while True:
                try:
                    hmon = win32api.EnumDisplayMonitors(None, None)[i]
                    info = win32api.GetMonitorInfo(hmon)
                    monitors.append({"name": f"Monitor {i+1}", "info": str(info)})
                    i += 1
                except IndexError:
                    break
            return monitors
        except Exception:
            pass

    if system == "darwin":
        try:
            from AppKit import NSScreen
            monitors = []
            for i, screen in enumerate(NSScreen.screens()):
                frame = screen.frame()
                monitors.append({
                    "name": f"Display {i+1}",
                    "width": int(frame.size.width),
                    "height": int(frame.size.height),
                    "x": int(frame.origin.x),
                    "y": int(frame.origin.y),
                })
            return monitors
        except Exception:
            pass

    return [{"name": "Primary", "width": 0, "height": 0}]

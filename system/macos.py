"""macOS system platform (osascript / pmset based)."""

from __future__ import annotations

import base64
import platform
import subprocess
from pathlib import Path

from system.base import SystemPlatform


def _osascript(script: str):
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=15,
    )


class MacOSPlatform(SystemPlatform):
    name = "macos"

    async def lock_screen(self) -> dict:
        try:
            _osascript('tell application "System Events" to keystroke "q" using {command down, control down}')
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def shutdown(self) -> dict:
        try:
            subprocess.run(["osascript", "-e", 'tell app "System Events" to shut down'], capture_output=True, timeout=15)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def reboot(self) -> dict:
        try:
            subprocess.run(["osascript", "-e", 'tell app "System Events" to restart'], capture_output=True, timeout=15)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def suspend(self) -> dict:
        try:
            subprocess.run(["pmset", "sleepnow"], capture_output=True, timeout=15)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_volume(self, level: int) -> dict:
        level = max(0, min(100, int(level)))
        try:
            _osascript(f"set volume output volume {level}")
            return {"ok": True, "level": level}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_mute(self, mute: bool) -> dict:
        try:
            _osascript(f"set volume output muted {'true' if mute else 'false'}")
            return {"ok": True, "mute": mute}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def audio_server_status(self) -> dict:
        try:
            result = subprocess.run(
                ["pgrep", "-x", "coreaudiod"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return {"status": "online"}
            return {"status": "offline", "error": "coreaudiod not running"}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    async def open_application(self, app_name: str) -> dict:
        try:
            subprocess.run(["open", "-a", app_name], capture_output=True, timeout=15, check=True)
            return {"ok": True, "application": app_name}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def close_application(self, app_name: str) -> dict:
        try:
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'], capture_output=True, timeout=15)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def screenshot(self, out_path: str, region: str = "") -> dict:
        try:
            subprocess.run(["screencapture", "-x", out_path], capture_output=True, timeout=15, check=True)
            data = base64.b64encode(Path(out_path).read_bytes()).decode()
            return {"ok": True, "format": "png", "data": data}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_brightness(self, level: int) -> dict:
        return {"ok": False, "error": "Brightness control requires brightness binary on macOS"}

    async def set_do_not_disturb(self, enabled: bool) -> dict:
        return {"ok": False, "error": "Do Not Disturb control is not exposed on macOS"}

    async def list_windows(self) -> dict:
        script = 'tell application "System Events" to get name of every window of every process'
        result = _osascript(script)
        if result.returncode == 0:
            return {"success": True, "windows": result.stdout.strip().splitlines()}
        return {"success": False, "error": result.stderr.strip() or "Cannot list windows"}

    async def get_active_window(self) -> dict:
        app_script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        title_script = 'tell application "System Events" to get title of front window of first application process whose frontmost is true'
        app_res = _osascript(app_script)
        title_res = _osascript(title_script)
        return {
            "app": app_res.stdout.strip() if app_res.returncode == 0 else "",
            "title": title_res.stdout.strip() if title_res.returncode == 0 else "",
            "x": 0, "y": 0, "width": 0, "height": 0,
        }

    async def get_screen_info(self) -> dict:
        script = 'tell application "Finder" to get bounds of window of desktop'
        result = _osascript(script)
        if result.returncode == 0:
            try:
                parts = result.stdout.strip().split(", ")
                if len(parts) >= 4:
                    return {"width": int(parts[2]), "height": int(parts[3]), "backend": "osascript"}
            except Exception:
                pass
        return {"width": 0, "height": 0, "backend": "unknown"}

    def info(self) -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

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

    def info(self) -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

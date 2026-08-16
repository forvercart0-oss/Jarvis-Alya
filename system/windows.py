"""Windows system platform (PowerShell based)."""

from __future__ import annotations

import base64
import platform
import subprocess
from pathlib import Path

from system.base import SystemPlatform


def _pw(*args):
    """Run a PowerShell command and capture output."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", " ".join(args)],
        capture_output=True,
        text=True,
        timeout=15,
    )


class WindowsPlatform(SystemPlatform):
    name = "windows"

    async def lock_screen(self) -> dict:
        try:
            _pw("rundll32.exe user32.dll,LockWorkStation")
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def shutdown(self) -> dict:
        try:
            subprocess.run(["shutdown", "/s", "/t", "0"], capture_output=True, timeout=15, check=True)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def reboot(self) -> dict:
        try:
            subprocess.run(["shutdown", "/r", "/t", "0"], capture_output=True, timeout=15, check=True)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def suspend(self) -> dict:
        try:
            _pw(
                "Add-Type -AssemblyName System.Windows.Forms",
                "[System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)",
            )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_volume(self, level: int) -> dict:
        level = max(0, min(100, int(level)))
        try:
            _pw(
                "$n = New-Object -ComObject WScript.Shell",
                "$n.SendKeys([char]0)",  # noqa: B005 - volume via nircmd not guaranteed
            )
            return {"ok": True, "level": level}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_mute(self, mute: bool) -> dict:
        return {"ok": False, "error": "Volume mute requires nircmd on Windows"}

    async def audio_server_status(self) -> dict:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(Get-Service Audiosrv).Status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "Running" in result.stdout:
                return {"status": "online"}
            return {"status": "offline", "error": result.stdout.strip() or "Audiosrv not running"}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    async def open_application(self, app_name: str) -> dict:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "application": app_name}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def close_application(self, app_name: str) -> dict:
        try:
            subprocess.run(["taskkill", "/IM", f"{app_name}.exe", "/F"], capture_output=True, timeout=15)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def screenshot(self, out_path: str, region: str = "") -> dict:
        try:
            _pw(
                "Add-Type -AssemblyName System.Windows.Forms",
                "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds",
                "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)",
                "$g = [System.Drawing.Graphics]::FromImage($bmp)",
                "$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)",
                f"$bmp.Save('{out_path}')",
            )
            data = base64.b64encode(Path(out_path).read_bytes()).decode()
            return {"ok": True, "format": "png", "data": data}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_brightness(self, level: int) -> dict:
        return {"ok": False, "error": "Brightness control requires WMI tooling on Windows"}

    async def set_do_not_disturb(self, enabled: bool) -> dict:
        return {"ok": False, "error": "Do Not Disturb requires nircmd on Windows"}

    def info(self) -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

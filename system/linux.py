"""Linux system platform (systemd, loginctl, wireplumber / pactl, X11/Wayland tools)."""

from __future__ import annotations

import base64
import platform
from pathlib import Path

from system.base import SystemPlatform, run, which


class LinuxPlatform(SystemPlatform):
    name = "linux"

    # -------------------------------------------------------------- power
    async def lock_screen(self) -> dict:
        if which("loginctl"):
            try:
                run(["loginctl", "lock-session"], check=True)
                return {"ok": True}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": "loginctl not available"}

    async def shutdown(self) -> dict:
        try:
            run(["systemctl", "poweroff"], check=True)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def reboot(self) -> dict:
        try:
            run(["systemctl", "reboot"], check=True)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def suspend(self) -> dict:
        try:
            run(["systemctl", "suspend"], check=True)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # -------------------------------------------------------------- audio
    async def set_volume(self, level: int) -> dict:
        level = max(0, min(100, int(level)))
        try:
            if which("wpctl"):
                run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{level / 100.0:.2f}"], check=True)
                return {"ok": True, "level": level}
            if which("pactl"):
                run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"], check=True)
                return {"ok": True, "level": level}
            return {"ok": False, "error": "wpctl/pactl not available"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_mute(self, mute: bool) -> dict:
        try:
            if which("wpctl"):
                run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if mute else "0"], check=True)
                return {"ok": True, "mute": mute}
            if which("pactl"):
                run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if mute else "0"], check=True)
                return {"ok": True, "mute": mute}
            return {"ok": False, "error": "wpctl/pactl not available"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def audio_server_status(self) -> dict:
        try:
            result = run(["pactl", "info"], timeout=5)
            if result.returncode == 0:
                return {"status": "online"}
            return {"status": "offline", "error": "pactl returned non-zero"}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    # -------------------------------------------------------- applications
    async def open_application(self, app_name: str) -> dict:
        exe = which(app_name)
        if not exe:
            return {"ok": False, "error": f"Application '{app_name}' not found."}
        try:
            import subprocess

            subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "application": app_name}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def close_application(self, app_name: str) -> dict:
        exe = which(app_name)
        if not exe:
            return {"ok": False, "error": f"Application '{app_name}' not found."}
        try:
            import subprocess

            subprocess.run(["pkill", "-f", exe], check=True)
            return {"ok": True}
        except subprocess.CalledProcessError:
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # --------------------------------------------------------------- display
    async def screenshot(self, out_path: str, region: str = "") -> dict:
        tool = which("gnome-screenshot", "spectacle", "grim", "scrot", "import", "maim")
        if not tool:
            return {"ok": False, "error": "No screenshot tool found (install grim, spectacle, or scrot)."}
        try:
            cmd = None
            if tool.endswith("grim"):
                cmd = [tool, out_path]
            elif tool.endswith("spectacle"):
                cmd = [tool, "-b", "-n", "-o", out_path]
            elif tool.endswith("gnome-screenshot"):
                cmd = [tool, "-f", out_path]
            elif tool.endswith("scrot"):
                cmd = [tool, out_path]
            elif tool.endswith("maim"):
                cmd = [tool, out_path]
            elif tool.endswith("import"):
                cmd = [tool, "-window", "root", out_path]
            result = run(cmd, timeout=15)
            if result.returncode != 0:
                return {"ok": False, "error": f"Screenshot failed: {result.stderr[:300]}"}
            data = base64.b64encode(Path(out_path).read_bytes()).decode()
            return {"ok": True, "format": "png", "data": data}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_brightness(self, level: int) -> dict:
        if not which("brightnessctl"):
            return {"ok": False, "error": "brightnessctl not found."}
        level = max(0, min(100, int(level)))
        try:
            run(["brightnessctl", "set", f"{level}%"], check=True)
            return {"ok": True, "level": level}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_do_not_disturb(self, enabled: bool) -> dict:
        value = "true" if enabled else "false"
        try:
            run(
                ["qdbus", "org.freedesktop.Notifications", "/org/freedesktop/Notifications", "org.freedesktop.Notifications.NotificationsEnabled", value],
                timeout=5,
            )
            return {"ok": True, "do_not_disturb": enabled}
        except Exception as exc:
            return {"ok": False, "error": f"qdbus not available: {exc}"}

    # ------------------------------------------------------------- identity
    def info(self) -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

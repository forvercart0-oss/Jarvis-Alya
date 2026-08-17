"""Unified computer-control layer for JARVIS Phase 10.

Wraps the OS platform backend and the input controller behind a single,
tool-friendly API. Every method returns a plain dict so tools can attach
extra metadata freely.
"""

from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path

from computer.input import input_controller
from system import get_platform


class ComputerController:
    def __init__(self):
        self.platform = get_platform()
        self.input = input_controller

    # -------------------------------------------------------------- power
    async def lock_screen(self) -> dict:
        return await self.platform.lock_screen()

    async def shutdown(self) -> dict:
        return await self.platform.shutdown()

    async def reboot(self) -> dict:
        return await self.platform.reboot()

    async def suspend(self) -> dict:
        return await self.platform.suspend()

    # -------------------------------------------------------------- audio
    async def set_volume(self, level: int) -> dict:
        return await self.platform.set_volume(level)

    async def set_mute(self, mute: bool) -> dict:
        return await self.platform.set_mute(mute)

    async def audio_server_status(self) -> dict:
        return await self.platform.audio_server_status()

    # -------------------------------------------------------- applications
    async def open_application(self, app_name: str) -> dict:
        return await self.platform.open_application(app_name)

    async def close_application(self, app_name: str) -> dict:
        return await self.platform.close_application(app_name)

    # --------------------------------------------------------------- display
    async def screenshot(self, region: str = "") -> dict:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            out = tmp.name
        try:
            result = await self.platform.screenshot(out, region)
            if not result.get("ok"):
                return result
            return {"format": result.get("format", "png"), "width": 0, "height": 0, "data": result.get("data", "")}
        finally:
            with contextlib.suppress(OSError):
                Path(out).unlink()

    async def set_brightness(self, level: int) -> dict:
        return await self.platform.set_brightness(level)

    async def set_do_not_disturb(self, enabled: bool) -> dict:
        return await self.platform.set_do_not_disturb(enabled)

    # ----------------------------------------------------------------- input
    async def type_text(self, text: str) -> dict:
        return await self.input.type_text(text)

    async def click_at(self, x: int, y: int, button: int = 1) -> dict:
        return await self.input.click_at(x, y, button)

    async def double_click_at(self, x: int, y: int) -> dict:
        return await self.input.double_click_at(x, y)

    async def right_click_at(self, x: int, y: int) -> dict:
        return await self.input.right_click_at(x, y)

    async def mouse_move(self, x: int, y: int) -> dict:
        return await self.input.mouse_move(x, y)

    async def mouse_drag(self, x1: int, y1: int, x2: int, y2: int) -> dict:
        return await self.input.mouse_drag(x1, y1, x2, y2)

    async def mouse_scroll(self, x: int, y: int, direction: str, amount: int = 3) -> dict:
        return await self.input.mouse_scroll(x, y, direction, amount)

    async def press_key(self, key: str) -> dict:
        return await self.input.press_key(key)

    async def hotkey(self, keys: str) -> dict:
        return await self.input.hotkey(keys)

    async def get_cursor_position(self) -> dict:
        return await self.input.get_cursor_position()

    async def get_active_window(self) -> dict:
        return await self.input.get_active_window()

    async def list_windows(self) -> dict:
        return await self.input.list_windows()

    async def focus_window(self, title: str) -> dict:
        return await self.input.focus_window(title)

    async def get_screen_info(self) -> dict:
        return await self.input.get_screen_info()

    async def copy(self) -> dict:
        try:
            import pyperclip
            return {"success": True, "content": pyperclip.paste()}
        except ImportError:
            return await self.hotkey("ctrl+c")

    async def paste(self) -> dict:
        try:
            import pyperclip
            return {"success": True, "content": pyperclip.paste()}
        except ImportError:
            return await self.hotkey("ctrl+v")

    async def minimize_window(self, window_id: str) -> dict:
        return {"success": False, "error": "minimize_window not implemented"}

    async def maximize_window(self, window_id: str) -> dict:
        return {"success": False, "error": "maximize_window not implemented"}

    async def restore_window(self, window_id: str) -> dict:
        return {"success": False, "error": "restore_window not implemented"}

    async def close_window(self, window_id: str) -> dict:
        return {"success": False, "error": "close_window not implemented"}

    async def move_window(self, window_id: str, x: int, y: int) -> dict:
        return {"success": False, "error": "move_window not implemented"}

    async def resize_window(self, window_id: str, width: int, height: int) -> dict:
        return {"success": False, "error": "resize_window not implemented"}

    async def list_processes(self) -> dict:
        if not self._available:
            return {"success": False, "error": "Computer control not available"}
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_percent", "status", "create_time"]
            ):
                try:
                    info = p.info
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "command": " ".join(info.get("cmdline", []) or []),
                        "cpu_percent": info.get("cpu_percent", 0.0),
                        "memory_percent": info.get("memory_percent", 0.0),
                        "status": info.get("status", ""),
                        "start_time": str(info.get("create_time", "")),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return {"success": True, "processes": procs[:100]}
        except ImportError:
            return {"success": False, "error": "psutil not available"}

    async def get_monitors(self) -> dict:
        if not self._available:
            return {"success": False, "error": "Computer control not available"}
        try:
            from vision.capture import list_monitors
            return await list_monitors()
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def run_command(self, command: str, timeout: int = 30) -> dict:
        import subprocess
        try:
            proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return {"success": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "code": proc.returncode}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def list_files(self, path: str = "") -> dict:
        if not path:
            path = str(Path.home())
        try:
            target = Path(path)
            entries = []
            for child in sorted(target.iterdir()):
                try:
                    entries.append({
                        "name": child.name,
                        "path": str(child),
                        "is_dir": child.is_dir(),
                        "size": child.stat().st_size if child.is_file() else 0,
                    })
                except OSError:
                    continue
            return {"success": True, "path": str(target), "entries": entries}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


computer_controller = ComputerController()

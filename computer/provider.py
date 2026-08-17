"""Computer control provider abstraction for JARVIS Phase 19."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.computer.provider")


@dataclass
class WindowInfo:
    window_id: str = ""
    title: str = ""
    application: str = ""
    process: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    state: str = "normal"
    monitor: int = 0
    workspace: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitorInfo:
    index: int = 0
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0
    primary: bool = False
    scale: float = 1.0
    backend: str = ""


@dataclass
class ProcessInfo:
    pid: int = 0
    name: str = ""
    command: str = ""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    status: str = ""
    start_time: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppInfo:
    name: str = ""
    executable: str = ""
    desktop_entry: str = ""
    path: str = ""
    icon: str = ""
    installed: bool = False
    running: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ComputerControlProvider(ABC):
    """Abstract computer control provider."""

    name: str = "base"

    @abstractmethod
    async def move_mouse(self, x: int, y: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def click(self, x: int, y: int, button: int = 1) -> dict[str, Any]:
        pass

    @abstractmethod
    async def double_click(self, x: int, y: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def right_click(self, x: int, y: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def drag(self, x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def scroll(self, x: int, y: int, amount: int, direction: str = "down") -> dict[str, Any]:
        pass

    @abstractmethod
    async def type_text(self, text: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def press_key(self, key: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def hotkey(self, keys: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def copy(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def paste(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def take_screenshot(self, path: str = "", region: str = "") -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_mouse_position(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def list_windows(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_active_window(self) -> WindowInfo:
        pass

    @abstractmethod
    async def focus_window(self, window_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def minimize_window(self, window_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def maximize_window(self, window_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def restore_window(self, window_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def close_window(self, window_id: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def move_window(self, window_id: str, x: int, y: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def resize_window(self, window_id: str, width: int, height: int) -> dict[str, Any]:
        pass

    @abstractmethod
    async def launch_application(self, app: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def close_application(self, app: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def list_processes(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_monitors(self) -> list[MonitorInfo]:
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        pass


class SystemComputerProvider(ComputerControlProvider):
    """Wraps the existing system platform."""

    name = "system"

    def __init__(self):
        from system import get_platform
        self._platform = get_platform()

    async def move_mouse(self, x: int, y: int) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.mouse_move(x, y)

    async def click(self, x: int, y: int, button: int = 1) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.click_at(x, y, button)

    async def double_click(self, x: int, y: int) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.double_click_at(x, y)

    async def right_click(self, x: int, y: int) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.right_click_at(x, y)

    async def drag(self, x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.mouse_drag(x1, y1, x2, y2)

    async def scroll(self, x: int, y: int, amount: int, direction: str = "down") -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.mouse_scroll(x, y, direction, amount)

    async def type_text(self, text: str) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.type_text(text)

    async def press_key(self, key: str) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.press_key(key)

    async def hotkey(self, keys: str) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.hotkey(keys)

    async def copy(self) -> dict[str, Any]:
        try:
            import pyperclip
            return {"success": True, "content": pyperclip.paste()}
        except ImportError:
            return await self.hotkey("ctrl+c")

    async def paste(self) -> dict[str, Any]:
        try:
            import pyperclip
            return {"success": True, "content": pyperclip.paste()}
        except ImportError:
            return await self.hotkey("ctrl+v")

    async def take_screenshot(self, path: str = "", region: str = "") -> dict[str, Any]:
        if not path:
            import tempfile, os
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
        return await self._platform.screenshot(path, region=region)

    async def get_mouse_position(self) -> dict[str, Any]:
        from computer.input import input_controller
        return await input_controller.get_cursor_position()

    async def list_windows(self) -> dict[str, Any]:
        if hasattr(self._platform, "list_windows"):
            return await self._platform.list_windows()
        return {"success": False, "error": "list_windows not supported"}

    async def get_active_window(self) -> WindowInfo:
        if hasattr(self._platform, "get_active_window"):
            data = await self._platform.get_active_window()
            if isinstance(data, dict):
                return WindowInfo(
                    window_id=data.get("window_id", ""),
                    title=data.get("title", ""),
                    application=data.get("app", ""),
                    process=data.get("process", ""),
                    x=data.get("x", 0),
                    y=data.get("y", 0),
                    width=data.get("width", 0),
                    height=data.get("height", 0),
                    state=data.get("state", "normal"),
                    monitor=data.get("monitor", 0),
                    workspace=data.get("workspace", ""),
                    metadata=data,
                )
        return WindowInfo()

    async def focus_window(self, window_id: str) -> dict[str, Any]:
        from computer.input import input_controller
        if hasattr(input_controller, "focus_window"):
            return await input_controller.focus_window(window_id)
        return {"success": False, "error": "focus_window not supported"}

    async def minimize_window(self, window_id: str) -> dict[str, Any]:
        return {"success": False, "error": "minimize_window not implemented"}

    async def maximize_window(self, window_id: str) -> dict[str, Any]:
        return {"success": False, "error": "maximize_window not implemented"}

    async def restore_window(self, window_id: str) -> dict[str, Any]:
        return {"success": False, "error": "restore_window not implemented"}

    async def close_window(self, window_id: str) -> dict[str, Any]:
        return {"success": False, "error": "close_window not implemented"}

    async def move_window(self, window_id: str, x: int, y: int) -> dict[str, Any]:
        return {"success": False, "error": "move_window not implemented"}

    async def resize_window(self, window_id: str, width: int, height: int) -> dict[str, Any]:
        return {"success": False, "error": "resize_window not implemented"}

    async def launch_application(self, app: str) -> dict[str, Any]:
        return await self._platform.open_application(app)

    async def close_application(self, app: str) -> dict[str, Any]:
        return await self._platform.close_application(app)

    async def list_processes(self) -> dict[str, Any]:
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_percent", "status", "create_time"]):
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

    async def get_monitors(self) -> list[MonitorInfo]:
        try:
            from vision.capture import list_monitors
            raw = await list_monitors()
            monitors = []
            for i, m in enumerate(raw.get("monitors", [])):
                monitors.append(MonitorInfo(
                    index=i,
                    width=m.get("width", 0),
                    height=m.get("height", 0),
                    x=m.get("x", 0),
                    y=m.get("y", 0),
                    primary=m.get("primary", i == 0),
                    scale=m.get("scale", 1.0),
                    backend=m.get("backend", ""),
                ))
            return monitors
        except Exception:
            return [MonitorInfo(index=0, width=0, height=0, primary=True)]

    async def health_check(self) -> dict[str, Any]:
        try:
            monitors = await self.get_monitors()
            return {"status": "online", "monitors": len(monitors), "provider": self.name}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}


_computer_provider: SystemComputerProvider | None = None


def get_computer_provider() -> ComputerControlProvider:
    global _computer_provider
    if _computer_provider is None:
        _computer_provider = SystemComputerProvider()
    return _computer_provider

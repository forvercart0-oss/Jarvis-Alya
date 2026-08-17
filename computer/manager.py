"""Computer control manager for JARVIS Phase 10."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from computer.safety import ComputerSafety
from computer.platform import detect_platform

logger = logging.getLogger("jarvis.computer.manager")


class ComputerManager:
    def __init__(self):
        self._safety = ComputerSafety()
        self._available = True
        self._platform = detect_platform()
        self._controller = None

    @property
    def available(self) -> bool:
        return self._available

    def _get_controller(self):
        if self._controller is None:
            from computer.controller import ComputerController
            self._controller = ComputerController()
        return self._controller

    def _run_platform(self, action: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        module = {"linux": "computer.linux", "windows": "computer.windows", "macos": "computer.macos"}.get(self._platform)  # noqa: E501
        if not module:
            return {"success": False, "error": f"Platform {self._platform} not supported"}
        mod = importlib.import_module(module)
        handler = getattr(mod, action, None)
        if not handler:
            return {"success": False, "error": f"Action {action} not implemented for {self._platform}"}
        try:
            if kwargs:
                return handler(**kwargs)
            if args:
                return handler(*args)
            return handler()
        except TypeError:
            return handler()

    async def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._safety.is_allowed(action):
            return {"success": False, "error": "Action not permitted by safety policy."}
        if self._safety.requires_confirmation(action):
            return {"success": False, "confirmation_required": True, "action": action, "arguments": arguments}

        handler = getattr(self, f"_handle_{action}", None)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        return await handler(arguments)

    async def _handle_open_application(self, args: dict[str, Any]) -> dict[str, Any]:
        app = args.get("app", "")
        if not app:
            return {"success": False, "error": "Application name required"}
        return self._run_platform("open_application", app)

    async def _handle_close_application(self, args: dict[str, Any]) -> dict[str, Any]:
        app = args.get("app", "")
        if not app:
            return {"success": False, "error": "Application name required"}
        return self._run_platform("close_application", app)

    async def _handle_type_text(self, args: dict[str, Any]) -> dict[str, Any]:
        text = args.get("text", "")
        if not text:
            return {"success": False, "error": "Text required"}
        return self._run_platform("type_text", text)

    async def _handle_take_screenshot(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "/tmp/jarvis_screenshot.png")
        return self._run_platform("take_screenshot", path)

    async def _handle_set_volume(self, args: dict[str, Any]) -> dict[str, Any]:
        level = args.get("level", 50)
        return self._run_platform("set_volume", level)

    async def _handle_click_at(self, args: dict[str, Any]) -> dict[str, Any]:
        x = args.get("x", 0)
        y = args.get("y", 0)
        button = args.get("button", 1)
        return self._run_platform("mouse_click", x, y, button)

    async def _handle_double_click_at(self, args: dict[str, Any]) -> dict[str, Any]:
        x = args.get("x", 0)
        y = args.get("y", 0)
        return self._run_platform("mouse_double_click", x, y)

    async def _handle_right_click_at(self, args: dict[str, Any]) -> dict[str, Any]:
        x = args.get("x", 0)
        y = args.get("y", 0)
        return self._run_platform("mouse_right_click", x, y)

    async def _handle_mouse_move(self, args: dict[str, Any]) -> dict[str, Any]:
        x = args.get("x", 0)
        y = args.get("y", 0)
        return self._run_platform("mouse_move", x, y)

    async def _handle_mouse_drag(self, args: dict[str, Any]) -> dict[str, Any]:
        x1 = args.get("x1", 0)
        y1 = args.get("y1", 0)
        x2 = args.get("x2", 0)
        y2 = args.get("y2", 0)
        return self._run_platform("mouse_drag", x1, y1, x2, y2)

    async def _handle_mouse_scroll(self, args: dict[str, Any]) -> dict[str, Any]:
        x = args.get("x", 0)
        y = args.get("y", 0)
        direction = args.get("direction", "down")
        amount = args.get("amount", 3)
        return self._run_platform("mouse_scroll", x, y, direction, amount)

    async def _handle_press_key(self, args: dict[str, Any]) -> dict[str, Any]:
        key = args.get("key", "")
        return self._run_platform("keyboard_press", key)

    async def _handle_hotkey(self, args: dict[str, Any]) -> dict[str, Any]:
        keys = args.get("keys", "")
        return self._run_platform("keyboard_hotkey", keys)

    async def _handle_get_cursor_position(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._run_platform("get_cursor_position")

    async def _handle_get_active_window(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._run_platform("get_active_window")

    async def _handle_list_windows(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._run_platform("list_windows")

    async def _handle_focus_window(self, args: dict[str, Any]) -> dict[str, Any]:
        title = args.get("title", "")
        return self._run_platform("focus_window", title)

    async def _handle_get_screen_info(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._run_platform("get_screen_info")

    async def _handle_copy(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self._get_controller().copy()

    async def _handle_paste(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self._get_controller().paste()

    async def _handle_focus_window(self, args: dict[str, Any]) -> dict[str, Any]:
        title = args.get("title", "")
        return self._run_platform("focus_window", title)

    async def _handle_minimize_window(self, args: dict[str, Any]) -> dict[str, Any]:
        window_id = args.get("window_id", "")
        return await self._get_controller().minimize_window(window_id)

    async def _handle_maximize_window(self, args: dict[str, Any]) -> dict[str, Any]:
        window_id = args.get("window_id", "")
        return await self._get_controller().maximize_window(window_id)

    async def _handle_restore_window(self, args: dict[str, Any]) -> dict[str, Any]:
        window_id = args.get("window_id", "")
        return await self._get_controller().restore_window(window_id)

    async def _handle_close_window(self, args: dict[str, Any]) -> dict[str, Any]:
        window_id = args.get("window_id", "")
        return await self._get_controller().close_window(window_id)

    async def _handle_move_window(self, args: dict[str, Any]) -> dict[str, Any]:
        window_id = args.get("window_id", "")
        x = args.get("x", 0)
        y = args.get("y", 0)
        return await self._get_controller().move_window(window_id, x, y)

    async def _handle_resize_window(self, args: dict[str, Any]) -> dict[str, Any]:
        window_id = args.get("window_id", "")
        width = args.get("width", 0)
        height = args.get("height", 0)
        return await self._get_controller().resize_window(window_id, width, height)

    async def _handle_launch_application(self, args: dict[str, Any]) -> dict[str, Any]:
        app = args.get("app", "")
        if not app:
            return {"success": False, "error": "Application name required"}
        return self._run_platform("open_application", app)

    async def _handle_close_application(self, args: dict[str, Any]) -> dict[str, Any]:
        app = args.get("app", "")
        if not app:
            return {"success": False, "error": "Application name required"}
        return self._run_platform("close_application", app)

    async def _handle_list_processes(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self._get_controller().list_processes()

    async def _handle_get_monitors(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self._get_controller().get_monitors()

    async def _handle_run_command(self, args: dict[str, Any]) -> dict[str, Any]:
        command = args.get("command", "")
        if not command:
            return {"success": False, "error": "Command required"}
        timeout = args.get("timeout", 30)
        return await self._get_controller().run_command(command, timeout=timeout)

    async def _handle_list_files(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        return await self._get_controller().list_files(path)

    async def _handle_search_files(self, args: dict[str, Any]) -> dict[str, Any]:
        query = args.get("query", "")
        path = args.get("path", "")
        if not query:
            return {"success": False, "error": "Query required"}
        from computer.file_manager import file_manager
        return file_manager.search(query, path)

    async def _handle_create_folder(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        if not path:
            return {"success": False, "error": "Path required"}
        from computer.file_manager import file_manager
        return file_manager.create_folder(path)

    async def _handle_rename_file(self, args: dict[str, Any]) -> dict[str, Any]:
        old_path = args.get("old_path", "")
        new_name = args.get("new_name", "")
        if not old_path or not new_name:
            return {"success": False, "error": "old_path and new_name required"}
        from computer.file_manager import file_manager
        return file_manager.rename(old_path, new_name)

    async def _handle_move_file(self, args: dict[str, Any]) -> dict[str, Any]:
        src = args.get("src", "")
        dst = args.get("dst", "")
        if not src or not dst:
            return {"success": False, "error": "src and dst required"}
        from computer.file_manager import file_manager
        return file_manager.move(src, dst)

    async def _handle_copy_file(self, args: dict[str, Any]) -> dict[str, Any]:
        src = args.get("src", "")
        dst = args.get("dst", "")
        if not src or not dst:
            return {"success": False, "error": "src and dst required"}
        from computer.file_manager import file_manager
        return file_manager.copy(src, dst)

    async def _handle_delete_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        if not path:
            return {"success": False, "error": "Path required"}
        from computer.file_manager import file_manager
        return file_manager.delete(path)

    async def _handle_open_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path", "")
        if not path:
            return {"success": False, "error": "Path required"}
        from computer.file_manager import file_manager
        return file_manager.open(path)

    async def _handle_read_clipboard(self, args: dict[str, Any]) -> dict[str, Any]:
        from computer.clipboard import clipboard_provider
        return clipboard_provider.read()

    async def _handle_write_clipboard(self, args: dict[str, Any]) -> dict[str, Any]:
        text = args.get("text", "")
        from computer.clipboard import clipboard_provider
        return clipboard_provider.write(text)

    async def _handle_open_terminal(self, args: dict[str, Any]) -> dict[str, Any]:
        command = args.get("command", "")
        from computer.terminal import terminal_provider
        return terminal_provider.open_terminal(command)

    async def _handle_run_terminal_command(self, args: dict[str, Any]) -> dict[str, Any]:
        command = args.get("command", "")
        timeout = args.get("timeout", 30)
        from computer.terminal import terminal_provider
        return terminal_provider.run_command(command, timeout=timeout)


computer_manager = ComputerManager()

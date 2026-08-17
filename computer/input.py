"""Simulated keyboard / pointer input across platforms.

Discovers the best available input tool at runtime (wtype, ydotool, xdotool
on Linux; pyautogui fallback) so the tools stay functional on any desktop.
"""

from __future__ import annotations

import shutil
import subprocess


def _which(*names):
    for name in names:
        if shutil.which(name):
            return name
    return None


class InputController:
    """Types text and drives the pointer using the available backend."""

    def __init__(self):
        self._backend = None

    def detect(self) -> str | None:
        if self._backend is None:
            self._backend = _which("wtype", "ydotool", "xdotool") or _which("pyautogui")
        return self._backend

    async def type_text(self, text: str) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found (install wtype or ydotool)."}
        try:
            if tool == "wtype":
                subprocess.run(["wtype", "-s", "25", text], capture_output=True, check=True)
            elif tool == "ydotool":
                subprocess.run(["ydotool", "type", text], capture_output=True, check=True)
            elif tool == "xdotool":
                subprocess.run(["xdotool", "type", "--delay", "25", text], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.typewrite(text, interval=0.02)
            return {"ok": True, "typed": len(text), "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def click_at(self, x: int, y: int, button: int = 1) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found (install ydotool or xdotool)."}
        try:
            if tool == "ydotool":
                subprocess.run(["ydotool", "mousemove", "--absolute", str(x), str(y)], capture_output=True, check=True)
                subprocess.run(["ydotool", "click", str(button)], capture_output=True, check=True)
            elif tool == "xdotool":
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], capture_output=True, check=True)
                subprocess.run(["xdotool", "click", str(button)], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.click(x, y, button=button)
            return {"ok": True, "x": x, "y": y, "button": button, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def double_click_at(self, x: int, y: int) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found."}
        try:
            if tool == "ydotool":
                subprocess.run(["ydotool", "mousemove", "--absolute", str(x), str(y)], capture_output=True, check=True)
                subprocess.run(["ydotool", "click", "1"], capture_output=True, check=True)
                subprocess.run(["ydotool", "click", "1"], capture_output=True, check=True)
            elif tool == "xdotool":
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], capture_output=True, check=True)
                subprocess.run(["xdotool", "click", "1", "click", "1"], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.doubleClick(x, y)
            return {"ok": True, "x": x, "y": y, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def right_click_at(self, x: int, y: int) -> dict:
        return await self.click_at(x, y, 3)

    async def mouse_move(self, x: int, y: int) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found."}
        try:
            if tool == "ydotool":
                subprocess.run(["ydotool", "mousemove", "--absolute", str(x), str(y)], capture_output=True, check=True)
            elif tool == "xdotool":
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.moveTo(x, y)
            return {"ok": True, "x": x, "y": y, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def mouse_drag(self, x1: int, y1: int, x2: int, y2: int) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found."}
        try:
            if tool == "ydotool":
                subprocess.run(["ydotool", "mousemove", "--absolute", str(x1), str(y1)], capture_output=True, check=True)
                subprocess.run(["ydotool", "mousedown", "1"], capture_output=True, check=True)
                subprocess.run(["ydotool", "mousemove", "--absolute", str(x2), str(y2)], capture_output=True, check=True)
                subprocess.run(["ydotool", "mouseup", "1"], capture_output=True, check=True)
            elif tool == "xdotool":
                subprocess.run(["xdotool", "mousemove", str(x1), str(y1), "mousedown", "1", "mousemove", str(x2), str(y2), "mouseup", "1"], capture_output=True, check=True)  # noqa: E501
            else:
                import pyautogui
                pyautogui.moveTo(x1, y1)
                pyautogui.dragTo(x2, y2, button="left")
            return {"ok": True, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def mouse_scroll(self, x: int, y: int, direction: str, amount: int = 3) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found."}
        try:
            if tool == "ydotool":
                subprocess.run(["ydotool", "mousemove", "--absolute", str(x), str(y)], capture_output=True, check=True)
                scroll_map = {"up": "4", "down": "5", "left": "6", "right": "7"}
                button = scroll_map.get(direction, "5")
                subprocess.run(["ydotool", "click", button * str(amount)], capture_output=True, check=True)
            elif tool == "xdotool":
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], capture_output=True, check=True)
                scroll_map = {"up": "4", "down": "5", "left": "6", "right": "7"}
                button = scroll_map.get(direction, "5")
                subprocess.run(["xdotool", "click", button * str(amount)], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.scroll(amount if direction == "up" else -amount, x, y)
            return {"ok": True, "x": x, "y": y, "direction": direction, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def press_key(self, key: str) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found."}
        try:
            if tool in ("wtype", "ydotool", "xdotool"):
                subprocess.run([tool, "key", key], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.press(key)
            return {"ok": True, "key": key, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def hotkey(self, keys: str) -> dict:
        tool = self.detect()
        if not tool:
            return {"ok": False, "error": "No input automation tool found."}
        try:
            if tool in ("ydotool", "xdotool"):
                subprocess.run([tool, "key", keys], capture_output=True, check=True)
            else:
                import pyautogui
                pyautogui.hotkey(*keys.split("+"))
            return {"ok": True, "keys": keys, "tool": tool}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def get_cursor_position(self) -> dict:
        try:
            import pyautogui
            x, y = pyautogui.position()
            return {"ok": True, "x": x, "y": y}
        except Exception:
            return {"ok": False, "error": "Cannot get cursor position."}

    async def get_active_window(self) -> dict:
        try:
            import pyautogui
            title = pyautogui.getActiveWindow().title
            return {"ok": True, "title": title}
        except Exception:
            return {"ok": False, "error": "Cannot get active window."}

    async def list_windows(self) -> dict:
        return {"ok": False, "error": "List windows not supported by this backend."}

    async def focus_window(self, title: str) -> dict:
        return {"ok": False, "error": "Focus window not supported by this backend."}

    async def get_screen_info(self) -> dict:
        try:
            import pyautogui
            size = pyautogui.size()
            return {"ok": True, "width": size.width, "height": size.height}
        except Exception:
            return {"ok": False, "error": "Cannot get screen info."}


input_controller = InputController()

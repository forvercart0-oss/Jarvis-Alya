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


input_controller = InputController()

"""Unified computer-control layer used by the tool registry.

Wraps the OS platform backend (:mod:`system`) and the input controller
(:mod:`computer.input`) behind a single, tool-friendly API. Every method
returns a plain dict so tools can attach extra metadata freely.
"""

from __future__ import annotations

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
            try:
                Path(out).unlink()
            except OSError:
                pass

    async def set_brightness(self, level: int) -> dict:
        return await self.platform.set_brightness(level)

    async def set_do_not_disturb(self, enabled: bool) -> dict:
        return await self.platform.set_do_not_disturb(enabled)

    # ----------------------------------------------------------------- input
    async def type_text(self, text: str) -> dict:
        return await self.input.type_text(text)

    async def click_at(self, x: int, y: int, button: int = 1) -> dict:
        return await self.input.click_at(x, y, button)


computer_controller = ComputerController()

"""Wait-for-element and smart wait for JARVIS Phase 24.

Supports waiting for UI elements to appear without arbitrary sleeps.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.wait_for_element")


class WaitForElement:
    def __init__(self, timeout: float = 10.0, poll_interval: float = 0.5):
        self.timeout = timeout
        self.poll_interval = poll_interval

    async def wait_for_element(
        self,
        check_fn,
        *args,
        timeout: float | None = None,
        poll_interval: float | None = None,
    ) -> dict[str, Any]:
        timeout = timeout or self.timeout
        poll_interval = poll_interval or self.poll_interval
        start = asyncio.get_event_loop().time()
        last_result = None
        attempts = 0
        while True:
            attempts += 1
            try:
                result = await check_fn(*args)
                last_result = result
                if result.get("found") or result.get("success"):
                    return {
                        "success": True,
                        "found": True,
                        "attempts": attempts,
                        "result": result,
                    }
            except Exception as exc:
                logger.debug("wait_for_element check failed: %s", exc)
                last_result = {"error": str(exc)}
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                return {
                    "success": False,
                    "found": False,
                    "timeout": True,
                    "attempts": attempts,
                    "elapsed": elapsed,
                    "last_result": last_result,
                }
            await asyncio.sleep(poll_interval)


class SmartWait:
    @staticmethod
    async def wait_for_page_load(timeout: float = 10.0) -> dict[str, Any]:
        waiter = WaitForElement(timeout=timeout, poll_interval=0.3)

        async def check():
            try:
                from vision.screen import capture_screen
                result = await capture_screen("full")
                if result.get("ok") or result.get("success"):
                    return {"success": True, "loaded": True}
                return {"success": False}
            except Exception:
                return {"success": False}

        return await waiter.wait_for_element(check)

    @staticmethod
    async def wait_for_window(title_substring: str, timeout: float = 10.0) -> dict[str, Any]:
        waiter = WaitForElement(timeout=timeout, poll_interval=0.5)

        async def check():
            try:
                from vision.capture import get_active_window
                info = await get_active_window()
                if isinstance(info, dict) and title_substring.lower() in info.get("title", "").lower():
                    return {"success": True, "found": True, "window": info}
                return {"success": False}
            except Exception:
                return {"success": False}

        return await waiter.wait_for_element(check)

    @staticmethod
    async def wait_for_dialog(timeout: float = 10.0) -> dict[str, Any]:
        waiter = WaitForElement(timeout=timeout, poll_interval=0.3)

        async def check():
            try:
                from vision.screen_understanding import screen_understanding_engine
                understanding = await screen_understanding_engine.understand("")
                if understanding and understanding.detected_elements:
                    for el in understanding.detected_elements:
                        if el.get("type") == "dialog":
                            return {"success": True, "found": True, "element": el}
                return {"success": False}
            except Exception:
                return {"success": False}

        return await waiter.wait_for_element(check)

    @staticmethod
    async def wait_for_button_enabled(label: str, timeout: float = 10.0) -> dict[str, Any]:
        waiter = WaitForElement(timeout=timeout, poll_interval=0.3)

        async def check():
            try:
                from vision.screen_understanding import screen_understanding_engine
                understanding = await screen_understanding_engine.understand("")
                if understanding and understanding.detected_elements:
                    for el in understanding.detected_elements:
                        if label.lower() in el.get("label", "").lower() and el.get("type") == "button":
                            return {"success": True, "found": True, "enabled": el.get("enabled", True)}
                return {"success": False}
            except Exception:
                return {"success": False}

        return await waiter.wait_for_element(check)


wait_for_element = WaitForElement()
smart_wait = SmartWait()

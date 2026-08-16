"""Browser actions for JARVIS Phase 3."""

from __future__ import annotations

import logging
from typing import Any

from browser.manager import BrowserManager
from browser.safety import BrowserSafety

logger = logging.getLogger("jarvis.browser.actions")


class BrowserActions:
    def __init__(self, manager: BrowserManager):
        self._manager = manager

    async def open_url(self, url: str, session_id: str = "default") -> dict[str, Any]:
        if not url.startswith("http"):
            url = f"https://{url}"
        if BrowserSafety.is_dangerous_action("navigate", url):
            return {"success": False, "error": "Refused to navigate to potentially dangerous URL."}
        return await self._manager.navigate(url, session_id)

    async def go_back(self, session_id: str = "default") -> dict[str, Any]:
        if not self._manager.available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = self._manager._page
            if page:
                await page.go_back()
                return {"success": True}
            return {"success": False, "error": "No active page"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def go_forward(self, session_id: str = "default") -> dict[str, Any]:
        if not self._manager.available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = self._manager._page
            if page:
                await page.go_forward()
                return {"success": True}
            return {"success": False, "error": "No active page"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def reload(self, session_id: str = "default") -> dict[str, Any]:
        if not self._manager.available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = self._manager._page
            if page:
                await page.reload()
                return {"success": True}
            return {"success": False, "error": "No active page"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def click(self, selector: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.click(selector, session_id)

    async def type_text(self, selector: str, text: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.type_text(selector, text, session_id)

    async def read_page(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.get_content(session_id)

    async def screenshot(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.screenshot(session_id)

    async def get_status(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.session_status(session_id)

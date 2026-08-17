"""Browser actions for JARVIS Phase 9."""

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
            page = await self._manager._get_page(session_id)
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
            page = await self._manager._get_page(session_id)
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
            page = await self._manager._get_page(session_id)
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

    async def press(self, key: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.press(key, session_id)

    async def scroll(self, direction: str = "down", amount: int = 500, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.scroll(direction, amount, session_id)

    async def wait(self, seconds: float = 1.0, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.wait(seconds, session_id)

    async def read_page(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.get_content(session_id)

    async def extract_links(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.extract_links(session_id)

    async def screenshot(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.screenshot(session_id)

    async def open_tab(self, url: str = "about:blank", session_id: str = "default") -> dict[str, Any]:
        return await self._manager.open_tab(url, session_id)

    async def close_tab(self, tab_id: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.close_tab(tab_id, session_id)

    async def switch_tab(self, tab_id: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.switch_tab(tab_id, session_id)

    async def download(self, url: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.download(url, session_id)

    async def get_status(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.session_status(session_id)

    async def get_page_context(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.get_page_context(session_id)

    async def find_element(self, target: str, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.find_element(target, session_id)

    async def smart_wait(self, session_id: str = "default") -> dict[str, Any]:
        return await self._manager.smart_wait(session_id)

    async def is_login_page(self, session_id: str = "default") -> dict[str, Any]:
        context_result = await self.get_page_context(session_id)
        if not context_result.get("success"):
            return context_result
        from browser.page_context import PageContext, page_context_extractor
        ctx = PageContext(**context_result.get("context", {}))
        is_login = page_context_extractor.detect_login_page(ctx)
        return {"success": True, "is_login": is_login}

    async def is_captcha(self, session_id: str = "default") -> dict[str, Any]:
        context_result = await self.get_page_context(session_id)
        if not context_result.get("success"):
            return context_result
        from browser.page_context import PageContext, page_context_extractor
        ctx = PageContext(**context_result.get("context", {}))
        is_captcha = page_context_extractor.detect_captcha(ctx)
        return {"success": True, "is_captcha": is_captcha}

    async def is_purchase_page(self, session_id: str = "default") -> dict[str, Any]:
        context_result = await self.get_page_context(session_id)
        if not context_result.get("success"):
            return context_result
        from browser.page_context import PageContext, page_context_extractor
        ctx = PageContext(**context_result.get("context", {}))
        is_purchase = page_context_extractor.detect_purchase_page(ctx)
        return {"success": True, "is_purchase": is_purchase}

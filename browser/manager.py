"""Browser manager facade for JARVIS Phase 3."""

from __future__ import annotations

import logging
from typing import Any

from browser.sessions import BrowserSession, get_browser_session_manager

logger = logging.getLogger("jarvis.browser.manager")


class BrowserManager:
    def __init__(self):
        self._session_mgr = get_browser_session_manager()
        self._available = False
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def initialize(self) -> None:
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            self._available = True
            logger.info("Browser manager initialized")
        except Exception as exc:
            logger.warning("Browser manager unavailable: %s", exc)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def shutdown(self) -> None:
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._available = False
        self._browser = None
        self._context = None
        self._page = None

    async def navigate(self, url: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._page:
            return {"success": False, "error": "Browser not available"}
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await self._page.title()
            current_url = self._page.url
            session = self._session_mgr.get(session_id) or self._session_mgr.create(session_id)
            session.url = current_url
            session.title = title
            session.connected = True
            session.error = None
            if not session.tabs:
                session.tabs.append({"title": title, "url": current_url})
            else:
                session.tabs[session.active_tab_index] = {"title": title, "url": current_url}
            return {"success": True, "url": current_url, "title": title}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def get_content(self, session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._page:
            return {"success": False, "error": "Browser not available"}
        try:
            text = await self._page.evaluate("() => document.body.innerText")
            return {"success": True, "content": text[:4000]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def screenshot(self, session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._page:
            return {"success": False, "error": "Browser not available"}
        try:
            data = await self._page.screenshot(full_page=False)
            import base64
            return {"success": True, "data": base64.b64encode(data).decode()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def click(self, selector: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._page:
            return {"success": False, "error": "Browser not available"}
        try:
            await self._page.click(selector, timeout=10000)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def type_text(self, selector: str, text: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._page:
            return {"success": False, "error": "Browser not available"}
        try:
            await self._page.fill(selector, text)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def session_status(self, session_id: str = "default") -> dict[str, Any]:
        session = self._session_mgr.get(session_id)
        if session:
            return session.to_dict()
        return {"session_id": session_id, "connected": False}

"""Browser manager facade for JARVIS Phase 9."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
from pathlib import Path
from typing import Any

from browser.sessions import get_browser_session_manager

logger = logging.getLogger("jarvis.browser.manager")


class BrowserManager:
    def __init__(self):
        self._session_mgr = get_browser_session_manager()
        self._available = False
        self._playwright = None
        self._browser = None
        self._context = None
        self._pages: dict[str, Any] = {}
        self._active_session = "default"
        self._browser_type = "chromium"
        self._headless = True
        self._download_dir = str(Path.home() / "Downloads" / "JARVIS-Browser")
        Path(self._download_dir).mkdir(parents=True, exist_ok=True)

    @property
    def available(self) -> bool:
        return self._available

    async def initialize(self, browser_type: str = "chromium", headless: bool = True) -> None:
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser_type = browser_type
            self._headless = headless
            browser_cls = getattr(self._playwright, browser_type, self._playwright.chromium)
            self._browser = await browser_cls.launch(headless=headless)
            self._context = await self._browser.new_context(
                accept_downloads=True,
                viewport={"width": 1280, "height": 720},
            )
            page = await self._context.new_page()
            self._pages[self._active_session] = page
            self._available = True
            logger.info("Browser manager initialized: %s headless=%s", browser_type, headless)
        except Exception as exc:
            logger.warning("Browser manager unavailable: %s", exc)
            self._available = False

    async def shutdown(self) -> None:
        try:
            for page in self._pages.values():
                with contextlib.suppress(Exception):
                    await page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as exc:
            logger.debug("Browser shutdown error: %s", exc)
        self._available = False
        self._browser = None
        self._context = None
        self._pages.clear()

    async def _get_page(self, session_id: str = "default"):
        if session_id not in self._pages:
            if not self._context:
                return None
            try:
                page = await self._context.new_page()
                self._pages[session_id] = page
            except Exception:
                return None
        return self._pages.get(session_id)

    async def navigate(self, url: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            current_url = page.url
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
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            text = await page.evaluate("() => document.body.innerText")
            return {"success": True, "content": text[:4000]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def screenshot(self, session_id: str = "default", full_page: bool = False) -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            data = await page.screenshot(full_page=full_page)
            return {"success": True, "data": base64.b64encode(data).decode()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def click(self, selector: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            await page.click(selector, timeout=10000)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def type_text(self, selector: str, text: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            await page.fill(selector, text)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def press(self, key: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            await page.keyboard.press(key)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def scroll(self, direction: str = "down", amount: int = 500, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            y = amount if direction == "down" else -amount
            await page.evaluate(f"window.scrollBy(0, {y})")
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def wait(self, seconds: float = 1.0, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            await asyncio.sleep(seconds)
            return {"success": True, "waited": seconds}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def extract_links(self, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a')).map(a => ({
                    text: (a.innerText || '').trim(),
                    href: a.href
                })).filter(l => l.text && l.href).slice(0, 50)
            """)
            return {"success": True, "links": links}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def open_tab(self, url: str = "about:blank", session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._context:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._context.new_page()
            if url and url != "about:blank":
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            tab_id = f"{session_id}_{len(self._pages)}"
            self._pages[tab_id] = page
            session = self._session_mgr.get(session_id) or self._session_mgr.create(session_id)
            session.tabs.append({"title": await page.title(), "url": page.url})
            return {"success": True, "tab_id": tab_id, "url": page.url}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def close_tab(self, tab_id: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = self._pages.pop(tab_id, None)
            if page:
                await page.close()
                session = self._session_mgr.get(session_id)
                if session and tab_id in [t.get("url") for t in session.tabs]:
                    session.tabs = [t for t in session.tabs if t.get("url") != tab_id]
                return {"success": True}
            return {"success": False, "error": "Tab not found"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def switch_tab(self, tab_id: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        page = self._pages.get(tab_id)
        if not page:
            return {"success": False, "error": "Tab not found"}
        self._active_session = tab_id
        session = self._session_mgr.get(session_id)
        if session:
            session.active_tab_index = next((i for i, t in enumerate(session.tabs) if t.get("url") == tab_id), 0)
        return {"success": True}

    async def download(self, url: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available or not self._context:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            async with page.expect_download(timeout=60000) as download_info:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            download = await download_info.value
            filename = download.suggested_filename
            dest = Path(self._download_dir) / filename
            counter = 1
            while dest.exists():
                dest = Path(self._download_dir) / f"{dest.stem}_{counter}{dest.suffix}"
                counter += 1
            await download.save_as(dest)
            return {"success": True, "filename": dest.name, "path": str(dest), "size": dest.stat().st_size}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def session_status(self, session_id: str = "default") -> dict[str, Any]:
        session = self._session_mgr.get(session_id)
        if session:
            return session.to_dict()
        return {"session_id": session_id, "connected": False}

    async def get_page_context(self, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            from browser.page_context import page_context_extractor
            context = await page_context_extractor.extract(page)
            return {"success": True, "context": context.to_dict()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def find_element(self, target: str, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            from browser.page_context import page_context_extractor
            context = await page_context_extractor.extract(page)
            from browser.element import find_best_element
            element = find_best_element(target, [e.to_dict() for e in context.interactive_elements])
            if element:
                return {"success": True, "element": element}
            return {"success": False, "error": f"Element not found: {target}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def smart_wait(self, session_id: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "Browser not available"}
        try:
            page = await self._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page"}
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

"""Browser provider abstraction for JARVIS Phase 18."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.provider")


@dataclass
class BrowserState:
    browser: str = ""
    window: str = ""
    tab: str = ""
    url: str = ""
    title: str = ""
    loading: bool = False
    active_tab: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "browser": self.browser,
            "window": self.window,
            "tab": self.tab,
            "url": self.url,
            "title": self.title,
            "loading": self.loading,
            "active_tab": self.active_tab,
            "metadata": self.metadata,
        }


class BrowserProvider(ABC):
    """Abstract browser provider."""

    name: str = "base"

    @abstractmethod
    async def launch(self, browser_type: str = "chromium", headless: bool = True) -> dict[str, Any]:
        """Launch browser."""

    @abstractmethod
    async def close(self) -> dict[str, Any]:
        """Close browser."""

    @abstractmethod
    async def new_tab(self, url: str = "about:blank") -> dict[str, Any]:
        """Open new tab."""

    @abstractmethod
    async def close_tab(self, tab_id: str) -> dict[str, Any]:
        """Close tab."""

    @abstractmethod
    async def list_tabs(self) -> list[dict[str, Any]]:
        """List all tabs."""

    @abstractmethod
    async def switch_tab(self, tab_id: str) -> dict[str, Any]:
        """Switch to tab."""

    @abstractmethod
    async def navigate(self, url: str) -> dict[str, Any]:
        """Navigate to URL."""

    @abstractmethod
    async def go_back(self) -> dict[str, Any]:
        """Go back."""

    @abstractmethod
    async def go_forward(self) -> dict[str, Any]:
        """Go forward."""

    @abstractmethod
    async def reload(self) -> dict[str, Any]:
        """Reload page."""

    @abstractmethod
    async def get_state(self) -> BrowserState:
        """Get current browser state."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check browser availability."""


class PlaywrightBrowserProvider(BrowserProvider):
    """Playwright-based browser provider."""

    name = "playwright"

    def __init__(self):
        self._manager = None

    async def _get_manager(self):
        if self._manager is None:
            from browser.manager import BrowserManager
            self._manager = BrowserManager()
            if not self._manager.available:
                await self._manager.initialize()
        return self._manager

    async def launch(self, browser_type: str = "chromium", headless: bool = True) -> dict[str, Any]:
        mgr = await self._get_manager()
        await mgr.initialize(browser_type=browser_type, headless=headless)
        return {"success": True, "browser": browser_type}

    async def close(self) -> dict[str, Any]:
        if self._manager:
            await self._manager.shutdown()
        return {"success": True}

    async def new_tab(self, url: str = "about:blank") -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.open_tab(url)

    async def close_tab(self, tab_id: str) -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.close_tab(tab_id)

    async def list_tabs(self) -> list[dict[str, Any]]:
        mgr = await self._get_manager()
        status = await mgr.session_status()
        return status.get("tabs", [])

    async def switch_tab(self, tab_id: str) -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.switch_tab(tab_id)

    async def navigate(self, url: str) -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.navigate(url)

    async def go_back(self) -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.go_back()

    async def go_forward(self) -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.go_forward()

    async def reload(self) -> dict[str, Any]:
        mgr = await self._get_manager()
        return await mgr.reload()

    async def get_state(self) -> BrowserState:
        mgr = await self._get_manager()
        status = await mgr.session_status()
        return BrowserState(
            browser="playwright",
            url=status.get("url", ""),
            title=status.get("title", ""),
            active_tab=status.get("tabs", [{}])[0].get("url", "") if status.get("tabs") else "",
            metadata=status,
        )

    async def health_check(self) -> dict[str, Any]:
        try:
            mgr = await self._get_manager()
            return {"status": "online" if mgr.available else "offline", "provider": self.name}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}


_browser_provider: PlaywrightBrowserProvider | None = None


def get_browser_provider() -> BrowserProvider:
    global _browser_provider
    if _browser_provider is None:
        _browser_provider = PlaywrightBrowserProvider()
    return _browser_provider

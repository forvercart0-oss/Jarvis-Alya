"""Browser automation tools for JARVIS Phase 9.

These tools use the Playwright-based BrowserManager for controlled
browser interaction. They integrate with the existing tool registry
and safety/confirmation system.
"""

from __future__ import annotations

import asyncio
import logging

from browser.actions import BrowserActions
from browser.manager import BrowserManager
from tools.registry import ToolResult

logger = logging.getLogger("jarvis.tools.browser")

_browser_mgr: BrowserManager | None = None
_browser_actions: BrowserActions | None = None
_browser_initializing: asyncio.Task | None = None


def _get_browser() -> BrowserActions:
    global _browser_mgr, _browser_actions, _browser_initializing
    if _browser_mgr is None:
        _browser_mgr = BrowserManager()
        try:
            loop = asyncio.get_running_loop()
            _browser_initializing = loop.create_task(_browser_mgr.initialize())
        except RuntimeError:
            pass
    if _browser_actions is None and _browser_mgr is not None:
        _browser_actions = BrowserActions(_browser_mgr)
    return _browser_actions


class BrowserNavigateTool:
    name = "browser_navigate"
    description = "Navigate the browser to a URL."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to navigate to"},
            "session_id": {"type": "string", "description": "Browser session ID"},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, session_id: str = "default", **kwargs) -> ToolResult:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        result = await _get_browser().open_url(url, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Navigation failed."))


class BrowserBackTool:
    name = "browser_back"
    description = "Go back to the previous page in the browser."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().go_back(session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Back navigation failed."))


class BrowserForwardTool:
    name = "browser_forward"
    description = "Go forward to the next page in the browser."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().go_forward(session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Forward navigation failed."))


class BrowserReloadTool:
    name = "browser_reload"
    description = "Reload the current browser page."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().reload(session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Reload failed."))


class BrowserClickTool:
    name = "browser_click"
    description = "Click an element on the current browser page."
    parameters = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector or text to click"},
            "session_id": {"type": "string"},
        },
        "required": ["selector"],
    }

    async def execute(self, selector: str, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().click(selector, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result, requires_confirmation=False)
        return ToolResult(success=False, error=result.get("error", "Click failed."), requires_confirmation=False)


class BrowserTypeTool:
    name = "browser_type"
    description = "Type text into an input field on the current browser page."
    parameters = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector for the input field"},
            "text": {"type": "string", "description": "Text to type"},
            "session_id": {"type": "string"},
        },
        "required": ["selector", "text"],
    }

    async def execute(self, selector: str, text: str, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().type_text(selector, text, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result, requires_confirmation=False)
        return ToolResult(success=False, error=result.get("error", "Type failed."), requires_confirmation=False)


class BrowserPressTool:
    name = "browser_press"
    description = "Press a keyboard key in the browser."
    parameters = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key to press, e.g. Enter, Escape, Tab"},
            "session_id": {"type": "string"},
        },
        "required": ["key"],
    }

    async def execute(self, key: str, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().press(key, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Press failed."))


class BrowserScrollTool:
    name = "browser_scroll"
    description = "Scroll the browser page."
    parameters = {
        "type": "object",
        "properties": {
            "direction": {"type": "string", "description": "Scroll direction: up or down"},
            "amount": {"type": "integer", "description": "Pixels to scroll"},
            "session_id": {"type": "string"},
        },
    }

    async def execute(self, direction: str = "down", amount: int = 500,
                     session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().scroll(direction, amount, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Scroll failed."))


class BrowserWaitTool:
    name = "browser_wait"
    description = "Wait for a specified number of seconds in the browser."
    parameters = {
        "type": "object",
        "properties": {
            "seconds": {"type": "number", "description": "Seconds to wait"},
            "session_id": {"type": "string"},
        },
    }

    async def execute(self, seconds: float = 1.0, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().wait(seconds, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Wait failed."))


class BrowserReadTool:
    name = "browser_read"
    description = "Read the visible text content of the current browser page."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().read_page(session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Read failed."))


class BrowserExtractLinksTool:
    name = "browser_extract_links"
    description = "Extract visible links from the current browser page."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().extract_links(session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Extract links failed."))


class BrowserScreenshotTool:
    name = "browser_screenshot"
    description = "Take a screenshot of the current browser page."
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "full_page": {"type": "boolean", "description": "Capture full page"},
        },
    }

    async def execute(self, session_id: str = "default", full_page: bool = False, **kwargs) -> ToolResult:
        result = await _get_browser().screenshot(session_id, full_page)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Screenshot failed."))


class BrowserOpenTabTool:
    name = "browser_open_tab"
    description = "Open a new browser tab."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to open in new tab"},
            "session_id": {"type": "string"},
        },
    }

    async def execute(self, url: str = "about:blank", session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().open_tab(url, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Open tab failed."))


class BrowserCloseTabTool:
    name = "browser_close_tab"
    description = "Close a browser tab."
    parameters = {
        "type": "object",
        "properties": {
            "tab_id": {"type": "string", "description": "Tab ID to close"},
            "session_id": {"type": "string"},
        },
        "required": ["tab_id"],
    }

    async def execute(self, tab_id: str, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().close_tab(tab_id, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Close tab failed."))


class BrowserSwitchTabTool:
    name = "browser_switch_tab"
    description = "Switch to a different browser tab."
    parameters = {
        "type": "object",
        "properties": {
            "tab_id": {"type": "string", "description": "Tab ID to switch to"},
            "session_id": {"type": "string"},
        },
        "required": ["tab_id"],
    }

    async def execute(self, tab_id: str, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().switch_tab(tab_id, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Switch tab failed."))


class BrowserDownloadTool:
    name = "browser_download"
    description = "Download a file from a URL using the browser."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to download from"},
            "session_id": {"type": "string"},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().download(url, session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Download failed."))


class BrowserStatusTool:
    name = "browser_status"
    description = "Get the current browser session status (URL, title, tabs)."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().get_status(session_id)
        return ToolResult(success=True, result=result)

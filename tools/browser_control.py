"""Browser automation tools for JARVIS Phase 3.

These tools use the Playwright-based BrowserManager for controlled
browser interaction. They integrate with the existing tool registry
and safety/confirmation system.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

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


class BrowserScreenshotTool:
    name = "browser_screenshot"
    description = "Take a screenshot of the current browser page."
    parameters = {
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
    }

    async def execute(self, session_id: str = "default", **kwargs) -> ToolResult:
        result = await _get_browser().screenshot(session_id)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Screenshot failed."))


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

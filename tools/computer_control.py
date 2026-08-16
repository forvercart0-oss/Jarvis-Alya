"""Unified computer control tool for JARVIS Phase 3.

Wraps the ComputerController to provide a single tool that the AI can
call with different actions. All side effects go through the safety
and confirmation system.
"""

from __future__ import annotations

import logging
from typing import Any

from computer.controller import computer_controller
from tools.browser_control import _get_browser
from tools.registry import ToolResult

logger = logging.getLogger("jarvis.tools.computer")


class ComputerControlTool:
    name = "computer_control"
    description = "Control the computer or browser. Actions: open_application, close_application, type_text, click_at, take_screenshot, set_volume, lock_screen, shutdown, reboot, browser_navigate, browser_click, browser_type, browser_read, browser_screenshot."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "Action to perform"},
            "arguments": {"type": "object", "description": "Action-specific arguments"},
        },
        "required": ["action"],
    }

    async def execute(self, action: str, arguments: dict[str, Any] | None = None, **kwargs) -> ToolResult:
        arguments = arguments or {}
        dangerous = {"shutdown", "reboot", "suspend", "lock_screen"}
        confirmation_actions = {
            "open_application", "close_application", "type_text",
            "click_at", "browser_click", "browser_type",
            "shutdown", "reboot",
        }

        if action in dangerous:
            return ToolResult(
                success=False,
                error=f"Action '{action}' is dangerous and requires explicit confirmation.",
                confirmation_required=True,
                confirmation_message=f"Confirm {action}?",
            )

        if action in confirmation_actions:
            return ToolResult(
                success=False,
                confirmation_required=True,
                confirmation_message=f"Confirm {action} with arguments: {arguments}",
            )

        try:
            if action.startswith("browser_"):
                browser_action = action[len("browser_"):]
                browser = _get_browser()
                handler = getattr(browser, browser_action, None)
                if not handler:
                    return ToolResult(success=False, error=f"Unknown browser action: {browser_action}")
                result = await handler(**arguments)
                if result.get("success"):
                    return ToolResult(success=True, result=result)
                return ToolResult(success=False, error=result.get("error", "Browser action failed."))

            handler = getattr(computer_controller, action, None)
            if not handler:
                return ToolResult(success=False, error=f"Unknown computer action: {action}")
            result = await handler(**arguments)
            if result.get("ok"):
                return ToolResult(success=True, result=result)
            return ToolResult(success=False, error=result.get("error", "Computer action failed."))
        except Exception as exc:
            logger.warning("Computer control %s failed: %s", action, exc)
            return ToolResult(success=False, error=str(exc))

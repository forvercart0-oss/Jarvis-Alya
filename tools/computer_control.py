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


async def _browser_vision_click(arguments: dict[str, Any]) -> ToolResult:
    target = arguments.get("target", "")
    if not target:
        return ToolResult(success=False, error="Target required for vision click.")
    try:
        from vision.manager import vision_manager
        result = await vision_manager.find(target)
        if result.get("found"):
            x = result.get("x", 0)
            y = result.get("y", 0)
            click_result = await computer_controller.click_at(x, y, 1)
            if click_result.get("ok"):
                return ToolResult(success=True, result={"x": x, "y": y, "confidence": result.get("confidence"), "method": "vision"})
        return ToolResult(success=False, error=result.get("error", "Vision target not found."))
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


async def _browser_vision_type(arguments: dict[str, Any]) -> ToolResult:
    text = arguments.get("text", "")
    if not text:
        return ToolResult(success=False, error="Text required for vision type.")
    try:
        result = await computer_controller.type_text(text)
        if result.get("ok"):
            return ToolResult(success=True, result={"typed": len(text), "method": "vision"})
        return ToolResult(success=False, error=result.get("error", "Vision type failed."))
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


class ComputerControlTool:
    name = "computer_control"
    description = "Control the computer or browser. Actions: open_application, close_application, type_text, click_at, take_screenshot, set_volume, lock_screen, shutdown, reboot, browser_navigate, browser_click, browser_type, browser_read, browser_screenshot, browser_vision_click, browser_vision_type."
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
            "browser_vision_click", "browser_vision_type",
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
                if browser_action == "vision_click":
                    return await _browser_vision_click(arguments)
                if browser_action == "vision_type":
                    return await _browser_vision_type(arguments)
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

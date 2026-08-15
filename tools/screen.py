"""Screen / desktop control tools: screenshots, brightness, notifications,
and simulated keyboard/mouse input (with graceful per-session fallbacks).
"""

from tools.registry import ToolResult

from computer.controller import computer_controller


class ScreenshotTool:
    name = "take_screenshot"
    description = "Capture a screenshot of the full screen and return it as a base64 PNG."
    parameters = {
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "optional 'WxH+X+Y' region (supported on X11 backends)"},
        },
    }

    async def execute(self, region: str = "", **kwargs) -> ToolResult:
        result = await computer_controller.screenshot(region)
        if result.get("data"):
            return ToolResult(success=True, result={"format": "png", "width": 0, "height": 0, "data": result["data"]})
        return ToolResult(success=False, error=result.get("error", "Screenshot failed."))


class BrightnessControlTool:
    name = "set_screen_brightness"
    description = "Set screen brightness to a percentage (0-100) using brightnessctl."
    parameters = {
        "type": "object",
        "properties": {"level": {"type": "integer", "description": "Brightness percentage 0-100"}},
        "required": ["level"],
    }

    async def execute(self, level: int, **kwargs) -> ToolResult:
        result = await computer_controller.set_brightness(level)
        if result.get("ok"):
            return ToolResult(success=True, result={"level": result.get("level", level)})
        return ToolResult(success=False, error=result.get("error", "Brightness control failed."))


class DoNotDisturbTool:
    name = "set_do_not_disturb"
    description = "Enable or disable Do Not Disturb notifications via KDE/Plasma."
    parameters = {
        "type": "object",
        "properties": {"enabled": {"type": "boolean"}},
        "required": ["enabled"],
    }

    async def execute(self, enabled: bool, **kwargs) -> ToolResult:
        result = await computer_controller.set_do_not_disturb(enabled)
        if result.get("ok"):
            return ToolResult(success=True, result={"do_not_disturb": enabled})
        return ToolResult(success=False, error=result.get("error", "Do Not Disturb control failed."))


class TypeTextTool:
    name = "type_text"
    description = "Type text into the focused window (via wtype, ydotool, or xdotool)."
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    async def execute(self, text: str, **kwargs) -> ToolResult:
        result = await computer_controller.type_text(text)
        if result.get("ok"):
            return ToolResult(success=True, result={"typed": result.get("typed", 0), "tool": result.get("tool")})
        return ToolResult(success=False, error=result.get("error", "Typing failed."))


class ClickTool:
    name = "click_at"
    description = "Move the pointer and click at x,y screen coordinates (ydotool/xdotool)."
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "button": {"type": "integer", "description": "1=left, 2=middle, 3=right"},
        },
        "required": ["x", "y"],
    }

    async def execute(self, x: int, y: int, button: int = 1, **kwargs) -> ToolResult:
        result = await computer_controller.click_at(x, y, button)
        if result.get("ok"):
            return ToolResult(success=True, result={"x": x, "y": y, "button": button, "tool": result.get("tool")})
        return ToolResult(success=False, error=result.get("error", "Click failed."))

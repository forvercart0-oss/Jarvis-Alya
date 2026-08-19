"""Vision tools for JARVIS Phase 4."""

from __future__ import annotations

import logging

from tools.registry import ToolResult
from vision.manager import vision_manager

logger = logging.getLogger("jarvis.tools.vision")


class VisionCaptureScreenTool:
    name = "vision_capture_screen"
    description = "Capture a screenshot. Modes: full, window, application, region, monitor."
    parameters = {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "description": "Capture mode: full, window, application, region, monitor"},
            "window": {"type": "string", "description": "Window name or ID (for window/application mode)"},
            "region": {"type": "string", "description": "Region string WxH+X+Y"},
            "monitor": {"type": "integer", "description": "Monitor index"},
        },
    }

    async def execute(self, mode: str = "full", window: str | None = None, region: str | None = None, monitor: int | None = None, **kwargs) -> ToolResult:
        result = await vision_manager.screenshot(mode=mode, window=window, region=region, monitor=monitor)
        if result.get("ok") or result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Screenshot failed."))


class VisionAnalyzeScreenTool:
    name = "vision_analyze_screen"
    description = "Analyze a screenshot. Modes: describe, ocr, elements."
    parameters = {
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Path to the screenshot image"},
            "prompt": {"type": "string", "description": "Optional prompt for analysis"},
            "mode": {"type": "string", "description": "Analysis mode: describe, ocr, elements"},
        },
        "required": ["image_path"],
    }

    async def execute(self, image_path: str, prompt: str = "", mode: str = "describe", **kwargs) -> ToolResult:
        result = await vision_manager.analyze(image_path, prompt=prompt, mode=mode)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Analysis failed."))


class VisionFindTargetTool:
    name = "vision_find_target"
    description = "Find a UI element on screen by name/description."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Target name or description (e.g. 'Login button')"},
            "region": {"type": "string", "description": "Optional region WxH+X+Y to limit search"},
        },
        "required": ["target"],
    }

    async def execute(self, target: str, region: str | None = None, **kwargs) -> ToolResult:
        result = await vision_manager.find(target, region=region)
        if result.get("found"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", f"Target '{target}' not found."))


class VisionOcrTool:
    name = "vision_ocr"
    description = "Run OCR on a screenshot to extract visible text."
    parameters = {
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Path to the screenshot image"},
            "region": {"type": "string", "description": "Optional region WxH+X+Y"},
        },
        "required": ["image_path"],
    }

    async def execute(self, image_path: str, region: str | None = None, **kwargs) -> ToolResult:
        from vision.ocr import ocr_image, ocr_region
        from vision.regions import parse_region
        if region:
            parsed = parse_region(region)
            result = await ocr_region(image_path, parsed or {})
        else:
            result = await ocr_image(image_path)
        text = result.get("text", "")
        if text:
            return ToolResult(success=True, result={"text": text, "backend": result.get("backend")})
        return ToolResult(success=False, error=result.get("error", "OCR failed."))


class ComputerMouseClickTool:
    name = "computer_mouse_click"
    description = "Click at screen coordinates."
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
        from vision.actions import mouse_click
        result = await mouse_click(x, y, button)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Click failed."))


class ComputerMouseMoveTool:
    name = "computer_mouse_move"
    description = "Move the mouse to screen coordinates."
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
        },
        "required": ["x", "y"],
    }

    async def execute(self, x: int, y: int, **kwargs) -> ToolResult:
        from vision.actions import mouse_move
        result = await mouse_move(x, y)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Mouse move failed."))


class ComputerMouseDragTool:
    name = "computer_mouse_drag"
    description = "Drag from one point to another."
    parameters = {
        "type": "object",
        "properties": {
            "x1": {"type": "integer"},
            "y1": {"type": "integer"},
            "x2": {"type": "integer"},
            "y2": {"type": "integer"},
        },
        "required": ["x1", "y1", "x2", "y2"],
    }

    async def execute(self, x1: int, y1: int, x2: int, y2: int, **kwargs) -> ToolResult:
        from vision.actions import mouse_drag
        result = await mouse_drag(x1, y1, x2, y2)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Drag failed."))


class ComputerMouseScrollTool:
    name = "computer_mouse_scroll"
    description = "Scroll at screen coordinates."
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "direction": {"type": "string", "description": "up or down"},
            "amount": {"type": "integer", "description": "Scroll amount"},
        },
        "required": ["x", "y"],
    }

    async def execute(self, x: int, y: int, direction: str = "down", amount: int = 3, **kwargs) -> ToolResult:
        from vision.actions import mouse_scroll
        result = await mouse_scroll(x, y, direction, amount)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Scroll failed."))


class ComputerKeyboardTypeTool:
    name = "computer_keyboard_type"
    description = "Type text into the focused window."
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to type"},
        },
        "required": ["text"],
    }

    async def execute(self, text: str, **kwargs) -> ToolResult:
        from vision.actions import keyboard_type
        result = await keyboard_type(text)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Typing failed."))


class ComputerKeyboardHotkeyTool:
    name = "computer_keyboard_hotkey"
    description = "Press a keyboard shortcut."
    parameters = {
        "type": "object",
        "properties": {
            "keys": {"type": "array", "items": {"type": "string"}, "description": "Keys like ['ctrl', 'c']"},
        },
        "required": ["keys"],
    }

    async def execute(self, keys: list[str], **kwargs) -> ToolResult:
        from vision.actions import keyboard_hotkey
        result = await keyboard_hotkey(keys)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Hotkey failed."))


class ComputerKeyboardPressTool:
    name = "computer_keyboard_press"
    description = "Press a single key."
    parameters = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key name like 'enter', 'escape'"},
        },
        "required": ["key"],
    }

    async def execute(self, key: str, **kwargs) -> ToolResult:
        from vision.actions import keyboard_press
        result = await keyboard_press(key)
        if result.get("success"):
            return ToolResult(success=True, result=result)
        return ToolResult(success=False, error=result.get("error", "Key press failed."))

"""Advanced mouse and keyboard actions for JARVIS Phase 4."""

from __future__ import annotations

import asyncio
import logging
import platform
from typing import Any

logger = logging.getLogger("jarvis.vision.actions")


async def _ensure_permission(permission: str) -> bool:
    from vision.permissions import check_computer_permission
    return check_computer_permission(permission)


async def mouse_move(x: int, y: int) -> dict[str, Any]:
    if not await _ensure_permission("computer.mouse"):
        return {"success": False, "error": "Permission denied: computer.mouse"}
    from computer.controller import computer_controller
    result = await computer_controller.click_at(x, y)
    if result.get("ok"):
        return {"success": True, "x": x, "y": y}
    return {"success": False, "error": result.get("error", "Mouse move failed.")}


async def mouse_click(x: int, y: int, button: int = 1) -> dict[str, Any]:
    if not await _ensure_permission("computer.mouse"):
        return {"success": False, "error": "Permission denied: computer.mouse"}
    from computer.controller import computer_controller
    result = await computer_controller.click_at(x, y, button)
    if result.get("ok"):
        return {"success": True, "x": x, "y": y, "button": button}
    return {"success": False, "error": result.get("error", "Click failed.")}


async def mouse_double_click(x: int, y: int) -> dict[str, Any]:
    if not await _ensure_permission("computer.mouse"):
        return {"success": False, "error": "Permission denied: computer.mouse"}
    from computer.controller import computer_controller
    r1 = await computer_controller.click_at(x, y, 1)
    await asyncio.sleep(0.05)
    r2 = await computer_controller.click_at(x, y, 1)
    if r1.get("ok") and r2.get("ok"):
        return {"success": True, "x": x, "y": y}
    return {"success": False, "error": "Double click failed."}


async def mouse_right_click(x: int, y: int) -> dict[str, Any]:
    return await mouse_click(x, y, button=3)


async def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
    if not await _ensure_permission("computer.mouse"):
        return {"success": False, "error": "Permission denied: computer.mouse"}
    from computer.controller import computer_controller
    await computer_controller.click_at(x1, y1, 1)
    await asyncio.sleep(0.05)
    result = await _run_platform_command("mouse_drag", x1, y1, x2, y2)
    if result.get("ok"):
        return {"success": True, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    return {"success": False, "error": result.get("error", "Drag failed.")}


async def mouse_scroll(x: int, y: int, direction: str = "down", amount: int = 3) -> dict[str, Any]:
    if not await _ensure_permission("computer.mouse"):
        return {"success": False, "error": "Permission denied: computer.mouse"}
    system = platform.system().lower()
    if system == "linux":
        scroll = "4" if direction == "down" else "5"
        result = await _run_platform_command("mouse_scroll", x, y, scroll * str(amount))
        if result.get("ok"):
            return {"success": True, "x": x, "y": y, "direction": direction}
        return result
    return {"success": False, "error": f"Scroll not implemented for {system}"}


async def keyboard_type(text: str) -> dict[str, Any]:
    if not await _ensure_permission("computer.keyboard"):
        return {"success": False, "error": "Permission denied: computer.keyboard"}
    from computer.controller import computer_controller
    result = await computer_controller.type_text(text)
    if result.get("ok"):
        return {"success": True, "typed": len(text)}
    return {"success": False, "error": result.get("error", "Typing failed.")}


async def keyboard_hotkey(keys: list[str]) -> dict[str, Any]:
    if not await _ensure_permission("computer.keyboard"):
        return {"success": False, "error": "Permission denied: computer.keyboard"}
    system = platform.system().lower()
    if system == "linux":
        mapping = {"ctrl": "ctrl", "alt": "alt", "shift": "shift", "win": "super", "cmd": "super"}
        xdotool_keys = [mapping.get(k.lower(), k.lower()) for k in keys]
        result = await _run_platform_command("keyboard_hotkey", "+".join(xdotool_keys))
        if result.get("ok"):
            return {"success": True, "keys": keys}
        return result
    return {"success": False, "error": f"Hotkey not implemented for {system}"}


async def keyboard_press(key: str) -> dict[str, Any]:
    if not await _ensure_permission("computer.keyboard"):
        return {"success": False, "error": "Permission denied: computer.keyboard"}
    system = platform.system().lower()
    if system == "linux":
        result = await _run_platform_command("keyboard_press", key)
        if result.get("ok"):
            return {"success": True, "key": key}
        return result
    return {"success": False, "error": f"Key press not implemented for {system}"}


async def _run_platform_command(action: str, *args: Any) -> dict[str, Any]:
    system = platform.system().lower()
    module_map = {"linux": "computer.linux", "windows": "computer.windows", "macos": "computer.macos"}
    module_name = module_map.get(system)
    if not module_name:
        return {"success": False, "error": f"Unsupported platform: {system}"}
    try:
        import importlib
        mod = importlib.import_module(module_name)
        handler = getattr(mod, action, None)
        if not handler:
            return {"success": False, "error": f"Action {action} not implemented for {system}"}
        return handler(*args)
    except Exception as exc:
        return {"success": False, "error": str(exc)}

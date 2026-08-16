"""Vision API routes for JARVIS Phase 4."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import get_settings
from vision.manager import vision_manager
from vision.capture import capture_screen, get_active_window, get_screen_info, list_monitors
from vision.analyzer import analyze_image, describe_screen
from vision.detector import detect_elements, find_target
from vision.ocr import ocr_image
from vision.regions import parse_region
from vision.permissions import (
    vision_read_screen, vision_capture, vision_analyze,
    computer_mouse, computer_keyboard,
)
from vision.actions import (
    mouse_click, mouse_double_click, mouse_right_click,
    mouse_drag, mouse_scroll, keyboard_type, keyboard_hotkey, keyboard_press,
)
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.api.vision")

router = APIRouter(prefix="/vision", tags=["vision"])


class ScreenshotRequest(BaseModel):
    mode: str = "full"
    window: str | None = None
    region: str | None = None
    monitor: int | None = None


class AnalyzeRequest(BaseModel):
    image_path: str
    prompt: str = ""
    mode: str = "describe"


class RegionRequest(BaseModel):
    region: str


class FindTargetRequest(BaseModel):
    target: str
    region: str | None = None


class OcrRequest(BaseModel):
    image_path: str
    region: str | None = None


class MouseClickRequest(BaseModel):
    x: int
    y: int
    button: int = 1


class MouseDragRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class ScrollRequest(BaseModel):
    x: int
    y: int
    direction: str = "down"
    amount: int = 3


class TypeRequest(BaseModel):
    text: str


class HotkeyRequest(BaseModel):
    keys: list[str]


class PressRequest(BaseModel):
    key: str


@router.get("/status")
async def vision_status() -> dict[str, Any]:
    return vision_manager.status()


@router.post("/screenshot")
async def vision_screenshot(req: ScreenshotRequest) -> dict[str, Any]:
    result = await vision_manager.screenshot(
        mode=req.mode,
        window=req.window,
        region=req.region,
        monitor=req.monitor,
    )
    if not result.get("ok") and not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Screenshot failed."))
    return result


@router.post("/analyze")
async def vision_analyze(req: AnalyzeRequest) -> dict[str, Any]:
    result = await vision_manager.analyze(req.image_path, prompt=req.prompt, mode=req.mode)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed."))
    return result


@router.post("/region")
async def vision_region(req: RegionRequest) -> dict[str, Any]:
    parsed = parse_region(req.region)
    if parsed is None:
        raise HTTPException(status_code=400, detail="Invalid region format. Use WxH+X+Y.")
    return {"ok": True, "region": parsed}


@router.post("/find")
async def vision_find(req: FindTargetRequest) -> dict[str, Any]:
    result = await vision_manager.find(req.target, region=req.region)
    if not result.get("success") and not result.get("found"):
        raise HTTPException(status_code=500, detail=result.get("error", "Target not found."))
    return result


@router.post("/ocr")
async def vision_ocr(req: OcrRequest) -> dict[str, Any]:
    if req.region:
        from vision.ocr import ocr_region
        result = await ocr_region(req.image_path, parse_region(req.region) or {})
    else:
        result = await ocr_image(req.image_path)
    if not result.get("success") and not result.get("text"):
        raise HTTPException(status_code=500, detail=result.get("error", "OCR failed."))
    return result


@router.get("/active_window")
async def vision_active_window() -> dict[str, Any]:
    return await vision_manager.active_window()


@router.get("/screen_info")
async def vision_screen_info() -> dict[str, Any]:
    return await vision_manager.screen_info()


@router.get("/monitors")
async def vision_monitors() -> dict[str, Any]:
    monitors = await vision_manager.monitors()
    return {"monitors": monitors}


@router.post("/mouse/click")
async def vision_mouse_click(req: MouseClickRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {"action": "mouse_click", "x": req.x, "y": req.y})
    result = await mouse_click(req.x, req.y, req.button)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "mouse_click", "x": req.x, "y": req.y})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Click failed."))


@router.post("/mouse/double_click")
async def vision_mouse_double_click(req: MouseClickRequest) -> dict[str, Any]:
    from vision.actions import mouse_double_click
    await ws_manager.broadcast("vision_action_started", {"action": "mouse_double_click", "x": req.x, "y": req.y})
    result = await mouse_double_click(req.x, req.y)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "mouse_double_click", "x": req.x, "y": req.y})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Double click failed."))


@router.post("/mouse/drag")
async def vision_mouse_drag(req: MouseDragRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {"action": "mouse_drag", "x1": req.x1, "y1": req.y1, "x2": req.x2, "y2": req.y2})
    result = await mouse_drag(req.x1, req.y1, req.x2, req.y2)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "mouse_drag"})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Drag failed."))


@router.post("/mouse/scroll")
async def vision_mouse_scroll(req: ScrollRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {"action": "mouse_scroll", "x": req.x, "y": req.y, "direction": req.direction})
    result = await mouse_scroll(req.x, req.y, req.direction, req.amount)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "mouse_scroll"})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Scroll failed."))


@router.post("/keyboard/type")
async def vision_keyboard_type(req: TypeRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {"action": "keyboard_type", "length": len(req.text)})
    result = await keyboard_type(req.text)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "keyboard_type"})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Typing failed."))


@router.post("/keyboard/hotkey")
async def vision_keyboard_hotkey(req: HotkeyRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {"action": "keyboard_hotkey", "keys": req.keys})
    result = await keyboard_hotkey(req.keys)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "keyboard_hotkey"})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Hotkey failed."))


@router.post("/keyboard/press")
async def vision_keyboard_press(req: PressRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {"action": "keyboard_press", "key": req.key})
    result = await keyboard_press(req.key)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "keyboard_press"})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Key press failed."))


@router.post("/permissions/check")
async def vision_permission_check(permission: str) -> dict[str, Any]:
    from vision.permissions import check_vision_permission, check_computer_permission
    allowed = check_vision_permission(permission) or check_computer_permission(permission)
    return {"permission": permission, "allowed": allowed}

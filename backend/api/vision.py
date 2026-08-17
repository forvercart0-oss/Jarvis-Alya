"""Vision API routes for JARVIS Phase 4."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ws_manager import ws_manager
from vision.actions import (
    keyboard_hotkey,
    keyboard_press,
    keyboard_type,
    mouse_click,
    mouse_double_click,
    mouse_drag,
    mouse_scroll,
)
from vision.manager import vision_manager
from vision.ocr import crop_region, ocr_image
from vision.regions import parse_region

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
    await ws_manager.broadcast("vision_action_started", {"action": "mouse_double_click", "x": req.x, "y": req.y})
    result = await mouse_double_click(req.x, req.y)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "mouse_double_click", "x": req.x, "y": req.y})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Double click failed."))


@router.post("/mouse/drag")
async def vision_mouse_drag(req: MouseDragRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {
        "action": "mouse_drag", "x1": req.x1, "y1": req.y1,
        "x2": req.x2, "y2": req.y2,
    })
    result = await mouse_drag(req.x1, req.y1, req.x2, req.y2)
    if result.get("success"):
        await ws_manager.broadcast("vision_action_completed", {"action": "mouse_drag"})
        return result
    await ws_manager.broadcast("vision_failed", {"error": result.get("error")})
    raise HTTPException(status_code=500, detail=result.get("error", "Drag failed."))


@router.post("/mouse/scroll")
async def vision_mouse_scroll(req: ScrollRequest) -> dict[str, Any]:
    await ws_manager.broadcast("vision_action_started", {
        "action": "mouse_scroll", "x": req.x, "y": req.y,
        "direction": req.direction,
    })
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
    from vision.permissions import check_computer_permission, check_vision_permission
    allowed = check_vision_permission(permission) or check_computer_permission(permission)
    return {"permission": permission, "allowed": allowed}


class CompareRequest(BaseModel):
    image_a: str
    image_b: str


@router.post("/compare")
async def vision_compare(req: CompareRequest) -> dict[str, Any]:
    result = await vision_manager.compare(req.image_a, req.image_b)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Comparison failed."))
    return result


@router.post("/camera/start")
async def vision_camera_start() -> dict[str, Any]:
    result = await vision_manager.camera_start()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Camera start failed."))
    return result


@router.post("/camera/stop")
async def vision_camera_stop() -> dict[str, Any]:
    result = await vision_manager.camera_stop()
    return result


@router.post("/camera/capture")
async def vision_camera_capture() -> dict[str, Any]:
    result = await vision_manager.camera_capture()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Camera capture failed."))
    return result


class RegionAnalyzeRequest(BaseModel):
    image_path: str
    region: str
    prompt: str = ""


@router.post("/region/analyze")
async def vision_region_analyze(req: RegionAnalyzeRequest) -> dict[str, Any]:
    parsed = parse_region(req.region)
    if parsed is None:
        raise HTTPException(status_code=400, detail="Invalid region format. Use WxH+X+Y.")
    cropped = crop_region(req.image_path, parsed)
    if not cropped.get("ok"):
        raise HTTPException(status_code=500, detail=cropped.get("error", "Region crop failed."))
    result = await vision_manager.analyze(cropped["path"], prompt=req.prompt, mode="describe")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Region analysis failed."))
    return result


class RememberVisualRequest(BaseModel):
    image_path: str
    description: str
    tags: list[str] = []
    project: str = ""


@router.post("/remember")
async def vision_remember(req: RememberVisualRequest) -> dict[str, Any]:
    result = await vision_manager.remember_visual(req.image_path, req.description, tags=req.tags, project=req.project)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Remember visual failed."))
    return result


class VisualQARequest(BaseModel):
    image_path: str
    question: str


@router.post("/qa")
async def vision_qa(req: VisualQARequest) -> dict[str, Any]:
    from vision.question_answering import visual_qa
    result = await visual_qa.answer(req.image_path, req.question)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("answer", "Visual QA failed."))
    return result


@router.get("/windows")
async def vision_windows() -> dict[str, Any]:
    from vision.screen import get_screen_provider
    provider = get_screen_provider()
    return await provider.list_windows()


@router.get("/cameras")
async def vision_cameras() -> dict[str, Any]:
    from vision.camera import CameraManager
    manager = CameraManager()
    return manager.list_cameras()


@router.post("/sensitive/check")
async def vision_sensitive_check(request: dict):
    from vision.sensitive import sensitive_detector
    text = request.get("text", "")
    window_title = request.get("window_title", "")
    is_sensitive, reason = sensitive_detector.is_sensitive_screen(text, window_title)
    return {"sensitive": is_sensitive, "reason": reason}


@router.post("/sensitive/redact")
async def vision_sensitive_redact(request: dict):
    from vision.sensitive import sensitive_detector
    text = request.get("text", "")
    redacted = sensitive_detector.redact(text)
    return {"redacted": redacted}


class ApplicationUnderstandRequest(BaseModel):
    window_title: str = ""
    ocr_text: str = ""


@router.post("/application/understand")
async def vision_application_understand(req: ApplicationUnderstandRequest) -> dict[str, Any]:
    result = await vision_manager.understand_application(req.window_title, req.ocr_text)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Application understanding failed."))
    return result


class DialogDetectRequest(BaseModel):
    ocr_text: str
    window_title: str = ""


@router.post("/dialog/detect")
async def vision_dialog_detect(req: DialogDetectRequest) -> dict[str, Any]:
    result = await vision_manager.detect_dialog(req.ocr_text, req.window_title)
    return result


class WorkflowRecordRequest(BaseModel):
    name: str = ""


@router.post("/workflow/start")
async def vision_workflow_start(req: WorkflowRecordRequest) -> dict[str, Any]:
    result = await vision_manager.start_workflow_recording(req.name)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Workflow start failed."))
    return result


@router.post("/workflow/stop")
async def vision_workflow_stop() -> dict[str, Any]:
    result = await vision_manager.stop_workflow_recording()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Workflow stop failed."))
    return result


class WorkflowReplayRequest(BaseModel):
    workflow: dict[str, Any]
    re_detect: bool = True


@router.post("/workflow/replay")
async def vision_workflow_replay(req: WorkflowReplayRequest) -> dict[str, Any]:
    result = await vision_manager.replay_workflow(req.workflow, req.re_detect)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Workflow replay failed.")
    return result


@router.get("/skills")
async def vision_skills() -> dict[str, Any]:
    result = await vision_manager.load_visual_skills()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Skills load failed."))
    return result


class SkillMatchRequest(BaseModel):
    text: str


@router.post("/skills/match")
async def vision_skill_match(req: SkillMatchRequest) -> dict[str, Any]:
    result = await vision_manager.match_visual_skill(req.text)
    return result


@router.post("/gesture/start")
async def vision_gesture_start() -> dict[str, Any]:
    result = await vision_manager.gesture_start()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Gesture start failed."))
    return result


@router.post("/gesture/stop")
async def vision_gesture_stop() -> dict[str, Any]:
    result = await vision_manager.gesture_stop()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Gesture stop failed."))
    return result


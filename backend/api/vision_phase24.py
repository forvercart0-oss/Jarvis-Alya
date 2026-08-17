"""Vision Phase 24 API routes for JARVIS.

Adds screen intelligence, query, diff, action planning, verification,
wait-for-element, and accessibility endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ws_manager import ws_manager
from vision.screen_intelligence import ScreenIntelligenceMode, screen_intelligence

logger = logging.getLogger("jarvis.api.vision_phase24")

router = APIRouter(prefix="/vision24", tags=["vision24"])


class ScreenModeRequest(BaseModel):
    mode: str = "on_demand"


class ScreenCaptureRequest(BaseModel):
    mode: str = "full"
    window: str | None = None
    region: str | None = None
    monitor: int | None = None


class CommandRequest(BaseModel):
    command: str
    context: dict[str, Any] | None = None


class FindElementRequest(BaseModel):
    target: str
    region: str | None = None


class WaitForRequest(BaseModel):
    target: str
    timeout: float = 10.0
    poll_interval: float = 0.5


class DiffRequest(BaseModel):
    current_ocr: str
    current_window: str
    current_elements: list[dict[str, Any]] | None = None
    current_image_hash: str


@router.get("/status")
async def screen_intelligence_status() -> dict[str, Any]:
    return {
        "enabled": screen_intelligence.enabled,
        "mode": screen_intelligence.mode,
    }


@router.post("/mode")
async def set_screen_mode(req: ScreenModeRequest) -> dict[str, Any]:
    mode = req.mode.lower()
    if mode not in (ScreenIntelligenceMode.OFF, ScreenIntelligenceMode.ON_DEMAND, ScreenIntelligenceMode.CONTINUOUS):
        raise HTTPException(status_code=400, detail="Invalid mode. Use off, on_demand, or continuous.")
    screen_intelligence.mode = mode
    screen_intelligence.enabled = mode != ScreenIntelligenceMode.OFF
    return {"success": True, "mode": mode, "enabled": screen_intelligence.enabled}


@router.post("/capture")
async def screen_intelligence_capture(req: ScreenCaptureRequest) -> dict[str, Any]:
    await ws_manager.broadcast("screen_capture_started", {"mode": req.mode})
    result = await screen_intelligence.capture_and_understand(
        mode=req.mode,
        window=req.window,
        region=req.region,
        monitor=req.monitor,
    )
    if not result.get("success"):
        await ws_manager.broadcast("screen_capture_complete", {"success": False, "error": result.get("error")})
        raise HTTPException(status_code=500, detail=result.get("error", "Capture failed"))
    await ws_manager.broadcast("screen_capture_complete", {"success": True, "image_path": result.get("image_path")})
    return result


@router.post("/command")
async def screen_intelligence_command(req: CommandRequest) -> dict[str, Any]:
    await ws_manager.broadcast("screen_analysis_started", {"command": req.command})
    result = await screen_intelligence.execute_command(req.command, req.context)
    await ws_manager.broadcast("screen_analysis_complete", {"success": result.get("success")})
    return result


@router.post("/query")
async def screen_intelligence_query(req: CommandRequest) -> dict[str, Any]:
    try:
        from vision.screen_query import screen_query_engine
        result = await screen_query_engine.query(req.command, req.context)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/diff")
async def screen_intelligence_diff(req: DiffRequest) -> dict[str, Any]:
    try:
        from vision.screen_diff import screen_diff_engine
        elements = req.current_elements or []
        diff = screen_diff_engine.diff(req.current_ocr, req.current_window, elements, req.current_image_hash)
        return diff.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/find")
async def screen_intelligence_find(req: FindElementRequest) -> dict[str, Any]:
    try:
        from vision.screen_query import screen_query_engine
        result = await screen_query_engine.query(f"find {req.target}")
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/wait_for_element")
async def wait_for_element_endpoint(req: WaitForRequest) -> dict[str, Any]:
    try:
        from vision.wait_for_element import wait_for_element
        async def check():
            from vision.screen_query import screen_query_engine
            return await screen_query_engine.query(f"find {req.target}")
        result = await wait_for_element.wait_for_element(check, timeout=req.timeout, poll_interval=req.poll_interval)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/wait_for_page")
async def wait_for_page_endpoint(timeout: float = 10.0) -> dict[str, Any]:
    try:
        from vision.wait_for_element import smart_wait
        return await smart_wait.wait_for_page_load(timeout=timeout)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/wait_for_dialog")
async def wait_for_dialog_endpoint(timeout: float = 10.0) -> dict[str, Any]:
    try:
        from vision.wait_for_element import smart_wait
        return await smart_wait.wait_for_dialog(timeout=timeout)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/understanding")
async def get_last_understanding() -> dict[str, Any]:
    try:
        understanding = screen_intelligence._get_understanding_engine().get_last_understanding()
        if understanding:
            return understanding.to_dict()
        return {"success": False, "error": "No understanding available"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/action_log")
async def get_action_log(limit: int = 50) -> dict[str, Any]:
    try:
        from vision.action_log import action_logger
        entries = action_logger.get_entries(limit)
        return {"success": True, "entries": entries}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/action_log/clear")
async def clear_action_log() -> dict[str, Any]:
    try:
        from vision.action_log import action_logger
        action_logger.clear()
        return {"success": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/accessibility/status")
async def accessibility_status() -> dict[str, Any]:
    try:
        from vision.accessibility import get_adapter
        adapter = get_adapter()
        if not adapter:
            return {"status": "unavailable", "error": "No adapter for this platform"}
        health = await adapter.health_check()
        return health
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/accessibility/tree")
async def accessibility_tree() -> dict[str, Any]:
    try:
        from vision.accessibility import get_adapter
        adapter = get_adapter()
        if not adapter:
            return {"success": False, "error": "No adapter for this platform"}
        tree = await adapter.get_element_tree()
        return {"success": True, "elements": [e.to_dict() for e in tree]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/redact")
async def redact_screen_text(request: dict) -> dict[str, Any]:
    from vision.sensitive import sensitive_detector
    text = request.get("text", "")
    redacted = sensitive_detector.redact(text)
    return {"redacted": redacted}


class PlanRequest(BaseModel):
    command: str


@router.post("/plan")
async def plan_screen_command(req: PlanRequest) -> dict[str, Any]:
    try:
        from vision.action_planner import visual_action_planner
        plan = visual_action_planner.plan(req.command)
        return plan.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

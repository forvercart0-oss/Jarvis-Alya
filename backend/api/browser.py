"""Browser API for JARVIS 2.0 Phase 9."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.browser")

router = APIRouter()


class BrowserNavigateRequest(BaseModel):
    url: str
    session_id: str = "default"


class BrowserActionRequest(BaseModel):
    action: str
    session_id: str = "default"
    selector: str | None = None
    text: str | None = None
    url: str | None = None
    key: str | None = None
    direction: str = "down"
    amount: int = 500
    seconds: float = 1.0
    full_page: bool = False
    tab_id: str | None = None


class BrowserSessionRequest(BaseModel):
    browser: str = "chromium"
    headless: bool = True


def _get_browser():
    from backend.main import browser_manager
    from browser.manager import BrowserManager
    if browser_manager is None:
        browser_manager = BrowserManager()
    return browser_manager


@router.post("/browser/session")
async def create_browser_session(request: BrowserSessionRequest):
    mgr = _get_browser()
    if not mgr.available:
        await mgr.initialize(browser=request.browser, headless=request.headless)
    return {"status": "started", "browser": request.browser, "headless": request.headless}


@router.get("/browser/sessions")
async def list_browser_sessions():
    from browser.sessions import get_browser_session_manager
    mgr = get_browser_session_manager()
    return {"sessions": [s.to_dict() for s in mgr._sessions.values()]}


@router.get("/browser/session/{session_id}")
async def get_browser_session(session_id: str):
    mgr = _get_browser()
    result = await mgr.session_status(session_id)
    return result


@router.post("/browser/session/{session_id}/navigate")
async def browser_navigate(session_id: str, request: BrowserNavigateRequest):
    mgr = _get_browser()
    result = await mgr.navigate(request.url, session_id)
    return result


@router.post("/browser/session/{session_id}/action")
async def browser_action(session_id: str, request: BrowserActionRequest):
    mgr = _get_browser()
    action = request.action.lower()
    if action == "navigate" and request.url:
        return await mgr.navigate(request.url, session_id)
    if action == "back":
        return await mgr.go_back(session_id)
    if action == "forward":
        return await mgr.go_forward(session_id)
    if action == "reload":
        return await mgr.reload(session_id)
    if action == "click" and request.selector:
        return await mgr.click(request.selector, session_id)
    if action == "type" and request.selector and request.text:
        return await mgr.type_text(request.selector, request.text, session_id)
    if action == "press" and request.key:
        return await mgr.press(request.key, session_id)
    if action == "scroll":
        return await mgr.scroll(request.direction, request.amount, session_id)
    if action == "wait":
        return await mgr.wait(request.seconds, session_id)
    if action == "read":
        return await mgr.get_content(session_id)
    if action == "extract_links":
        return await mgr.extract_links(session_id)
    if action == "screenshot":
        return await mgr.screenshot(session_id, request.full_page)
    if action == "open_tab" and request.url:
        return await mgr.open_tab(request.url, session_id)
    if action == "close_tab" and request.tab_id:
        return await mgr.close_tab(request.tab_id, session_id)
    if action == "switch_tab" and request.tab_id:
        return await mgr.switch_tab(request.tab_id, session_id)
    if action == "download" and request.url:
        return await mgr.download(request.url, session_id)
    raise HTTPException(status_code=400, detail=f"Unknown browser action: {request.action}")


@router.post("/browser/session/{session_id}/pause")
async def browser_pause(session_id: str):
    return {"status": "paused", "session_id": session_id}


@router.post("/browser/session/{session_id}/resume")
async def browser_resume(session_id: str):
    return {"status": "resumed", "session_id": session_id}


@router.post("/browser/session/{session_id}/stop")
async def browser_stop(session_id: str):
    mgr = _get_browser()
    await mgr.shutdown()
    return {"status": "stopped", "session_id": session_id}


@router.get("/browser/status")
async def browser_status():
    mgr = _get_browser()
    status = await mgr.session_status()
    return status


@router.get("/browser/session/{session_id}/page/context")
async def browser_page_context(session_id: str):
    mgr = _get_browser()
    result = await mgr.get_page_context(session_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to get page context"))
    return result


@router.post("/browser/element/find")
async def browser_find_element(request: dict):
    target = request.get("target", "")
    session_id = request.get("session_id", "default")
    if not target:
        raise HTTPException(status_code=400, detail="Target required")
    mgr = _get_browser()
    result = await mgr.find_element(target, session_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Element not found"))
    return result


@router.post("/browser/take-control")
async def browser_take_control(request: dict):
    session_id = request.get("session_id", "default")
    from browser.takeover import browser_takeover
    return browser_takeover.enable(session_id)


@router.post("/browser/release-control")
async def browser_release_control(request: dict):
    session_id = request.get("session_id", "default")
    from browser.takeover import browser_takeover
    return browser_takeover.disable(session_id)


@router.get("/browser/takeover/status")
async def browser_takeover_status(session_id: str = "default"):
    from browser.takeover import browser_takeover
    return browser_takeover.status(session_id)


@router.post("/browser/check/captcha")
async def browser_check_captcha(request: dict):
    session_id = request.get("session_id", "default")
    mgr = _get_browser()
    result = await mgr.is_captcha(session_id)
    return result


@router.post("/browser/check/login")
async def browser_check_login(request: dict):
    session_id = request.get("session_id", "default")
    mgr = _get_browser()
    result = await mgr.is_login_page(session_id)
    return result


@router.post("/browser/check/purchase")
async def browser_check_purchase(request: dict):
    session_id = request.get("session_id", "default")
    mgr = _get_browser()
    result = await mgr.is_purchase_page(session_id)
    return result

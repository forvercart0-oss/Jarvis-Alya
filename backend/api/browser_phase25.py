"""Browser Phase 25 API routes for JARVIS.

Adds advanced browser intelligence, page inspection, DOM analysis,
element resolution, download manager, upload support, page reading,
page summarization, table extraction, page diff, verification, recovery,
anti-loop, memory, and WebSocket events.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ws_manager import ws_manager
from browser.browser_anti_loop import browser_anti_loop
from browser.browser_intelligence import browser_intelligence
from browser.browser_memory import browser_memory_store
from browser.browser_recovery import browser_recovery_engine
from browser.browser_verification import browser_verifier
from browser.dom_analyzer import dom_analyzer
from browser.download_manager import browser_download_manager
from browser.element_resolver import element_resolver
from browser.page_diff import page_diff_engine
from browser.page_inspector import page_inspector
from browser.page_reader import web_page_reader
from browser.page_summarizer import page_summarizer
from browser.table_extractor import table_extractor
from browser.upload_manager import browser_upload_manager

logger = logging.getLogger("jarvis.api.browser_phase25")

router = APIRouter(prefix="/browser25", tags=["browser25"])


class BrowserGoalRequest(BaseModel):
    goal: str
    session_id: str = "default"


class BrowserReadRequest(BaseModel):
    mode: str = "normal"
    session_id: str = "default"


class BrowserUploadRequest(BaseModel):
    selector: str
    file_path: str
    session_id: str = "default"


class BrowserDiffRequest(BaseModel):
    session_id: str = "default"


@router.get("/status")
async def browser25_status() -> dict[str, Any]:
    return {
        "enabled": browser_intelligence.enabled,
        "downloads": [d.to_dict() for d in browser_download_manager.get_recent(5)],
    }


@router.post("/enable")
async def browser25_enable() -> dict[str, Any]:
    browser_intelligence.enabled = True
    return {"success": True, "enabled": True}


@router.post("/disable")
async def browser25_disable() -> dict[str, Any]:
    browser_intelligence.enabled = False
    return {"success": True, "enabled": False}


@router.post("/task")
async def browser25_task(request: BrowserGoalRequest) -> dict[str, Any]:
    await ws_manager.broadcast("browser_task_started", {"goal": request.goal, "session_id": request.session_id})
    result = await browser_intelligence.execute_task(request.goal, request.session_id)
    await ws_manager.broadcast("browser_task_completed", {"goal": request.goal, "success": result.get("success")})
    return result


@router.get("/page/inspect")
async def browser25_inspect(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        inspected = await page_inspector.inspect(page)
        return {"success": True, "page": inspected.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/page/dom")
async def browser25_dom(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        elements = await dom_analyzer.analyze(page)
        return {"success": True, "elements": [e.to_dict() for e in elements]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/element/resolve")
async def browser25_resolve(request: BrowserGoalRequest) -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        from browser.page_context import page_context_extractor
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(request.session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        page_context = await page_context_extractor.extract(page)
        resolved = await element_resolver.resolve(request.goal, page_context, page)
        if resolved:
            return {"success": True, "element": resolved.to_dict()}
        return {"success": False, "error": f"Element not resolved: {request.goal}"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/page/read")
async def browser25_read(mode: str = "normal", session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        result = await web_page_reader.read(page, mode=mode)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/page/summarize")
async def browser25_summarize(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        from browser.page_context import page_context_extractor
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        page_context = await page_context_extractor.extract(page)
        summary = await page_summarizer.summarize(page_context, page)
        return summary
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/page/tables")
async def browser25_tables(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        tables = await table_extractor.extract_tables(page)
        return {"success": True, "tables": tables}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/upload")
async def browser25_upload(request: BrowserUploadRequest) -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(request.session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        result = await browser_upload_manager.upload(page, request.selector, request.file_path)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/downloads")
async def browser25_downloads(limit: int = 20) -> dict[str, Any]:
    downloads = browser_download_manager.get_recent(limit)
    return {"success": True, "downloads": downloads}


@router.post("/page/diff")
async def browser25_diff(request: BrowserDiffRequest) -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(request.session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        url = page.url if hasattr(page, "url") else ""
        title = await page.title() if hasattr(page, "title") else ""
        text = await page.evaluate("() => document.body.innerText") if hasattr(page, "evaluate") else ""
        from browser.dom_analyzer import dom_analyzer
        elements = await dom_analyzer.analyze(page)
        diff = page_diff_engine.diff(url, title, text or "", [e.to_dict() for e in elements])
        return diff.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/verify")
async def browser25_verify(request: dict) -> dict[str, Any]:
    try:
        action = request.get("action", "")
        session_id = request.get("session_id", "default")
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        if action == "navigation":
            expected_url = request.get("expected_url", "")
            return await browser_verifier.verify_navigation(page, expected_url)
        if action == "element":
            selector = request.get("selector", "")
            return await browser_verifier.verify_element_present(page, selector)
        if action == "text":
            text = request.get("text", "")
            return await browser_verifier.verify_text_present(page, text)
        return {"success": False, "error": f"Unknown verification action: {action}"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recover")
async def browser25_recover(request: dict) -> dict[str, Any]:
    try:
        failed_action = request.get("failed_action", {})
        session_id = request.get("session_id", "default")
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        from browser.page_context import page_context_extractor
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        page_context = await page_context_extractor.extract(page)
        result = await browser_recovery_engine.recover(failed_action, page_context, page)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/memory")
async def browser25_memory(session_id: str = "default") -> dict[str, Any]:
    memory = browser_memory_store.get(session_id)
    return {
        "session_id": memory.session_id,
        "current_url": memory.current_url,
        "current_title": memory.current_title,
        "recent_actions": memory.recent_actions[-10:],
        "last_resolved_elements": memory.last_resolved_elements,
        "user_preferences": memory.user_preferences,
    }


@router.post("/memory/preference")
async def browser25_set_preference(request: dict) -> dict[str, Any]:
    session_id = request.get("session_id", "default")
    key = request.get("key", "")
    value = request.get("value", "")
    if not key:
        raise HTTPException(status_code=400, detail="Key required")
    memory = browser_memory_store.get(session_id)
    memory.set_preference(key, value)
    return {"success": True, "key": key, "value": value}


@router.get("/detect/login")
async def browser25_detect_login(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        from browser.page_context import page_context_extractor
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        page_context = await page_context_extractor.extract(page)
        return {
            "is_login": page_context_extractor.detect_login_page(page_context),
            "is_captcha": page_context_extractor.detect_captcha(page_context),
            "is_mfa": page_context_extractor.detect_mfa(page_context),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/detect/errors")
async def browser25_detect_errors(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        text = await page.evaluate("() => document.body.innerText") if hasattr(page, "evaluate") else ""
        url = page.url if hasattr(page, "url") else ""
        error_patterns = ["404", "403", "500", "error", "exception", "traceback", "failed", "not found"]
        errors = []
        for line in (text or "").splitlines():
            if any(p in line.lower() for p in error_patterns):
                errors.append(line.strip())
        return {"success": True, "errors": errors[:10], "url": url}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/anti-loop/reset")
async def browser25_anti_loop_reset(session_id: str = "default") -> dict[str, Any]:
    browser_anti_loop.reset(session_id)
    return {"success": True}


@router.get("/page/structure")
async def browser25_page_structure(session_id: str = "default") -> dict[str, Any]:
    try:
        from backend.main import browser_manager as global_mgr
        from browser.manager import BrowserManager
        mgr = global_mgr if global_mgr else BrowserManager()
        if not mgr.available:
            raise HTTPException(status_code=503, detail="Browser not available")
        page = await mgr._get_page(session_id)
        if not page:
            raise HTTPException(status_code=404, detail="No active page")
        structure = await page.evaluate("""
            () => {
                const sections = [];
                document.querySelectorAll('header, nav, main, aside, footer, section, [role="dialog"], .modal').forEach(el => {
                    sections.push({
                        type: el.tagName.toLowerCase(),
                        role: el.getAttribute('role') || '',
                        text: (el.innerText || '').trim().slice(0, 200)
                    });
                });
                return sections;
            }
        """)
        return {"success": True, "structure": structure or []}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

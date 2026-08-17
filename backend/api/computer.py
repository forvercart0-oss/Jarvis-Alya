"""Computer API for JARVIS 2.0 Phase 10."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("jarvis.api.computer")

router = APIRouter()


class ComputerActionRequest(BaseModel):
    action: str
    arguments: dict[str, Any] | None = None
    session_id: str = "default"


class ComputerSessionRequest(BaseModel):
    mode: str = "observe"


class ComputerScreenshotRequest(BaseModel):
    mode: str = "full"
    region: str | None = None
    monitor: int | None = None


def _get_manager():
    from computer.manager import ComputerManager
    return ComputerManager()


@router.post("/computer/session")
async def create_computer_session(request: ComputerSessionRequest):
    from computer.session import get_computer_session_manager
    mgr = get_computer_session_manager()
    session = mgr.create("default")
    session.mode = request.mode
    return {"status": "started", "session_id": session.session_id, "mode": request.mode}


@router.get("/computer/status")
async def get_computer_status():
    from computer.platform import detect_platform
    from computer.safety import ComputerSafety
    platform = detect_platform()
    safety = ComputerSafety()
    return {
        "platform": platform,
        "available": True,
        "safety": {
            "dangerous_actions": list(safety.DANGEROUS_ACTIONS),
            "confirmation_actions": list(safety.CONFIRMATION_ACTIONS),
        }
    }


@router.get("/computer/windows")
async def list_computer_windows():
    mgr = _get_manager()
    result = mgr._run_platform("list_windows")
    return result


@router.get("/computer/monitors")
async def list_computer_monitors():
    try:
        from vision.capture import list_monitors
        result = await list_monitors()
        return result
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.post("/computer/screenshot")
async def computer_screenshot(request: ComputerScreenshotRequest):
    try:
        from vision.capture import capture_screen
        result = await capture_screen(request.mode, region=request.region, monitor=request.monitor)
        return result
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.post("/computer/action")
async def computer_action(request: ComputerActionRequest):
    from computer.session import get_computer_session_manager
    mgr = _get_manager()
    session_mgr = get_computer_session_manager()
    session_mgr.get(request.session_id) or session_mgr.create(request.session_id)

    action = request.action
    arguments = request.arguments or {}

    if action in ("get_cursor_position", "get_active_window", "list_windows", "get_screen_info"):
        result = mgr._run_platform(action)
        session_mgr.add_action(request.session_id, {"action": action, "arguments": arguments, "result": result})
        return result

    if not mgr._safety.is_allowed(action):
        result = {"success": False, "error": f"Action '{action}' is not permitted by safety policy."}
        session_mgr.add_action(request.session_id, {"action": action, "arguments": arguments, "result": result})
        return result

    if mgr._safety.requires_confirmation(action):
        result = {"success": False, "confirmation_required": True, "action": action, "arguments": arguments}
        session_mgr.add_action(request.session_id, {"action": action, "arguments": arguments, "result": result})
        return result

    try:
        result = mgr._run_platform(action, **arguments)
        session_mgr.add_action(request.session_id, {"action": action, "arguments": arguments, "result": result})
        return result
    except Exception as exc:
        result = {"success": False, "error": str(exc)}
        session_mgr.add_action(request.session_id, {"action": action, "arguments": arguments, "result": result})
        return result


@router.post("/computer/pause")
async def computer_pause():
    from computer.session import get_computer_session_manager
    mgr = get_computer_session_manager()
    session = mgr.get("default")
    if session:
        mgr.update("default", mode="paused")
    return {"status": "paused"}


@router.post("/computer/resume")
async def computer_resume():
    from computer.session import get_computer_session_manager
    mgr = get_computer_session_manager()
    session = mgr.get("default")
    if session:
        mgr.update("default", mode="observe")
    return {"status": "resumed"}


@router.post("/computer/stop")
async def computer_stop():
    from computer.session import get_computer_session_manager
    mgr = get_computer_session_manager()
    mgr.update("default", mode="off")
    return {"status": "stopped"}


@router.get("/computer/processes")
async def computer_processes():
    mgr = _get_manager()
    result = await mgr._handle_list_processes({})
    return result


@router.post("/computer/action/command")
async def computer_run_command(request: dict):
    command = request.get("command", "")
    timeout = request.get("timeout", 30)
    if not command:
        raise HTTPException(status_code=400, detail="Command required")
    mgr = _get_manager()
    result = await mgr._handle_run_command({"command": command, "timeout": timeout})
    return result


@router.post("/computer/files/list")
async def computer_files_list(request: dict):
    path = request.get("path", "")
    mgr = _get_manager()
    result = await mgr._handle_list_files({"path": path})
    return result


@router.post("/computer/files/search")
async def computer_files_search(request: dict):
    query = request.get("query", "")
    path = request.get("path", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query required")
    mgr = _get_manager()
    result = await mgr._handle_search_files({"query": query, "path": path})
    return result


@router.post("/computer/files/create")
async def computer_files_create(request: dict):
    path = request.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="Path required")
    mgr = _get_manager()
    result = await mgr._handle_create_folder({"path": path})
    return result


@router.post("/computer/files/rename")
async def computer_files_rename(request: dict):
    old_path = request.get("old_path", "")
    new_name = request.get("new_name", "")
    if not old_path or not new_name:
        raise HTTPException(status_code=400, detail="old_path and new_name required")
    mgr = _get_manager()
    result = await mgr._handle_rename_file({"old_path": old_path, "new_name": new_name})
    return result


@router.post("/computer/files/move")
async def computer_files_move(request: dict):
    src = request.get("src", "")
    dst = request.get("dst", "")
    if not src or not dst:
        raise HTTPException(status_code=400, detail="src and dst required")
    mgr = _get_manager()
    result = await mgr._handle_move_file({"src": src, "dst": dst})
    return result


@router.post("/computer/files/copy")
async def computer_files_copy(request: dict):
    src = request.get("src", "")
    dst = request.get("dst", "")
    if not src or not dst:
        raise HTTPException(status_code=400, detail="src and dst required")
    mgr = _get_manager()
    result = await mgr._handle_copy_file({"src": src, "dst": dst})
    return result


@router.post("/computer/files/delete")
async def computer_files_delete(request: dict):
    path = request.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="Path required")
    mgr = _get_manager()
    result = await mgr._handle_delete_file({"path": path})
    return result


@router.post("/computer/files/open")
async def computer_files_open(request: dict):
    path = request.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="Path required")
    mgr = _get_manager()
    result = await mgr._handle_open_file({"path": path})
    return result


@router.post("/computer/clipboard/read")
async def computer_clipboard_read():
    mgr = _get_manager()
    result = await mgr._handle_read_clipboard({})
    return result


@router.post("/computer/clipboard/write")
async def computer_clipboard_write(request: dict):
    text = request.get("text", "")
    mgr = _get_manager()
    result = await mgr._handle_write_clipboard({"text": text})
    return result


@router.post("/computer/terminal/open")
async def computer_terminal_open(request: dict):
    command = request.get("command", "")
    mgr = _get_manager()
    result = await mgr._handle_open_terminal({"command": command})
    return result


@router.post("/computer/take-control")
async def computer_take_control(request: dict):
    session_id = request.get("session_id", "default")
    from computer.takeover import computer_takeover
    return computer_takeover.enable(session_id)


@router.post("/computer/release-control")
async def computer_release_control(request: dict):
    session_id = request.get("session_id", "default")
    from computer.takeover import computer_takeover
    return computer_takeover.disable(session_id)


@router.get("/computer/takeover/status")
async def computer_takeover_status(session_id: str = "default"):
    from computer.takeover import computer_takeover
    return computer_takeover.status(session_id)


@router.get("/computer/permissions")
async def computer_permissions():
    from computer.trust import computer_permission_manager
    return computer_permission_manager.list_permissions()

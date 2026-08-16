"""Vision-specific permission helpers for JARVIS Phase 4."""

from __future__ import annotations

from typing import Any


async def vision_read_screen(permission_manager: Any = None) -> dict[str, Any]:
    pm = permission_manager or _get_permission_manager()
    ok = pm.is_allowed("vision.read_screen")
    return {"allowed": ok, "permission": "vision.read_screen"}


async def vision_capture(permission_manager: Any = None) -> dict[str, Any]:
    pm = permission_manager or _get_permission_manager()
    ok = pm.is_allowed("vision.capture")
    return {"allowed": ok, "permission": "vision.capture"}


async def vision_analyze(permission_manager: Any = None) -> dict[str, Any]:
    pm = permission_manager or _get_permission_manager()
    ok = pm.is_allowed("vision.analyze")
    return {"allowed": ok, "permission": "vision.analyze"}


async def computer_mouse(permission_manager: Any = None) -> dict[str, Any]:
    pm = permission_manager or _get_permission_manager()
    ok = pm.is_allowed("computer.mouse")
    return {"allowed": ok, "permission": "computer.mouse"}


async def computer_keyboard(permission_manager: Any = None) -> dict[str, Any]:
    pm = permission_manager or _get_permission_manager()
    ok = pm.is_allowed("computer.keyboard")
    return {"allowed": ok, "permission": "computer.keyboard"}


def check_vision_permission(permission: str, permission_manager: Any = None) -> bool:
    pm = permission_manager or _get_permission_manager()
    return pm.is_allowed(permission)


def check_computer_permission(permission: str, permission_manager: Any = None) -> bool:
    pm = permission_manager or _get_permission_manager()
    return pm.is_allowed(permission)


def _get_permission_manager():
    try:
        from backend.main import permission_manager as pm
        return pm
    except Exception:
        try:
            from permissions.manager import PermissionManager
            from pathlib import Path
            from config.settings import get_settings
            return PermissionManager(Path(get_settings().data_dir) / "permissions.json")
        except Exception:
            class _Dummy:
                def is_allowed(self, perm): return True
            return _Dummy()

"""Updater API routes for JARVIS Phase 31."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ws_manager import ws_manager
from updater.models import UpdateState

logger = logging.getLogger("jarvis.api.updater")

router = APIRouter(prefix="/api/updater", tags=["updater"])


class UpdaterCheckRequest(BaseModel):
    force: bool = False


class UpdaterInstallRequest(BaseModel):
    commit_sha: str | None = None


class UpdaterConfigRequest(BaseModel):
    enabled: bool | None = None
    auto_check: bool | None = None
    check_interval_hours: int | None = None
    auto_download: bool | None = None
    auto_install: bool | None = None
    install_on_metered: bool | None = None
    require_confirmation: bool | None = None


_updater_service = None


def _get_updater():
    global _updater_service
    if _updater_service is None:
        from backend.services.updater_service import updater_service
        _updater_service = updater_service
    return _updater_service


@router.get("/status")
async def updater_status() -> dict[str, Any]:
    return _get_updater().get_status()


@router.post("/check")
async def updater_check(req: UpdaterCheckRequest) -> dict[str, Any]:
    progress = await _get_updater().check_for_update(force=req.force)
    await ws_manager.broadcast("updater_status", progress.to_dict())
    return progress.to_dict()


@router.post("/download")
async def updater_download() -> dict[str, Any]:
    progress = _get_updater().progress
    if progress.available_update is None:
        raise HTTPException(status_code=400, detail="No update available")
    await ws_manager.broadcast("updater_status", progress.to_dict())
    return progress.to_dict()


@router.post("/install")
async def updater_install(req: UpdaterInstallRequest) -> dict[str, Any]:
    progress = _get_updater().progress
    if progress.state not in (UpdateState.READY_TO_INSTALL, UpdateState.DOWNLOADED):
        raise HTTPException(status_code=400, detail="Update not ready")
    await ws_manager.broadcast("updater_status", progress.to_dict())
    return progress.to_dict()


@router.post("/cancel")
async def updater_cancel() -> dict[str, Any]:
    _get_updater().progress.state = UpdateState.IDLE
    _get_updater().progress.message = "Cancelled"
    await ws_manager.broadcast("updater_status", _get_updater().progress.to_dict())
    return _get_updater().progress.to_dict()


@router.get("/config")
async def updater_config() -> dict[str, Any]:
    return _get_updater().get_status()["config"]


@router.post("/config")
async def updater_update_config(req: UpdaterConfigRequest) -> dict[str, Any]:
    config = _get_updater().config
    if req.enabled is not None:
        config.enabled = req.enabled
    if req.auto_check is not None:
        config.auto_check = req.auto_check
    if req.check_interval_hours is not None:
        config.check_interval_hours = max(1, req.check_interval_hours)
    if req.auto_download is not None:
        config.auto_download = req.auto_download
    if req.auto_install is not None:
        config.auto_install = req.auto_install
    if req.install_on_metered is not None:
        config.install_on_metered = req.install_on_metered
    if req.require_confirmation is not None:
        config.require_confirmation = req.require_confirmation
    return config.to_dict()

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from permissions.registry import requested_permissions_full
from safety.activity import get_activity_logger
from skills.validator import SkillValidationError

router = APIRouter()


class SkillImportRequest(BaseModel):
    json: str


def _parse_skill_json(json_text: str) -> dict[str, Any]:
    try:
        return json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc


@router.get("/skills")
async def list_skills():
    from backend.main import skill_manager
    return skill_manager.list_skills()


@router.get("/skills/activity")
async def get_skill_activity(limit: int = 100):
    from backend.main import skill_manager
    return skill_manager.get_activity_log(limit)


@router.post("/skills/reload")
async def reload_all_skills():
    from backend.main import skill_registry
    skill_registry.reload()
    return {"status": "reloaded"}


@router.post("/skills/import/review")
async def review_skill_import(request: SkillImportRequest):
    """Validate imported skill JSON and report requested permissions without
    registering anything. Lets the user approve permissions first."""
    from backend.main import skill_manager
    try:
        skill = skill_manager.validate_skill(_parse_skill_json(request.json))
    except SkillValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "valid": True,
        "id": skill["id"],
        "name": skill.get("name"),
        "requested_permissions": requested_permissions_full(skill),
    }


@router.post("/skills/import")
async def import_skill(request: SkillImportRequest):
    from backend.main import skill_manager
    try:
        skill_id = skill_manager.import_skill(request.json)
        skill = skill_manager.get_skill(skill_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_activity_logger().log(skill=skill_id, action="skill.import", result="ok")
    return {
        "status": "imported",
        "id": skill_id,
        "requested_permissions": requested_permissions_full(skill) if skill else {},
    }


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    from backend.main import skill_manager
    skill = skill_manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/skills")
async def create_skill(skill_data: dict):
    from backend.main import skill_manager
    try:
        skill_id = skill_manager.install_skill(skill_data)
        skill = skill_manager.get_skill(skill_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_activity_logger().log(skill=skill_id, action="skill.create", result="ok")
    return {
        "id": skill_id,
        "requested_permissions": requested_permissions_full(skill) if skill else {},
    }


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, updates: dict):
    from backend.main import skill_manager, skill_registry
    try:
        ok = skill_manager.update_skill(skill_id, updates)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill_manager.save_skill_to_disk(skill_id, skill_registry.custom_dir)
    get_activity_logger().log(skill=skill_id, action="skill.update", result="ok")
    return {"status": "updated", "id": skill_id}


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    from backend.main import skill_manager
    skill = skill_manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    if skill.get("_source") == "builtin":
        raise HTTPException(status_code=400, detail="Cannot delete a builtin skill")
    if not skill_manager.delete_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    get_activity_logger().log(skill=skill_id, action="skill.delete", result="ok")
    return {"status": "deleted", "id": skill_id}


@router.post("/skills/{skill_id}/enable")
async def enable_skill(skill_id: str):
    from backend.main import skill_manager
    if not skill_manager.enable_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "enabled", "id": skill_id}


@router.post("/skills/{skill_id}/disable")
async def disable_skill(skill_id: str):
    from backend.main import skill_manager
    if not skill_manager.disable_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "disabled", "id": skill_id}


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str, body: dict | None = None):
    from backend.main import skill_manager
    skill = skill_manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    enabled = bool(body and body.get("enabled", not skill.get("enabled", False)))
    ok = skill_manager.enable_skill(skill_id) if enabled else skill_manager.disable_skill(skill_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "ok", "id": skill_id, "enabled": enabled}


@router.post("/skills/{skill_id}/reload")
async def reload_skill(skill_id: str):
    from backend.main import skill_manager, skill_registry
    skill = skill_manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill_manager.save_skill_to_disk(skill_id, skill_registry.custom_dir)
    skill_registry.reload()
    return {"status": "reloaded", "id": skill_id}


@router.get("/skills/{skill_id}/export")
async def export_skill(skill_id: str):
    from backend.main import skill_manager
    try:
        data = skill_manager.export_skill(skill_id)
        return {"id": skill_id, "json": data}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Skill not found") from exc

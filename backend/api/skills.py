from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()


class SkillImportRequest(BaseModel):
    json: str


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


@router.post("/skills/import")
async def import_skill(request: SkillImportRequest):
    from backend.main import skill_manager
    try:
        skill_id = skill_manager.import_skill(request.json)
        return {"status": "imported", "id": skill_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
        skill_id = skill_manager.create_skill(skill_data)
        return {"id": skill_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, updates: dict):
    from backend.main import skill_manager
    ok = skill_manager.update_skill(skill_id, updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "updated", "id": skill_id}


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    from backend.main import skill_manager
    ok = skill_manager.delete_skill(skill_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "deleted", "id": skill_id}


@router.post("/skills/{skill_id}/enable")
async def enable_skill(skill_id: str):
    from backend.main import skill_manager
    ok = skill_manager.enable_skill(skill_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "enabled", "id": skill_id}


@router.post("/skills/{skill_id}/disable")
async def disable_skill(skill_id: str):
    from backend.main import skill_manager
    ok = skill_manager.disable_skill(skill_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "disabled", "id": skill_id}


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str, body: Optional[dict] = None):
    from backend.main import skill_manager
    skill = skill_manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    enabled = bool(body and body.get("enabled", not skill.get("enabled", False)))
    if enabled:
        ok = skill_manager.enable_skill(skill_id)
    else:
        ok = skill_manager.disable_skill(skill_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "ok", "id": skill_id, "enabled": enabled}


@router.post("/skills/{skill_id}/reload")
async def reload_skill(skill_id: str):
    from backend.main import skill_manager, skill_registry
    skill = skill_manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill_manager.save_skill_to_disk(skill_id, skill_registry.base_dir)
    skill_registry.reload()
    return {"status": "reloaded", "id": skill_id}


@router.get("/skills/{skill_id}/export")
async def export_skill(skill_id: str):
    from backend.main import skill_manager
    try:
        data = skill_manager.export_skill(skill_id)
        return {"id": skill_id, "json": data}
    except KeyError:
        raise HTTPException(status_code=404, detail="Skill not found")

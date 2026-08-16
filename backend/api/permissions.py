
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from permissions.models import ALL_PERMISSIONS, PERMISSION_DESCRIPTIONS
from safety.activity import get_activity_logger

router = APIRouter()


class PermissionUpdate(BaseModel):
    permissions: dict[str, bool]


class BulkPermissionUpdate(BaseModel):
    skills: dict[str, dict[str, bool]]


def _definitions() -> dict[str, dict]:
    return {
        perm: {
            "label": PERMISSION_DESCRIPTIONS[perm].label,
            "description": PERMISSION_DESCRIPTIONS[perm].description,
            "risk": PERMISSION_DESCRIPTIONS[perm].risk,
        }
        for perm in ALL_PERMISSIONS
    }


@router.get("/permissions")
async def get_permissions():
    """Return the permission overview: definitions + per-skill granted state."""
    from backend.main import permission_manager, skill_registry
    return {
        "default_policy": "deny",
        "definitions": _definitions(),
        "skills": permission_manager.summary(skill_registry.list_all())["permissions"],
    }


@router.get("/permissions/{skill_id}")
async def get_skill_permissions(skill_id: str):
    from backend.main import permission_manager, skill_registry
    skill = skill_registry.get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {
        "skill_id": skill_id,
        "effective": permission_manager.effective(skill_id, skill),
        "granted": permission_manager.get_granted(skill_id),
        "pending": permission_manager.pending(skill_id, skill),
    }


@router.put("/permissions/{skill_id}")
async def update_skill_permissions(skill_id: str, update: PermissionUpdate):
    from backend.main import permission_manager, skill_registry
    skill = skill_registry.get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    granted = permission_manager.grant(skill_id, update.permissions)
    get_activity_logger().log(
        skill=skill_id,
        action="permissions.update",
        result="granted" if any(update.permissions.values()) else "revoked",
        detail={"permissions": update.permissions},
    )
    return {"skill_id": skill_id, "granted": granted}


@router.put("/permissions")
async def update_permissions(update: BulkPermissionUpdate):
    from backend.main import permission_manager
    for skill_id, perms in update.skills.items():
        permission_manager.grant(skill_id, perms)
    return {"status": "updated"}


@router.post("/permissions/reset")
async def reset_permissions():
    from backend.main import permission_manager
    count = permission_manager.reset()
    get_activity_logger().log(skill=None, action="permissions.reset", result="ok", detail={"count": count})
    return {"status": "reset", "count": count}


@router.delete("/permissions/{skill_id}")
async def reset_skill_permissions(skill_id: str):
    from backend.main import permission_manager
    permission_manager.reset_skill(skill_id)
    get_activity_logger().log(skill=skill_id, action="permissions.reset_skill", result="ok")
    return {"status": "reset"}

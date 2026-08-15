from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AutomationCreate(BaseModel):
    name: str
    trigger: str
    action: str
    schedule: Optional[str] = None
    keywords: Optional[list[str]] = None
    action_payload: Optional[dict] = None
    enabled: bool = True


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    trigger: Optional[str] = None
    action: Optional[str] = None
    schedule: Optional[str] = None
    keywords: Optional[list[str]] = None
    action_payload: Optional[dict] = None
    enabled: Optional[bool] = None


def _parse(data: dict) -> dict:
    result = dict(data)
    if isinstance(result.get("keywords"), str):
        result["keywords"] = [k.strip() for k in result["keywords"].split(",") if k.strip()]
    return result


@router.get("/automations")
async def list_automations():
    from backend.main import memory_manager
    return memory_manager.store.get_automations()


@router.post("/automations")
async def create_automation(automation: AutomationCreate):
    from backend.main import memory_manager
    payload = automation.model_dump(exclude_none=True)
    payload = _parse(payload)
    automation_id = memory_manager.store.add_automation(payload)
    return {"id": automation_id}


@router.put("/automations/{automation_id}")
async def update_automation(automation_id: str, updates: AutomationUpdate):
    from backend.main import memory_manager
    payload = updates.model_dump(exclude_none=True)
    payload = _parse(payload)
    memory_manager.store.update_automation(automation_id, payload)
    return {"status": "updated"}


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: str):
    from backend.main import memory_manager
    memory_manager.store.delete_automation(automation_id)
    return {"status": "deleted"}

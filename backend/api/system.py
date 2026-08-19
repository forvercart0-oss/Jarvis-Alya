from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CommandRequest(BaseModel):
    command: str
    confirm_required: bool = False


def _serialize(result):
    if hasattr(result, "_data"):
        return result._data
    if hasattr(result, "__dict__"):
        return result.__dict__
    return result


@router.get("/system/stats")
async def get_system_stats():
    from backend.main import system_service
    return system_service.full_stats()


@router.get("/system/history")
async def get_system_history():
    from backend.main import system_service
    return system_service.get_history()


@router.post("/system/command")
async def run_command(request: CommandRequest):
    from backend.main import tool_service
    result = await tool_service.execute(
        "terminal",
        command=request.command,
    )
    return _serialize(result)

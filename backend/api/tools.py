from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict = {}
    confirmed: bool = False


@router.get("/tools")
async def list_tools():
    from backend.main import tool_service
    return tool_service.list_tools()


@router.post("/tools/execute")
async def execute_tool(request: ToolExecuteRequest):
    from backend.main import tool_service
    result = await tool_service.execute(request.name, arguments=request.arguments, confirmed=request.confirmed)
    if hasattr(result, "_data"):
        return result._data
    if hasattr(result, "__dict__"):
        return result.__dict__
    return result

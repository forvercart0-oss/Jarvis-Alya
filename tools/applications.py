from tools.registry import ToolResult
from computer.controller import computer_controller


class OpenApplicationTool:
    name = "open_application"
    description = "Open a desktop application."
    parameters = {
        "type": "object",
        "properties": {"app_name": {"type": "string", "description": "Name of the application"}},
        "required": ["app_name"],
    }

    async def execute(self, app_name: str, **kwargs) -> ToolResult:
        result = await computer_controller.open_application(app_name)
        if result.get("ok"):
            return ToolResult(success=True, result={"application": app_name})
        return ToolResult(success=False, error=result.get("error", "Failed to open application."))


class CloseApplicationTool:
    name = "close_application"
    description = "Close a running application."
    parameters = {
        "type": "object",
        "properties": {"app_name": {"type": "string"}},
        "required": ["app_name"],
    }

    async def execute(self, app_name: str, **kwargs) -> ToolResult:
        result = await computer_controller.close_application(app_name)
        if result.get("ok"):
            return ToolResult(success=True)
        return ToolResult(success=False, error=result.get("error", "Failed to close application."))

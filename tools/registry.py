import asyncio
from typing import Any, Callable, Dict, Optional


class ToolResult:
    def __init__(self, success: bool, result: Any = None, error: str = "", confirmation_required: bool = False, confirmation_message: str = "", requires_confirmation: bool = False, **kwargs):
        self.success = success
        self.result = result
        self.error = error
        self.confirmation_required = confirmation_required or requires_confirmation
        self.confirmation_message = confirmation_message
        self._data = {
            "success": success,
            "result": result,
            "error": error,
            "confirmation_required": self.confirmation_required,
            "confirmation_message": confirmation_message,
        }
        if self.confirmation_required:
            self._data["requires_confirmation"] = True
        for k, v in kwargs.items():
            setattr(self, k, v)
            self._data[k] = v

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return repr(self._data)


class Tool:
    name: str = ""
    description: str = ""
    parameters: dict = {}

    async def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise AssertionError(f"Duplicate tool name: {tool.name}")
        self._tools[tool.name] = tool

    def register_handler(self, name: str, description: str, parameters: dict, handler: Callable):
        if name in self._handlers:
            raise AssertionError(f"Duplicate handler name: {name}")
        self._handlers[name] = handler
        _name = name
        _description = description
        _parameters = parameters
        class HandlerTool(Tool):
            name = _name
            description = _description
            parameters = _parameters
            async def execute(self_inner, **kwargs) -> ToolResult:
                kwargs.pop("confirmed", None)
                try:
                    result = handler(**kwargs)
                    if asyncio.iscoroutine(result):
                        result = await result
                    return ToolResult(success=True, result=result)
                except TypeError as exc:
                    return ToolResult(success=False, error=f"Invalid arguments: {exc}")
                except Exception as exc:
                    return ToolResult(success=False, error=str(exc))
        self.register(HandlerTool())

    def names(self):
        return list(self._tools.keys())

    def list_tools(self):
        result = []
        for name, tool in self._tools.items():
            result.append({
                "name": name,
                "description": tool.description,
                "requires_confirmation": getattr(tool, "requires_confirmation", False),
            })
        return result

    def tools_spec(self):
        spec = []
        for name, tool in self._tools.items():
            spec.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return spec

    async def execute(self, name: str, arguments: dict = None, confirmed: bool = False) -> ToolResult:
        arguments = dict(arguments or {})
        if "confirmed" in arguments:
            confirmed = arguments.pop("confirmed") or confirmed
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        try:
            result = await tool.execute(confirmed=confirmed, **arguments)
            if result.confirmation_required and not confirmed:
                return ToolResult(
                    success=False,
                    confirmation_required=True,
                    confirmation_message=result.confirmation_message or f"Please confirm {name}.",
                )
            return result
        except TypeError as exc:
            return ToolResult(success=False, error=f"Invalid arguments: {exc}")
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


def build_registry(db_path=None) -> ToolRegistry:
    from tools.terminal import TerminalTool
    from tools.filesystem import ReadFileTool, WriteFileTool, DeleteFileTool
    from tools.system import SystemInfoTool, CpuUsageTool, MemoryUsageTool, DiskUsageTool, BatteryStatusTool, LockScreenTool, ShutdownTool, RebootTool, SuspendTool, VolumeControlTool
    from tools.applications import OpenApplicationTool, CloseApplicationTool
    from tools.calculator import CalculatorTool
    from tools.time import TimeTool, DateTool
    from tools.web import WebSearchTool
    from tools.browser import OpenBrowserTool
    from tools.memory_tools import RememberTool, ForgetTool, RecallMemoriesTool
    from tools.projects import (
        ListProjectsTool, CreateProjectTool, DeleteProjectTool,
        ListProjectFilesTool, ReadProjectFileTool, WriteProjectFileTool,
        RunProjectCommandTool,
    )
    from tools.screen import (
        ScreenshotTool, BrightnessControlTool, DoNotDisturbTool,
        TypeTextTool, ClickTool,
    )
    from tools.media import GenerateImageTool, GenerateVideoTool
    from memory.manager import MemoryManager

    if hasattr(db_path, "store"):
        memory = db_path
    elif isinstance(db_path, str):
        memory = MemoryManager(db_path)
    else:
        memory = MemoryManager()

    registry = ToolRegistry()
    registry.register(TerminalTool())
    registry.register(CalculatorTool())
    registry.register(TimeTool())
    registry.register(DateTool())
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(DeleteFileTool())
    registry.register(SystemInfoTool())
    registry.register(CpuUsageTool())
    registry.register(MemoryUsageTool())
    registry.register(DiskUsageTool())
    registry.register(BatteryStatusTool())
    registry.register(LockScreenTool())
    registry.register(ShutdownTool())
    registry.register(RebootTool())
    registry.register(SuspendTool())
    registry.register(VolumeControlTool())
    registry.register(OpenApplicationTool())
    registry.register(CloseApplicationTool())
    registry.register(WebSearchTool())
    registry.register(OpenBrowserTool())
    registry.register(RememberTool(memory))
    registry.register(ForgetTool(memory))
    registry.register(RecallMemoriesTool(memory))
    registry.register(ListProjectsTool())
    registry.register(CreateProjectTool())
    registry.register(DeleteProjectTool())
    registry.register(ListProjectFilesTool())
    registry.register(ReadProjectFileTool())
    registry.register(WriteProjectFileTool())
    registry.register(RunProjectCommandTool())
    registry.register(ScreenshotTool())
    registry.register(BrightnessControlTool())
    registry.register(DoNotDisturbTool())
    registry.register(TypeTextTool())
    registry.register(ClickTool())
    registry.register(GenerateImageTool())
    registry.register(GenerateVideoTool())
    return registry

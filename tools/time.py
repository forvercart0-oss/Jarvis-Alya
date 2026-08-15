import datetime
from typing import Optional
from tools.registry import ToolResult


class TimeTool:
    name = "get_time"
    description = "Get the current time."
    parameters = {"type": "object", "properties": {"timezone": {"type": "string"}}}

    async def execute(self, timezone: str = "local", **kwargs) -> ToolResult:
        try:
            if timezone != "local":
                import pytz
                tz = pytz.timezone(timezone)
                now = datetime.datetime.now(tz)
            else:
                now = datetime.datetime.now().astimezone()
            return ToolResult(success=True, timezone=timezone, time=now.strftime("%H:%M:%S"), iso=now.isoformat())
        except Exception as exc:
            return ToolResult(success=False, error=f"Unknown timezone: {exc}")


class DateTool:
    name = "get_date"
    description = "Get the current date."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        now = datetime.datetime.now().astimezone()
        return ToolResult(
            success=True,
            date=now.date().isoformat(),
            weekday=now.strftime("%A"),
        )

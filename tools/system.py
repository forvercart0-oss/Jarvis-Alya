import platform
from tools.registry import ToolResult
import psutil

from computer.controller import computer_controller


class SystemInfoTool:
    name = "system_info"
    description = "Get system information."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, result=computer_controller.platform.info())


class CpuUsageTool:
    name = "cpu_usage"
    description = "Get CPU usage."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, result={"cpu_percent": psutil.cpu_percent(interval=1)})


class MemoryUsageTool:
    name = "memory_usage"
    description = "Get RAM usage."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        mem = psutil.virtual_memory()
        return ToolResult(success=True, result={
            "percent": mem.percent,
            "used_gb": round(mem.used / (1024**3), 1),
            "total_gb": round(mem.total / (1024**3), 1),
        })


class DiskUsageTool:
    name = "disk_usage"
    description = "Get disk usage."
    parameters = {"type": "object", "properties": {"path": {"type": "string"}}}

    async def execute(self, path: str = "/", **kwargs) -> ToolResult:
        usage = psutil.disk_usage(path)
        return ToolResult(success=True, result={
            "path": path,
            "percent": usage.percent,
            "used_gb": round(usage.used / (1024**3), 1),
            "total_gb": round(usage.total / (1024**3), 1),
        })


class BatteryStatusTool:
    name = "battery_status"
    description = "Get battery status."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        if not hasattr(psutil, "sensors_battery"):
            return ToolResult(success=True, result={"status": "Not available"})
        battery = psutil.sensors_battery()
        if battery is None:
            return ToolResult(success=True, result={"status": "No battery detected", "percent": None, "power_plugged": None})
        return ToolResult(success=True, result={
            "status": "ok",
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
        })


class LockScreenTool:
    name = "lock_screen"
    description = "Lock the screen."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        result = await computer_controller.lock_screen()
        if result.get("ok"):
            return ToolResult(success=True)
        return ToolResult(success=False, error=result.get("error", "Lock failed."))


class ShutdownTool:
    name = "shutdown"
    description = "Initiate system shutdown."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, confirmed: bool = False, **kwargs) -> ToolResult:
        if not confirmed:
            return ToolResult(success=False, confirmation_required=True, confirmation_message="Shutdown the system now, Sir?")
        result = await computer_controller.shutdown()
        if result.get("ok"):
            return ToolResult(success=True)
        return ToolResult(success=False, error=result.get("error", "Shutdown failed."))


class RebootTool:
    name = "reboot"
    description = "Initiate system reboot."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, confirmed: bool = False, **kwargs) -> ToolResult:
        if not confirmed:
            return ToolResult(success=False, confirmation_required=True, confirmation_message="Reboot the system now, Sir?")
        result = await computer_controller.reboot()
        if result.get("ok"):
            return ToolResult(success=True)
        return ToolResult(success=False, error=result.get("error", "Reboot failed."))


class SuspendTool:
    name = "suspend"
    description = "Suspend the system."
    parameters = {"type": "object", "properties": {}}

    async def execute(self, confirmed: bool = False, **kwargs) -> ToolResult:
        if not confirmed:
            return ToolResult(success=False, confirmation_required=True, confirmation_message="Suspend the system now, Sir?")
        result = await computer_controller.suspend()
        if result.get("ok"):
            return ToolResult(success=True)
        return ToolResult(success=False, error=result.get("error", "Suspend failed."))


class VolumeControlTool:
    name = "volume_control"
    description = "Set the system volume to a percentage (0-100) or toggle mute."
    parameters = {
        "type": "object",
        "properties": {
            "level": {"type": "integer", "description": "Volume percentage 0-100"},
            "mute": {"type": "boolean", "description": "Mute or unmute the default sink"},
        },
    }

    async def execute(self, level: int = None, mute: bool = None, **kwargs) -> ToolResult:
        if mute is not None:
            result = await computer_controller.set_mute(mute)
            if result.get("ok"):
                return ToolResult(success=True, result={"mute": mute})
            return ToolResult(success=False, error=result.get("error", "Mute failed."))
        if level is None:
            return ToolResult(success=False, error="Specify a volume level or mute.")
        result = await computer_controller.set_volume(level)
        if result.get("ok"):
            return ToolResult(success=True, result={"level": result.get("level", level)})
        return ToolResult(success=False, error=result.get("error", "Volume control failed."))

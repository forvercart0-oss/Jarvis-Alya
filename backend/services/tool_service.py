import asyncio
from collections import deque
from tools.registry import ToolRegistry


class ToolService:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._cpu_history: deque = deque(maxlen=60)
        self._ram_history: deque = deque(maxlen=60)
        self._last_cpu: float = 0.0
        self._last_ram: float = 0.0

    def list_tools(self):
        return self.registry.list_tools()

    def execute(self, name: str, arguments: dict = None, **kwargs):
        merged = dict(arguments) if arguments else {}
        confirmed = kwargs.pop("confirmed", None)
        merged.update(kwargs)
        if confirmed is not None and "confirmed" not in merged:
            merged["confirmed"] = confirmed
        return self.registry.execute(name, arguments=merged)

    async def get_cpu_usage(self) -> dict:
        result = await self.registry.execute("cpu_usage")
        data = result._data if hasattr(result, "_data") else result.__dict__
        percent = data.get("result", {}).get("cpu_percent") if isinstance(data.get("result"), dict) else data.get("cpu_percent")
        if percent is not None:
            self._last_cpu = float(percent)
            self._cpu_history.append({"time": asyncio.get_event_loop().time(), "value": self._last_cpu})
        return data

    async def get_ram_usage(self) -> dict:
        result = await self.registry.execute("memory_usage")
        data = result._data if hasattr(result, "_data") else result.__dict__
        percent = data.get("result", {}).get("percent") if isinstance(data.get("result"), dict) else data.get("percent")
        if percent is not None:
            self._last_ram = float(percent)
            self._ram_history.append({"time": asyncio.get_event_loop().time(), "value": self._last_ram})
        return data

    def get_cpu_history(self) -> list[dict]:
        return list(self._cpu_history)

    def get_ram_history(self) -> list[dict]:
        return list(self._ram_history)

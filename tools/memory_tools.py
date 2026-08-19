from tools.registry import Tool, ToolResult
from memory.manager import MemoryManager


class RememberTool(Tool):
    name = "remember"
    description = "Store an important fact or preference the user just told you."
    parameters = {
        "type": "object",
        "properties": {"content": {"type": "string"}},
        "required": ["content"],
    }

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    async def execute(self, content: str, **kwargs) -> ToolResult:
        mem = self.memory.remember(content)
        return ToolResult(success=True, result={"key": mem["key"], "id": mem["id"]})


class ForgetTool(Tool):
    name = "forget"
    description = "Delete a memory that matches the given text."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    async def execute(self, query: str, **kwargs) -> ToolResult:
        removed = self.memory.forget(query)
        return ToolResult(success=removed > 0, result={"removed": removed})


class RecallMemoriesTool(Tool):
    name = "recall_memories"
    description = "Retrieve what JARVIS remembers about the user."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
    }

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    async def execute(self, query: str = "", **kwargs) -> ToolResult:
        memories = self.memory.recall(query)
        return ToolResult(success=True, result={"memories": memories})

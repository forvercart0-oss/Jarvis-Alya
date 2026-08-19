from abc import ABC, abstractmethod
from typing import AsyncGenerator


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> str:
        pass

    @abstractmethod
    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def chat_with_tools(self, messages: list[dict], tools: list[dict], **kwargs) -> dict:
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class ProviderResponse:
    def __init__(self, content: str, provider: str, model: str):
        self.content = content
        self.provider = provider
        self.model = model


class ToolCall:
    def __init__(self, id: str, name: str, arguments: dict):
        self.id = id
        self.name = name
        self.arguments = arguments

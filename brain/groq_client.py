import asyncio
from types import SimpleNamespace
from typing import AsyncGenerator, Optional
from groq import Groq, APITimeoutError, AuthenticationError, RateLimitError, InternalServerError
from config.settings import Settings


class GroqClientError(Exception):
    pass


class GroqClient:
    def __init__(self, settings: Optional[Settings]):
        self.settings = settings
        if settings and settings.groq_api_key:
            self._client = Groq(api_key=settings.groq_api_key)
        else:
            self._client = None

    def is_available(self) -> bool:
        return bool(self._client)

    @staticmethod
    def _normalize_error(exc: Exception) -> GroqClientError:
        status_code = getattr(exc, "status_code", None)
        if status_code == 401 or isinstance(exc, AuthenticationError):
            return GroqClientError("GROQ_API_KEY is invalid or expired. Please check your configuration.")
        if status_code == 429 or isinstance(exc, RateLimitError):
            return GroqClientError("Groq rate limit exceeded. Please wait and try again.")
        if status_code and status_code >= 500 or isinstance(exc, InternalServerError):
            return GroqClientError("Groq servers are currently unavailable. Please try again later.")
        if isinstance(exc, APITimeoutError):
            return GroqClientError("Groq request timed out. The service may be overloaded.")
        return GroqClientError(f"Unexpected Groq error: {exc}")

    async def chat(self, messages: list[dict]) -> SimpleNamespace:
        if not self._client:
            raise GroqClientError("Groq client is not configured.")
        try:
            response = self._client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
            )
            if asyncio.iscoroutine(response):
                response = await response
            return SimpleNamespace(content=response.choices[0].message.content)
        except Exception as exc:
            raise self._normalize_error(exc) from exc

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        if not self._client:
            raise GroqClientError("Groq client is not configured.")
        try:
            stream = self._client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
                stream=True,
            )
            if asyncio.iscoroutine(stream):
                stream = await stream
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else ""
                if delta:
                    yield delta
        except Exception as exc:
            raise self._normalize_error(exc) from exc

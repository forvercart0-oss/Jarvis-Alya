import asyncio
import json
from typing import Any, AsyncGenerator, Optional
from groq import Groq, APITimeoutError, AuthenticationError, RateLimitError, InternalServerError
from brain.provider import AIProvider, ProviderResponse
from config.settings import get_settings


class GroqProvider(AIProvider):
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._client = None
        self.reconfigure()

    @property
    def name(self) -> str:
        return "groq"

    def reconfigure(self):
        """Rebuild the underlying client after settings change."""
        self._client = None
        if self.settings.groq_api_key:
            try:
                self._client = Groq(api_key=self.settings.groq_api_key)
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        return bool(self._client is not None and self.settings.groq_api_key)

    @staticmethod
    def _normalize_error(exc: Exception) -> str:
        status_code = getattr(exc, "status_code", None)
        if status_code == 401 or isinstance(exc, AuthenticationError):
            return "GROQ_API_KEY is invalid or expired. Please check your configuration."
        if status_code == 429 or isinstance(exc, RateLimitError):
            return "Groq rate limit exceeded. Please wait and try again."
        if status_code and status_code >= 500 or isinstance(exc, InternalServerError):
            return "Groq servers are currently unavailable. Please try again later."
        if isinstance(exc, APITimeoutError):
            return "Groq request timed out. The service may be overloaded."
        return f"Unexpected Groq error: {exc}"

    def _build_kwargs(self, **kwargs) -> dict:
        return {
            "model": kwargs.get("model", self.settings.groq_model),
            "temperature": kwargs.get("temperature", self.settings.groq_temperature),
            "max_tokens": kwargs.get("max_tokens", self.settings.groq_max_tokens),
        }

    async def generate(self, messages: list[dict], **kwargs) -> ProviderResponse:
        if not self._client:
            raise RuntimeError("Groq client is not configured.")
        try:
            response = self._client.chat.completions.create(
                **self._build_kwargs(**kwargs), messages=messages
            )
            content = response.choices[0].message.content
            return ProviderResponse(content=content or "", provider="groq", model=self.settings.groq_model)
        except Exception as exc:
            raise RuntimeError(self._normalize_error(exc)) from exc

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        if not self._client:
            raise RuntimeError("Groq client is not configured.")
        try:
            stream = self._client.chat.completions.create(
                **self._build_kwargs(**kwargs), messages=messages, stream=True
            )
            if asyncio.iscoroutine(stream):
                stream = await stream
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else ""
                if delta:
                    yield delta
        except Exception as exc:
            raise RuntimeError(self._normalize_error(exc)) from exc

    async def chat_with_tools(self, messages: list[dict], tools: list[dict], **kwargs) -> dict:
        if not self._client:
            raise RuntimeError("Groq client is not configured.")
        try:
            response = self._client.chat.completions.create(
                **self._build_kwargs(**kwargs),
                messages=messages,
                tools=tools if tools else None,
            )
            msg = response.choices[0].message
            result = {"content": msg.content or "", "tool_calls": []}
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    result["tool_calls"].append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": {},
                    })
                    try:
                        result["tool_calls"][-1]["arguments"] = json.loads(tc.function.arguments)
                    except Exception:
                        result["tool_calls"][-1]["arguments"] = {}
            return result
        except Exception as exc:
            raise RuntimeError(self._normalize_error(exc)) from exc

    async def health_check(self) -> dict:
        if not self._client:
            return {"status": "offline", "provider": "groq", "error": "No API key configured"}
        try:
            import time as _time
            start = _time.monotonic()
            await asyncio.to_thread(
                lambda: self._client.chat.completions.create(
                    model=self.settings.groq_model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=1,
                )
            )
            latency_ms = round((_time.monotonic() - start) * 1000)
            return {
                "status": "online",
                "provider": "groq",
                "model": self.settings.groq_model,
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            return {"status": "offline", "provider": "groq", "error": self._normalize_error(exc)}

    async def list_models(self) -> list[str]:
        if not self._client:
            return []
        try:
            models = await asyncio.to_thread(lambda: self._client.models.list())
            return sorted(m.id for m in models.data if "/" not in m.id)
        except Exception:
            return []

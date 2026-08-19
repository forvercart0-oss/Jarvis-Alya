import json
import time
from typing import AsyncGenerator

import httpx

from brain.provider import AIProvider, ProviderResponse
from config.settings import get_settings

_URL = "https://openrouter.ai/api/v1/chat/completions"
_HEADERS = {"Content-Type": "application/json"}


class OpenRouterProvider(AIProvider):
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._client = httpx.AsyncClient(timeout=120)

    @property
    def name(self) -> str:
        return "openrouter"

    def reconfigure(self):
        if self._client is not None:
            try:
                import asyncio as _asyncio

                _asyncio.get_event_loop().run_until_complete(self._client.aclose())
            except Exception:
                pass
        self._client = httpx.AsyncClient(timeout=120)

    def is_available(self) -> bool:
        return bool(self.settings.openrouter_api_key)

    def _headers(self) -> dict:
        headers = dict(_HEADERS)
        headers["Authorization"] = f"Bearer {self.settings.openrouter_api_key}"
        return headers

    def _payload(self, messages: list[dict], tools: list[dict], stream: bool, **kwargs) -> dict:
        payload = {
            "model": kwargs.get("model", self.settings.openrouter_model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.settings.groq_temperature),
            "max_tokens": kwargs.get("max_tokens", self.settings.groq_max_tokens),
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
        return payload

    async def generate(self, messages: list[dict], **kwargs) -> ProviderResponse:
        if not self.is_available():
            raise RuntimeError("OpenRouter is not configured.")
        try:
            response = await self._client.post(_URL, json=self._payload(messages, [], False, **kwargs), headers=self._headers())
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"].get("content", "") or ""
            return ProviderResponse(content=content, provider="openrouter", model=self.settings.openrouter_model)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenRouter HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("OpenRouter request timed out.")
        except Exception as exc:
            raise RuntimeError(f"OpenRouter error: {exc}") from exc

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise RuntimeError("OpenRouter is not configured.")
        try:
            async with self._client.stream(
                "POST", _URL, json=self._payload(messages, [], True, **kwargs), headers=self._headers()
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenRouter HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("OpenRouter request timed out.")
        except Exception as exc:
            raise RuntimeError(f"OpenRouter error: {exc}") from exc

    async def chat_with_tools(self, messages: list[dict], tools: list[dict], **kwargs) -> dict:
        if not self.is_available():
            raise RuntimeError("OpenRouter is not configured.")
        try:
            response = await self._client.post(
                _URL, json=self._payload(messages, tools, False, **kwargs), headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()
            msg = data["choices"][0]["message"]
            result = {"content": msg.get("content", "") or "", "tool_calls": []}
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    arguments = tc.get("function", {}).get("arguments", {})
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except Exception:
                            arguments = {}
                    result["tool_calls"].append({
                        "id": tc.get("id", ""),
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": arguments,
                    })
            return result
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenRouter HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("OpenRouter request timed out.")
        except Exception as exc:
            raise RuntimeError(f"OpenRouter error: {exc}") from exc

    async def health_check(self) -> dict:
        if not self.is_available():
            return {"status": "offline", "provider": "openrouter", "error": "No API key configured"}
        try:
            start = time.monotonic()
            response = await self._client.get(
                "https://openrouter.ai/api/v1/models",
                headers=self._headers(),
                timeout=15.0,
            )
            latency_ms = round((time.monotonic() - start) * 1000)
            if response.status_code == 200:
                return {
                    "status": "online",
                    "provider": "openrouter",
                    "model": self.settings.openrouter_model,
                    "latency_ms": latency_ms,
                }
            return {"status": "offline", "provider": "openrouter", "error": f"HTTP {response.status_code}"}
        except httpx.TimeoutException:
            return {"status": "offline", "provider": "openrouter", "error": "Connection timed out"}
        except Exception as exc:
            return {"status": "offline", "provider": "openrouter", "error": str(exc)}

    async def list_models(self) -> list[str]:
        if not self.is_available():
            return []
        try:
            response = await self._client.get(
                "https://openrouter.ai/api/v1/models", headers=self._headers(), timeout=15.0
            )
            if response.status_code != 200:
                return []
            return sorted(m.get("id", "") for m in response.json().get("data", []))
        except Exception:
            return []

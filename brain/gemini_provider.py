import asyncio
import json
import time
from typing import AsyncGenerator

import httpx

from brain.provider import AIProvider, ProviderResponse
from config.settings import get_settings

_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _to_gemini_tools(tools: list[dict]) -> list[dict]:
    """Convert OpenAI-style function tools to Gemini functionDeclarations."""
    out = []
    for tool in tools:
        fn = tool.get("function", {})
        parameters = fn.get("parameters", {})
        if not parameters.get("properties"):
            continue
        out.append({
            "functionDeclarations": [{
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "parameters": parameters,
            }]
        })
    return out


def _to_gemini_contents(messages: list[dict]) -> list[dict]:
    """Convert OpenAI-style messages to Gemini contents (flatten tool results)."""
    contents: list[dict] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content") or ""
        if role == "system":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "tool":
            contents.append({"role": "user", "parts": [{"text": f"Tool result:\n{content}"}]})
        else:
            contents.append({"role": role, "parts": [{"text": content}]})
    return contents


class GeminiProvider(AIProvider):
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._client = httpx.AsyncClient(timeout=60)

    @property
    def name(self) -> str:
        return "gemini"

    def reconfigure(self):
        if self._client is not None:
            try:
                import asyncio as _asyncio

                _asyncio.get_event_loop().run_until_complete(self._client.aclose())
            except Exception:
                pass
        self._client = httpx.AsyncClient(timeout=60)

    def is_available(self) -> bool:
        return bool(self.settings.gemini_api_key)

    def _url(self, stream: bool = False) -> str:
        model = self.settings.gemini_model
        endpoint = "streamGenerateContent" if stream else "generateContent"
        alt = "&alt=sse" if stream else ""
        return f"{_BASE}/models/{model}:{endpoint}?key={self.settings.gemini_api_key}{alt}"

    def _payload(self, messages: list[dict], tools: list[dict], **kwargs) -> dict:
        payload = {
            "contents": _to_gemini_contents(messages),
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.settings.groq_temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.settings.groq_max_tokens),
            },
        }
        if tools:
            payload["tools"] = _to_gemini_tools(tools)
        return payload

    @staticmethod
    def _parse_tool_calls(response: dict) -> list[dict]:
        calls = []
        try:
            candidates = response.get("candidates", [])
            parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
            for part in parts:
                if "functionCall" in part:
                    fn = part["functionCall"]
                    calls.append({
                        "id": fn.get("name", ""),
                        "name": fn.get("name", ""),
                        "arguments": fn.get("args", {}) or {},
                    })
        except Exception:
            pass
        return calls

    async def generate(self, messages: list[dict], **kwargs) -> ProviderResponse:
        if not self.is_available():
            raise RuntimeError("Gemini is not configured.")
        try:
            response = await self._client.post(self._url(), json=self._payload(messages, [], **kwargs))
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            return ProviderResponse(content=text, provider="gemini", model=self.settings.gemini_model)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Gemini HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("Gemini request timed out.")
        except Exception as exc:
            raise RuntimeError(f"Gemini error: {exc}") from exc

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise RuntimeError("Gemini is not configured.")
        try:
            async with self._client.stream("POST", self._url(stream=True), json=self._payload(messages, [], **kwargs)) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                        parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
                    except Exception:
                        continue
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Gemini HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("Gemini request timed out.")
        except Exception as exc:
            raise RuntimeError(f"Gemini error: {exc}") from exc

    async def chat_with_tools(self, messages: list[dict], tools: list[dict], **kwargs) -> dict:
        if not self.is_available():
            raise RuntimeError("Gemini is not configured.")
        try:
            response = await self._client.post(self._url(), json=self._payload(messages, tools, **kwargs))
            response.raise_for_status()
            data = response.json()
            tool_calls = self._parse_tool_calls(data)
            text = ""
            try:
                text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            except Exception:
                pass
            return {"content": text, "tool_calls": tool_calls}
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Gemini HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("Gemini request timed out.")
        except Exception as exc:
            raise RuntimeError(f"Gemini error: {exc}") from exc

    async def health_check(self) -> dict:
        if not self.is_available():
            return {"status": "offline", "provider": "gemini", "error": "No API key configured"}
        try:
            start = time.monotonic()
            response = await self._client.get(
                f"{_BASE}/models?key={self.settings.gemini_api_key}", timeout=10.0
            )
            latency_ms = round((time.monotonic() - start) * 1000)
            if response.status_code == 200:
                return {
                    "status": "online",
                    "provider": "gemini",
                    "model": self.settings.gemini_model,
                    "latency_ms": latency_ms,
                }
            return {"status": "offline", "provider": "gemini", "error": f"HTTP {response.status_code}"}
        except httpx.TimeoutException:
            return {"status": "offline", "provider": "gemini", "error": "Connection timed out"}
        except Exception as exc:
            return {"status": "offline", "provider": "gemini", "error": str(exc)}

    async def list_models(self) -> list[str]:
        if not self.is_available():
            return []
        try:
            response = await self._client.get(
                f"{_BASE}/models?key={self.settings.gemini_api_key}", timeout=10.0
            )
            if response.status_code != 200:
                return []
            models = [
                m.get("name", "").replace("models/", "")
                for m in response.json().get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            return sorted(models)
        except Exception:
            return []

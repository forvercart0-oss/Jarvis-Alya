import httpx
import json
from typing import AsyncGenerator
from brain.provider import AIProvider, ProviderResponse
from config.settings import get_settings


class LocalLLMProvider(AIProvider):
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._client = None
        self.reconfigure()

    @property
    def name(self) -> str:
        return "local_llm"

    def reconfigure(self):
        if self._client is not None:
            try:
                import asyncio

                asyncio.get_event_loop().run_until_complete(self._client.aclose())
            except Exception:
                pass
        self._client = httpx.AsyncClient(timeout=self.settings.local_llm_timeout or 60)

    def is_available(self) -> bool:
        return bool(
            self.settings.local_llm_enabled
            and self.settings.local_llm_url
            and self.settings.local_llm_model
        )

    async def _ollama_chat(self, messages: list[dict], **kwargs) -> httpx.Response:
        url = f"{self.settings.local_llm_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.settings.local_llm_model,
            "messages": messages,
            "stream": kwargs.get("stream", False),
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 1024),
            },
        }
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        return await self._client.post(url, json=payload)

    async def _openai_chat(self, messages: list[dict], **kwargs) -> httpx.Response:
        url = f"{self.settings.local_llm_url.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.settings.local_llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.local_llm_api_key}"
        payload = {
            "model": kwargs.get("model", self.settings.local_llm_model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "stream": kwargs.get("stream", False),
        }
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        return await self._client.post(url, json=payload, headers=headers)

    async def _custom_chat(self, messages: list[dict], **kwargs) -> httpx.Response:
        url = f"{self.settings.local_llm_url.rstrip('/')}/chat"
        headers = {"Content-Type": "application/json"}
        if self.settings.local_llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.local_llm_api_key}"
        payload = {
            "model": kwargs.get("model", self.settings.local_llm_model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "stream": kwargs.get("stream", False),
        }
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        return await self._client.post(url, json=payload, headers=headers)

    async def _post(self, messages: list[dict], stream: bool = False, **kwargs):
        api_type = (self.settings.local_llm_api_type or "openai").lower()
        if api_type == "ollama":
            return await self._ollama_chat(messages, stream=stream, **kwargs)
        if api_type == "custom":
            return await self._custom_chat(messages, stream=stream, **kwargs)
        return await self._openai_chat(messages, stream=stream, **kwargs)

    async def generate(self, messages: list[dict], **kwargs) -> ProviderResponse:
        if not self.is_available():
            raise RuntimeError("Local LLM is not configured.")
        try:
            response = await self._post(messages, stream=False, **kwargs)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return ProviderResponse(content=content, provider="local_llm", model=self.settings.local_llm_model)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Local LLM HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("Local LLM request timed out.")
        except Exception as exc:
            raise RuntimeError(f"Local LLM error: {exc}") from exc

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise RuntimeError("Local LLM is not configured.")
        try:
            response = await self._post(messages, stream=True, **kwargs)
            response.raise_for_status()
            api_type = (self.settings.local_llm_api_type or "openai").lower()
            if api_type == "ollama":
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        elif "response" in data:
                            yield data["response"]
                    except Exception:
                        continue
            else:
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Local LLM HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("Local LLM request timed out.")
        except Exception as exc:
            raise RuntimeError(f"Local LLM error: {exc}") from exc

    async def chat_with_tools(self, messages: list[dict], tools: list[dict], **kwargs) -> dict:
        if not self.is_available():
            raise RuntimeError("Local LLM is not configured.")
        try:
            response = await self._post(messages, stream=False, tools=tools, **kwargs)
            response.raise_for_status()
            data = response.json()
            msg = data["choices"][0]["message"]
            result = {"content": msg.get("content", "") or "", "tool_calls": []}
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    result["tool_calls"].append({
                        "id": tc.get("id", ""),
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": tc.get("function", {}).get("arguments", {}),
                    })
                    if isinstance(result["tool_calls"][-1]["arguments"], str):
                        try:
                            result["tool_calls"][-1]["arguments"] = json.loads(result["tool_calls"][-1]["arguments"])
                        except Exception:
                            result["tool_calls"][-1]["arguments"] = {}
            return result
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Local LLM HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.TimeoutException:
            raise RuntimeError("Local LLM request timed out.")
        except Exception as exc:
            raise RuntimeError(f"Local LLM error: {exc}") from exc

    async def health_check(self) -> dict:
        if not self.is_available():
            return {"status": "offline", "provider": "local_llm", "error": "Not configured"}
        try:
            import time as _time
            api_type = (self.settings.local_llm_api_type or "openai").lower()
            if api_type == "ollama":
                url = f"{self.settings.local_llm_url.rstrip('/')}/api/tags"
            else:
                url = f"{self.settings.local_llm_url.rstrip('/')}/v1/models"
            start = _time.monotonic()
            response = await self._client.get(url, timeout=10.0)
            latency_ms = round((_time.monotonic() - start) * 1000)
            if response.status_code == 200:
                data = {}
                try:
                    data = response.json()
                except Exception:
                    pass
                if api_type == "ollama":
                    models = [m.get("name", "") for m in data.get("models", [])]
                    detected = (
                        self.settings.local_llm_model
                        if self.settings.local_llm_model in models
                        else (models[0] if models else self.settings.local_llm_model)
                    )
                else:
                    detected = self.settings.local_llm_model
                return {
                    "status": "online",
                    "provider": "local_llm",
                    "model": detected,
                    "url": self.settings.local_llm_url,
                    "api_type": api_type,
                    "latency_ms": latency_ms,
                }
            return {"status": "offline", "provider": "local_llm", "error": f"HTTP {response.status_code}"}
        except httpx.TimeoutException:
            return {"status": "offline", "provider": "local_llm", "error": "Connection timed out"}
        except Exception as exc:
            return {"status": "offline", "provider": "local_llm", "error": str(exc)}

    async def list_models(self) -> list[str]:
        if not self.is_available():
            return []
        try:
            api_type = (self.settings.local_llm_api_type or "openai").lower()
            if api_type == "ollama":
                url = f"{self.settings.local_llm_url.rstrip('/')}/api/tags"
                response = await self._client.get(url, timeout=10.0)
                if response.status_code != 200:
                    return []
                return sorted(m.get("name", "") for m in response.json().get("models", []))
            url = f"{self.settings.local_llm_url.rstrip('/')}/v1/models"
            headers = {}
            if self.settings.local_llm_api_key:
                headers["Authorization"] = f"Bearer {self.settings.local_llm_api_key}"
            response = await self._client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                return []
            return sorted(m.get("id", "") for m in response.json().get("data", []))
        except Exception:
            return []

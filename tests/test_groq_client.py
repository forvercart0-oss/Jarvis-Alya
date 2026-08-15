from __future__ import annotations

from types import SimpleNamespace

import pytest

from brain.groq_client import GroqClient, GroqClientError
from config.settings import Settings


def _settings_with_key(key="sk-test"):
    s = Settings()
    s.groq_api_key = key
    return s


def test_client_unavailable_without_key():
    s = Settings()
    s.groq_api_key = ""
    client = GroqClient(s)
    assert client.is_available() is False


def test_client_available_with_key():
    client = GroqClient(_settings_with_key())
    assert client.is_available() is True


@pytest.mark.asyncio
async def test_chat_stream_raises_without_key():
    client = GroqClient(_settings_with_key(""))
    with pytest.raises(GroqClientError, match="not configured"):
        async for _ in client.chat_stream([{"role": "user", "content": "hi"}]):
            pass  # pragma: no cover


def test_error_normalization_auth():
    exc = SimpleNamespace(status_code=401, message="nope")
    err = GroqClient._normalize_error(exc)
    assert "GROQ_API_KEY" in str(err)


def test_error_normalization_rate_limit():
    exc = SimpleNamespace(status_code=429, message="slow down")
    err = GroqClient._normalize_error(exc)
    assert "rate limit" in str(err).lower()


def test_error_normalization_server():
    exc = SimpleNamespace(status_code=503, message="busy")
    err = GroqClient._normalize_error(exc)
    assert "servers" in str(err)


def test_error_normalization_timeout():
    from groq import APITimeoutError

    err = GroqClient._normalize_error(APITimeoutError("took too long"))
    assert "timed out" in str(err)


def test_error_normalization_generic():
    err = GroqClient._normalize_error(RuntimeError("something exploded"))
    assert "Unexpected Groq error" in str(err)


@pytest.mark.asyncio
async def test_chat_success_returns_message(monkeypatch):
    client = GroqClient(_settings_with_key())

    class FakeMessage(SimpleNamespace):
        content = "hello back"

    class FakeChoices:
        def __init__(self):
            self.message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoices()]

    class FakeCreate:
        async def create(self, **kwargs):
            return FakeResponse()

    completions = SimpleNamespace(create=FakeCreate().create)
    chat = SimpleNamespace(completions=completions)
    client._client = SimpleNamespace(chat=chat)

    message = await client.chat([{"role": "user", "content": "hi"}])
    assert message.content == "hello back"


@pytest.mark.asyncio
async def test_chat_propagates_error(monkeypatch):
    client = GroqClient(_settings_with_key())

    class FakeRateLimit(Exception):
        status_code = 429
        message = "over quota"

    async def boom(**kwargs):
        raise FakeRateLimit("over quota")

    completions = SimpleNamespace(create=boom)
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    with pytest.raises(GroqClientError, match="rate limit"):
        await client.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_chat_stream_yields_content_deltas(monkeypatch):
    client = GroqClient(_settings_with_key())

    class FakeDelta:
        content = "world"

    class FakeChoice:
        choices = [SimpleNamespace(delta=FakeDelta())]

    class FakeStream:
        async def __aiter__(self):
            for chunk in [FakeChoice(), FakeChoice(), SimpleNamespace(choices=[])]:
                yield chunk

    async def stream_creator(**kwargs):
        return FakeStream()

    completions = SimpleNamespace(create=stream_creator)
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    chunks = [c async for c in client.chat_stream([{"role": "user", "content": "hi"}])]
    assert chunks == ["world", "world"]

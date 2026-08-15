import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator, Optional

from brain.provider_registry import create_providers, select_provider
from brain.conversation import ConversationManager
from brain.router import Router
from brain.offline import offline_reply
from brain.prompts import build_persona_prompt
from tools.registry import ToolRegistry
from memory.manager import MemoryManager
from voice.tts_manager import TTSManager
from config.settings import get_settings

logger = logging.getLogger("jarvis.ai")

_WORD_RE = re.compile(r"\S+\s*")


def chunk_text(text: str, max_chunk: int = 6) -> list[str]:
    """Split text into small chunks for streaming to the UI."""
    if len(text) <= max_chunk:
        return [text] if text else []
    words = _WORD_RE.findall(text)
    chunks: list[str] = []
    current = ""
    for word in words:
        current += word
        if len(current) >= max_chunk:
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    return chunks or [text]


class AIService:
    def __init__(self, memory: MemoryManager, tts: TTSManager, tool_registry: ToolRegistry):
        settings = get_settings()
        self.providers = create_providers(settings)
        self.groq = self.providers["groq"]
        self.local_llm = self.providers["local_llm"]
        self.gemini = self.providers["gemini"]
        self.openrouter = self.providers["openrouter"]
        self.conversation = ConversationManager(memory)
        self.router = Router()
        self.memory = memory
        self.tts = tts
        self.tools = tool_registry
        self.settings = settings
        self._current_conv: Optional[str] = None
        self._current_provider: Optional[Any] = None
        self._pending_confirmation: Optional[dict] = None
        self._confirmation_event: Optional[asyncio.Event] = None
        self._confirmation_result: Optional[bool] = None

    # ------------------------------------------------------------- providers
    def reconfigure_providers(self):
        for provider in self.providers.values():
            provider.reconfigure()

    def _get_or_create_conv(self, conversation_id: Optional[str] = None) -> str:
        if conversation_id:
            conv = self.memory.store.get_conversation(conversation_id)
            if conv:
                self._current_conv = conversation_id
                return conversation_id
        if self._current_conv is None:
            self._current_conv = self.memory.ensure_conversation(None)
        return self._current_conv

    def _select_provider(self):
        return select_provider(self.providers, self.settings.provider_priority)

    def _next_available_provider(self, current):
        """Return the first other available provider for auto-failover."""
        for name in ("groq", "gemini", "openrouter", "local_llm"):
            provider = self.providers.get(name)
            if provider and provider is not current and provider.is_available():
                return provider
        return None

    async def health(self) -> dict:
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as exc:
                results[name] = {"status": "offline", "provider": name, "error": str(exc)}
        return results

    def _get_tools_spec(self) -> list[dict]:
        return self.tools.tools_spec()

    def _tool_result_data(self, result) -> dict:
        if hasattr(result, "_data"):
            return result._data
        if hasattr(result, "__dict__"):
            return result.__dict__
        return {"success": True, "result": str(result)}

    # ------------------------------------------------------------ tool calls
    async def _process_single_tool(self, tool_name: str, tool_args: dict, confirmed: bool = False) -> dict:
        result = await self.tools.execute(tool_name, confirmed=confirmed, **tool_args)
        data = self._tool_result_data(result)
        if data.get("confirmation_required") and not confirmed and not tool_args.get("_confirmed"):
            data = {
                "success": False,
                "error": "confirmation_required",
                "confirmation_required": True,
                "confirmation_message": data.get("confirmation_message", f"Confirm {tool_name}?"),
            }
        return data

    async def _execute_with_confirmation(self, tool_name: str, tool_args: dict) -> tuple[dict, bool]:
        data = await self._process_single_tool(tool_name, tool_args)
        if data.get("confirmation_required"):
            self._pending_confirmation = {"tool": tool_name, "arguments": tool_args}
            yield_data = {
                "tool": tool_name,
                "arguments": tool_args,
                "message": data.get("confirmation_message", f"Confirm {tool_name}?"),
            }
            return data, False, yield_data
        return data, True, None

    async def _wait_for_confirmation(self, tool_name: str, tool_args: dict) -> bool:
        self._confirmation_event = asyncio.Event()
        self._confirmation_result = None
        await self._confirmation_event.wait()
        result = bool(self._confirmation_result)
        self._confirmation_event = None
        self._confirmation_result = None
        return result

    def confirm_tool(self, confirmed: bool):
        if self._confirmation_event:
            self._confirmation_result = confirmed
            self._confirmation_event.set()

    async def _run_tool_calls(self, tool_calls: list[dict]) -> AsyncGenerator[dict, None]:
        results: list[dict] = []
        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("arguments", {}) or {}
            yield {"event": "tool_start", "data": {"tool": tool_name, "arguments": tool_args}}

            result = await self.tools.execute(tool_name, confirmed=False, **tool_args)
            data = self._tool_result_data(result)

            if data.get("confirmation_required"):
                yield {"event": "tool_confirmation", "data": {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "message": data.get("confirmation_message", f"Confirm {tool_name}?"),
                    "tool_call_id": tc.get("id", ""),
                }}
                confirmed = await self._wait_for_confirmation(tool_name, tool_args)
                if confirmed:
                    result = await self.tools.execute(tool_name, confirmed=True, **tool_args)
                    data = self._tool_result_data(result)
                else:
                    data = {"success": False, "error": "User cancelled the operation."}

            results.append({
                "tool_call_id": tc.get("id", ""),
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(data),
            })

            yield {"event": "tool_result", "data": {
                "tool": tool_name,
                "result": data,
                "success": data.get("success", False),
            }}

        self._last_tool_results = results

    # --------------------------------------------------------------- offline
    async def _handle_offline(self, user_message: str, conv_id: str) -> AsyncGenerator[dict, None]:
        route = self.router.heuristic_route(user_message)
        reply = ""
        if route.action == "tool":
            async for ev in self._run_tool_calls([{"name": route.name, "arguments": route.arguments, "id": ""}]):
                yield ev
            result_data = self._last_tool_results[0]["content"] if self._last_tool_results else "{}"
            try:
                result_data = json.loads(result_data)
            except Exception:
                result_data = {"success": False}
            reply = offline_reply(user_message, {"name": route.name}, result_data)
        else:
            reply = "Sir, I'm currently offline. No AI provider is available, but I can still help with local tasks."
        self.conversation.add_message(conv_id, "assistant", reply)
        await self._emit_response(reply, conv_id, "offline")

    async def _emit_response(self, reply: str, conv_id: str, provider_name: str):
        for chunk in chunk_text(reply):
            yield {"event": "token", "data": {"chunk": chunk, "provider": provider_name}}
            await asyncio.sleep(0.015)
        await self._finish(reply, conv_id, provider_name)

    async def _finish(self, reply: str, conv_id: str, provider_name: str):
        yield {"event": "speaking", "data": {"text": reply}}
        if self.tts and reply:
            await self.tts.speak_chunks(reply)
        yield {"event": "done", "data": {"response": reply, "conversation_id": conv_id, "provider": provider_name}}

    # ------------------------------------------------------------- streaming
    async def _stream_provider_response(self, provider, messages, conv_id) -> AsyncGenerator[dict, None]:
        tools_spec = self._get_tools_spec()
        result = await provider.chat_with_tools(messages, tools_spec)
        content = result.get("content", "") or ""
        tool_calls = result.get("tool_calls", [])

        if not content and not tool_calls:
            content = "I processed your request, Sir."

        self._last_tool_results = []
        if tool_calls:
            async for ev in self._run_tool_calls(tool_calls):
                yield ev
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc.get("name", ""), "arguments": json.dumps(tc.get("arguments", {}))}}
                    for tc in tool_calls
                ],
            })
            for tr in self._last_tool_results:
                messages.append({"role": "tool", "tool_call_id": tr["tool_call_id"], "content": tr["content"]})
            follow_up = await provider.chat_with_tools(messages, tools_spec)
            content = follow_up.get("content", "") or content

        for chunk in chunk_text(content):
            yield {"event": "token", "data": {"chunk": chunk, "provider": provider.name}}
            await asyncio.sleep(0.015)
        yield {"event": "_final_content", "data": {"content": content}}

    async def process_message(self, user_message: str, conversation_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
        conv_id = self._get_or_create_conv(conversation_id)
        self.conversation.add_message(conv_id, "user", user_message)
        self._last_tool_results = []

        yield {"event": "thinking", "data": {}}

        provider = self._select_provider()
        self._current_provider = provider

        if not provider:
            async for ev in self._handle_offline(user_message, conv_id):
                yield ev
            return

        system_prompt = build_persona_prompt(
            self.settings.persona,
            user_name=self.settings.user_name,
            assistant_name=self.settings.assistant_name,
        )
        messages = self.conversation.build_messages_with_system(conv_id, user_message, system_prompt)
        full_response = ""
        active_provider = provider

        try:
            async for ev in self._stream_provider_response(provider, messages, conv_id):
                if ev["event"] == "token":
                    full_response += ev["data"]["chunk"]
                elif ev["event"] == "_final_content":
                    full_response = ev["data"]["content"]
                yield ev
        except Exception as exc:
            logger.warning("Provider %s failed: %s", provider.name, exc)
            if self.settings.auto_failover:
                alt = self._next_available_provider(provider)
                if alt:
                    yield {"event": "notification", "data": {"message": f"Failing over to {alt.name}...", "type": "warning"}}
                    try:
                        async for ev in self._stream_provider_response(alt, messages, conv_id):
                            if ev["event"] == "token":
                                full_response += ev["data"]["chunk"]
                            elif ev["event"] == "_final_content":
                                full_response = ev["data"]["content"]
                            yield ev
                        active_provider = alt
                    except Exception as exc2:
                        logger.warning("Failover also failed: %s", exc2)
                        full_response = f"I'm having trouble connecting to my AI services, Sir. ({exc})"
                else:
                    full_response = f"I'm having trouble with the {provider.name} provider, Sir: {exc}"
            else:
                full_response = f"I'm having trouble with the {provider.name} provider, Sir: {exc}"

        if not full_response.strip():
            full_response = "I'm not sure I understood that, Sir. Could you rephrase?"

        self.conversation.add_message(conv_id, "assistant", full_response)
        yield {"event": "speaking", "data": {"text": full_response}}
        if self.tts and full_response:
            await self.tts.speak_chunks(full_response)
        yield {"event": "done", "data": {"response": full_response, "conversation_id": conv_id, "provider": active_provider.name}}

    def get_conversation_id(self) -> Optional[str]:
        return self._current_conv

    async def reset_conversation(self) -> str:
        self._current_conv = self.memory.ensure_conversation(None)
        return self._current_conv

    def set_tts(self, tts: TTSManager):
        self.tts = tts

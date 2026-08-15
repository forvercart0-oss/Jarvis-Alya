import asyncio
import logging
from typing import Callable, Optional

from voice import VoiceService
from voice.tts_manager import TTSManager
from memory.manager import MemoryManager
from backend.services.ai_service import AIService
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.voice_manager")


class VoiceManager:
    def __init__(self, memory: MemoryManager, ai_service: AIService):
        self.memory = memory
        self.ai_service = ai_service
        self._voice = VoiceService()
        self._processing = False
        self._started = False

    @property
    def tts(self) -> TTSManager:
        return self._voice.tts

    @property
    def mic_available(self) -> bool:
        return self._voice.mic_available

    @property
    def tts_available(self) -> bool:
        return self._voice.tts_available

    @property
    def initialized(self) -> bool:
        return self._voice._initialized

    def list_voices(self) -> list[str]:
        return self._voice.list_voices()

    def voice_catalog(self) -> list[dict]:
        return self._voice.voice_catalog()

    def initialize(self) -> bool:
        return self._voice.initialize()

    def is_available(self) -> bool:
        return self._voice._initialized and (self._voice.mic_available or self._voice.tts_available)

    async def start(self):
        try:
            if not self._voice.initialize():
                return
            self._started = True
            await self.tts.start()
            mic_ok = self._voice.listener.is_available()
            if self._voice.settings.wake_word_enabled and mic_ok:
                self._voice.start_wakeword(self._on_wake)
                await ws_manager.broadcast("wakeword_ready", {"wake_word": self._voice.settings.wake_word})
            elif mic_ok:
                asyncio.create_task(self._listen_loop())
            else:
                logger.warning("Microphone unavailable — voice input disabled; TTS still active.")
        except Exception as exc:
            logger.warning("Voice start failed: %s", exc)

    async def stop(self):
        self._started = False
        try:
            await self.tts.stop()
        except Exception:
            pass
        try:
            self._voice.shutdown()
        except Exception:
            pass

    # ------------------------------------------------------------ wake word
    def _on_wake(self):
        try:
            asyncio.create_task(self._handle_wake())
        except Exception:
            pass

    async def _handle_wake(self):
        if self._processing:
            return
        self._processing = True
        try:
            await self.speak("Yes, Sir?")
            text = await self._voice.listen(max_duration=15.0)
            if text:
                await self._process(text)
        except Exception as exc:
            logger.warning("Wake word handling failed: %s", exc)
        finally:
            self._processing = False

    # --------------------------------------------------------------- listen
    async def _listen_loop(self):
        while self._started:
            try:
                if self._processing:
                    await asyncio.sleep(0.5)
                    continue
                text = await self._voice.listen()
                if text:
                    self._processing = True
                    asyncio.create_task(self._process(text))
            except Exception:
                await asyncio.sleep(0.5)

    async def _process(self, text: str):
        try:
            async for event in self.ai_service.process_message(text):
                if event["event"].startswith("_"):
                    continue
                await ws_manager.broadcast(event["event"], event["data"])
        except Exception as exc:
            logger.warning("Voice process failed: %s", exc)
        finally:
            self._processing = False

    # ------------------------------------------------------------- output
    async def speak(self, text: str) -> bool:
        if not text or not self._started:
            return False
        try:
            return await self._voice.speak(text)
        except Exception as exc:
            logger.warning("Speak failed: %s", exc)
            return False

    async def test_voice(self, text: str = "Hello! This is JARVIS speaking.") -> bool:
        """Play a test utterance immediately through the configured engine."""
        try:
            return await self._voice.speak_now(text)
        except Exception as exc:
            logger.warning("Voice test failed: %s", exc)
            return False

    def is_speaking(self) -> bool:
        return self._voice.tts.is_speaking()

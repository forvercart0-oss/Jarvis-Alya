"""Persona service: switches JARVIS / ALYA identities at runtime.

Switching applies, without restarting the application:

- the persona-aware system prompt (used on the next message),
- the preferred TTS voice (male vs female Kokoro voice),
- the theme accent/secondary colors,
- the assistant name,
- a ``persona_switched`` WebSocket event so the UI can animate the orb,
  swap the logo and repaint the theme.
"""

from __future__ import annotations

import logging

from backend.services.ws_manager import ws_manager
from config.personas import get_persona, persona_payload
from config.settings import get_settings

logger = logging.getLogger("jarvis.persona")


class PersonaService:
    def __init__(self):
        self.settings = get_settings()

    # --------------------------------------------------------------- state
    def current(self) -> dict:
        return persona_payload(self.settings.persona)

    # ------------------------------------------------------------- switching
    async def switch(self, persona_id: str) -> dict:
        persona = get_persona(persona_id)
        settings = self.settings
        settings.persona = persona.id
        settings.assistant_name = persona.name

        # Theme colors follow the persona but only overwrite when the user has
        # not customized them away from a persona default.
        if settings.accent_color in ("#00f0ff", "#ff6ec7", "", "cyan", None):
            settings.accent_color = persona.accent_color

        # Voice follows persona gender when the current voice is from the
        # opposite gender or is the engine default.
        from voice.kokoro_tts import KOKORO_VOICES, _voice_gender

        current_voice = (settings.tts_voice or "").lower()
        if not current_voice or current_voice not in KOKORO_VOICES or _voice_gender(current_voice) != persona.gender:
            settings.tts_voice = persona.default_voice

        try:
            from backend.main import tts_manager, memory_manager
        except Exception:  # not fully wired yet (import-time guard)
            tts_manager = None
            memory_manager = None

        if tts_manager is not None:
            try:
                tts_manager.set_voice(settings.tts_voice)
            except Exception as exc:
                logger.warning("Voice apply failed during persona switch: %s", exc)

        try:
            settings.persist()
            if memory_manager is not None:
                memory_manager.store.set_setting("persona", persona.id)
                memory_manager.store.set_setting("tts_voice", settings.tts_voice)
                memory_manager.store.set_setting("accent_color", settings.accent_color)
        except Exception as exc:
            logger.warning("Persona persistence failed: %s", exc)

        payload = persona_payload(persona.id)
        payload["assistant_name"] = persona.name
        payload["tts_voice"] = settings.tts_voice
        payload["accent_color"] = settings.accent_color
        await ws_manager.broadcast("persona_switched", payload)
        logger.info("Persona switched -> %s (voice=%s)", persona.name, settings.tts_voice)
        return payload

    # ---------------------------------------------------------- startup apply
    async def apply_persona_on_startup(self) -> None:
        """Apply persona defaults for voice/name if they were never set.

        Keeps existing user voice choices untouched unless they conflict with
        the persona gender (a male persona with a female Kokoro voice is
        corrected on startup too).
        """
        persona = get_persona(self.settings.persona)
        changed = False
        if self.settings.assistant_name != persona.name:
            self.settings.assistant_name = persona.name
            changed = True
        from voice.kokoro_tts import KOKORO_VOICES, _voice_gender

        current = (self.settings.tts_voice or "").lower()
        if not current or current not in KOKORO_VOICES or _voice_gender(current) != persona.gender:
            self.settings.tts_voice = persona.default_voice
            changed = True
        if self.settings.accent_color in ("#00f0ff", "#ff6ec7", "", "cyan", None):
            self.settings.accent_color = persona.accent_color
            changed = True
        if changed:
            try:
                self.settings.persist()
                from backend.main import memory_manager

                if memory_manager is not None:
                    memory_manager.store.set_setting("persona", self.settings.persona)
                    memory_manager.store.set_setting("tts_voice", self.settings.tts_voice)
                    memory_manager.store.set_setting("accent_color", self.settings.accent_color)
            except Exception:
                pass
        logger.info("Persona '%s' active (voice=%s)", persona.name, self.settings.tts_voice)


persona_service = PersonaService()

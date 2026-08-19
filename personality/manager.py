"""Personality engine for JARVIS 2.0.

Manages JARVIS/ALYA behavior, personality levels for ALYA,
language detection, persona-aware greetings, and response styling.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, Optional

from config.personas import get_persona, persona_payload, PERSONAS
from language.detector import detect_language

logger = logging.getLogger("jarvis.personality")


class PreferenceLearner:
    def __init__(self, memory_manager: Any | None = None):
        self._memory = memory_manager

    def learn_from_feedback(self, user_message: str, assistant_response: str, feedback: str) -> dict | None:
        if not self._memory:
            return None
        feedback_lower = feedback.lower()
        if any(p in feedback_lower for p in ["perfect", "exactly", "good", "do this every time", "always do this"]):
            key = "response_style"
            value = "concise" if len(assistant_response) < 200 else "detailed"
            return self._memory.remember_adaptive_preference(
                key=key,
                value=value,
                source="correction",
                confidence="medium",
                metadata={"trigger": feedback},
            )
        if any(p in feedback_lower for p in ["don't", "stop", "wrong", "no ", "use another"]):
            key = "avoid_pattern"
            value = feedback[:200]
            return self._memory.remember_adaptive_preference(
                key=key,
                value=value,
                source="correction",
                confidence="medium",
                metadata={"trigger": feedback, "type": "negative"},
            )
        return None

    def detect_explicit_preference(self, user_message: str) -> dict | None:
        if not self._memory:
            return None
        lower = user_message.lower()
        patterns = [
            ("always use dark mode", "theme", "dark"),
            ("always use light mode", "theme", "light"),
            ("use concise", "response_style", "concise"),
            ("give me short", "response_style", "concise"),
            ("don't give long", "response_style", "concise"),
            ("always use postgresql", "database", "postgresql"),
            ("use postgres", "database", "postgresql"),
            ("prefer python", "language", "python"),
            ("use fastapi", "framework", "fastapi"),
        ]
        for trigger, key, value in patterns:
            if trigger in lower:
                return self._memory.remember_adaptive_preference(
                    key=key,
                    value=value,
                    source="explicit_user",
                    confidence="high",
                    metadata={"trigger": trigger},
                )
        return None


@dataclass
class PersonalityLevel:
    """Personality level configuration for ALYA."""
    level: str  # professional | friendly | playful | teasing | flirty
    formality: float = 0.5  # 0 = very casual, 1 = very formal
    warmth: float = 0.7  # 0 = cold, 1 = very warm
    humor: float = 0.3  # 0 = serious, 1 = playful
    affection: float = 0.2  # 0 = distant, 1 = affectionate (carefully bounded)


PERSONALITY_LEVELS: dict[str, PersonalityLevel] = {
    "professional": PersonalityLevel(
        level="professional",
        formality=0.8,
        warmth=0.5,
        humor=0.1,
        affection=0.1,
    ),
    "friendly": PersonalityLevel(
        level="friendly",
        formality=0.5,
        warmth=0.8,
        humor=0.4,
        affection=0.3,
    ),
    "playful": PersonalityLevel(
        level="playful",
        formality=0.3,
        warmth=0.9,
        humor=0.7,
        affection=0.4,
    ),
    "teasing": PersonalityLevel(
        level="teasing",
        formality=0.2,
        warmth=0.7,
        humor=0.9,
        affection=0.5,
    ),
    "flirty": PersonalityLevel(
        level="flirty",
        formality=0.1,
        warmth=0.9,
        humor=0.6,
        affection=0.7,
    ),
}


class PersonalityEngine:
    """Manages JARVIS and ALYA persona behavior.

    Handles:
    - Persona switching and persistence
    - ALYA personality level slider
    - Language detection and adaptation
    - Persona-aware greeting generation
    - Response styling based on personality
    """

    def __init__(
        self,
        persona_id: str = "jarvis",
        personality_level: str = "professional",
        language_mode: str = "auto",
        memory_manager: Any | None = None,
    ):
        self._persona_id = persona_id
        self._personality_level = personality_level
        self._language_mode = language_mode
        self._current_persona = get_persona(persona_id)
        self._greeting_index: int = 0
        self._preference_learner = PreferenceLearner(memory_manager)

    @property
    def persona_id(self) -> str:
        return self._persona_id

    @property
    def persona(self):
        return self._current_persona

    @property
    def personality_level(self) -> str:
        return self._personality_level

    @property
    def language_mode(self) -> str:
        return self._language_mode

    def get_personality_config(self) -> PersonalityLevel:
        """Get the current personality level configuration."""
        return PERSONALITY_LEVELS.get(
            self._personality_level, PERSONALITY_LEVELS["professional"]
        )

    def switch_persona(self, persona_id: str) -> dict:
        """Switch to a different persona."""
        persona = get_persona(persona_id)
        self._current_persona = persona
        self._persona_id = persona.id
        self._greeting_index = 0
        logger.info("Switched persona to %s", persona.name)
        return persona_payload(persona.id)

    def set_personality_level(self, level: str) -> dict:
        """Set the ALYA personality level."""
        if level not in PERSONALITY_LEVELS:
            level = "professional"
        self._personality_level = level
        config = self.get_personality_config()
        logger.info("Personality level set to %s", level)
        return {
            "level": level,
            "formality": config.formality,
            "warmth": config.warmth,
            "humor": config.humor,
            "affection": config.affection,
        }

    def set_language_mode(self, mode: str) -> str:
        """Set the language mode."""
        self._language_mode = detect_language(mode) if mode != "auto" else "auto"
        return self._language_mode

    def detect_language(self, text: str) -> str:
        """Detect the language of input text."""
        if self._language_mode != "auto":
            return self._language_mode
        return detect_language(text)

    def get_greeting(self, user_name: str = "Sir", context: str = "first") -> str:
        """Get a persona-aware greeting.

        Args:
            user_name: Name to address the user with.
            context: Greeting context - "first", "returning", or "casual".
        """
        persona = self._current_persona
        greetings = getattr(persona, "greetings", ())

        if not greetings:
            if self._persona_id == "jarvis":
                greetings = (
                    "Assalamualaikum. Main JARVIS hoon. Aap kaise hain?",
                    "Assalamualaikum. Main JARVIS hoon. Bataiye kya kaam karna hai?",
                    "Assalamualaikum. JARVIS ready hai. Kya help chahiye?",
                )
            else:
                greetings = (
                    "Assalamualaikum. Main ALYA hoon. Aap kaise hain?",
                    "Assalamualaikum. Main ALYA hoon. Bataiye kya kaam karna hai?",
                    "Assalamualaikum. ALYA ready hai. Kya help chahiye?",
                )

        if context == "first" or len(greetings) == 1:
            return random.choice(greetings)

        # Cycle through greetings for returning users
        greeting = greetings[self._greeting_index % len(greetings)]
        self._greeting_index += 1
        return greeting

    def get_persona_aware_opening(self, user_name: str = "Sir") -> str:
        """Get a persona-aware conversation opening."""
        level = self.get_personality_config()

        if self._persona_id == "jarvis":
            if level.formality > 0.7:
                return f"At your service, {user_name}."
            elif level.formality > 0.4:
                return f"Ready when you are, {user_name}."
            else:
                return f"Hey {user_name}, what's up?"
        else:
            if level.warmth > 0.8:
                return f"I'm here for you, {user_name}!"
            elif level.warmth > 0.5:
                return f"Hi there, {user_name}! How can I help?"
            else:
                return f"Hello, {user_name}."

    def apply_persona_to_response(
        self,
        response: str,
        user_message: str = "",
        user_name: str = "Sir",
    ) -> str:
        """Apply persona styling to a response.

        This post-processes the response based on personality settings.
        The primary persona shaping should happen in the system prompt,
        but this can add persona-specific flair.
        """
        level = self.get_personality_config()

        # Add personality-appropriate prefix for certain responses
        if response.strip().startswith(("I cannot", "I can't", "I'm sorry")):
            if self._persona_id == "alya" and level.warmth > 0.6:
                # Add warm prefix for ALYA
                if not response.strip().startswith("I'm sorry"):
                    response = "I'm sorry, " + response[0].lower() + response[1:]
            elif self._persona_id == "jarvis" and level.formality > 0.7:
                # Add formal prefix for JARVIS
                if not response.strip().startswith("I'm afraid"):
                    response = "I'm afraid I can't comply with that, Sir. " + response

        return response

    def get_state(self) -> dict:
        """Get the current personality engine state."""
        config = self.get_personality_config()
        return {
            "persona_id": self._persona_id,
            "persona_name": self._current_persona.name,
            "personality_level": self._personality_level,
            "language_mode": self._language_mode,
            "formality": config.formality,
            "warmth": config.warmth,
            "humor": config.humor,
            "affection": config.affection,
            "available_personas": list(PERSONAS.keys()),
            "available_levels": list(PERSONALITY_LEVELS.keys()),
        }

    def process_feedback(self, user_message: str, assistant_response: str, feedback: str) -> dict | None:
        return self._preference_learner.learn_from_feedback(user_message, assistant_response, feedback)

    def detect_preference(self, user_message: str) -> dict | None:
        return self._preference_learner.detect_explicit_preference(user_message)


_personality_engine: Optional[PersonalityEngine] = None


def get_personality_engine(
    persona_id: str = "jarvis",
    personality_level: str = "professional",
    language_mode: str = "auto",
    memory_manager: Any | None = None,
) -> PersonalityEngine:
    """Get or create the global personality engine."""
    global _personality_engine
    if _personality_engine is None:
        _personality_engine = PersonalityEngine(
            persona_id=persona_id,
            personality_level=personality_level,
            language_mode=language_mode,
            memory_manager=memory_manager,
        )
    return _personality_engine

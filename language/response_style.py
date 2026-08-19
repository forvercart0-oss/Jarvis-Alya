"""Response style selection based on detected/user language."""

from __future__ import annotations

from language.detector import detect_language


def response_style_for(text: str, persona_gender: str = "male") -> str:
    """Return style hints for the AI based on input language and persona."""
    lang = detect_language(text)
    if lang in ("ur", "roman_urdu", "mixed"):
        if persona_gender == "female":
            return "feminine_hinglish"
        return "masculine_hinglish"
    return "english"


def style_instruction(persona_gender: str = "male") -> str:
    if persona_gender == "female":
        return (
            "Respond in the same language style as the user. "
            "If the user writes in Roman Urdu / Hinglish, you may reply in natural Roman Urdu/Hinglish with FEMININE grammar. "
            "If the user writes in English, reply in English."
        )
    return (
        "Respond in the same language style as the user. "
        "If the user writes in Roman Urdu / Hinglish, you may reply in natural Roman Urdu/Hinglish with MASCULINE grammar. "
        "If the user writes in English, reply in English."
    )

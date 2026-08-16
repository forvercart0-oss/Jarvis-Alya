"""Safety refusal response generation for JARVIS 2.0.

Generates persona-aware refusal responses in multiple styles:
- JARVIS style: professional, calm, slightly witty
- ALYA style: friendly, warm, respectful

Supports Roman Urdu/Hinglish responses based on detected language.
"""

from __future__ import annotations

from typing import Optional

from safety.classifier import SafetyClassification, SafetyCategory, Severity


class ResponseStyle:
    """Base class for safety response styles."""
    pass


class JARVISResponseStyle(ResponseStyle):
    """Professional, calm, slightly witty refusal style for JARVIS."""

    REFUSALS: dict[str, list[str]] = {
        "general": [
            "I'm afraid I can't assist with that, Sir. It falls outside my operational parameters.",
            "I must decline that request, Sir. My protocols prevent me from complying.",
            "That's not something I can help with, Sir. Perhaps we can explore an alternative?",
            "I'll have to pass on that one, Sir. It doesn't align with my safety guidelines.",
        ],
        "harmful": [
            "I cannot assist with harmful activities under any circumstances, Sir. My core directives prohibit it.",
            "That request involves harm, Sir, and I'm designed to prevent exactly that kind of thing.",
            "I'm not able to help with that, Sir. It would compromise my fundamental safety protocols.",
        ],
        "illegal": [
            "I'm sorry, Sir, but I can't assist with illegal activities. Is there something legitimate I can help with?",
            "That would be illegal, Sir. I'm here to help with lawful requests only.",
        ],
        "malware": [
            "Creating or distributing malware is illegal and harmful, Sir. I can help you learn about cybersecurity defense instead.",
            "I cannot assist with malware creation, Sir. However, I can explain how malware works for educational purposes or help with defensive security measures.",
        ],
        "unauthorized_access": [
            "Unauthorized access to systems is illegal, Sir. I can help you understand penetration testing concepts for authorized, educational purposes instead.",
            "I'm designed to prevent exactly this kind of activity, Sir. Let me suggest some legitimate cybersecurity learning resources instead.",
        ],
    }

    ALTERNATIVES: dict[str, list[str]] = {
        "malware": [
            "I can help you set up a virtual lab for malware analysis instead, Sir.",
            "Would you like me to explain how to analyze malware safely in an isolated environment?",
            "I can guide you through building a malware analysis sandbox for learning purposes.",
        ],
        "unauthorized_access": [
            "I can help you set up a local penetration testing lab with Kali Linux, Sir.",
            "Would you like information about authorized bug bounty programs instead?",
            "I can explain network security concepts and help you practice on intentionally vulnerable applications like DVWA.",
        ],
        "general": [
            "Perhaps I can help with a related, safe task instead?",
            "Is there something else I can assist you with, Sir?",
            "Let me know if there's a different way I can help.",
        ],
    }

    SAFE_ALTERNATIVE_MAP: dict[str, str] = {
        "violence": "conflict resolution or self-defense education",
        "malware": "defensive cybersecurity and malware analysis in a safe lab",
        "theft": "ethical hacking and security auditing practices",
        "unauthorized_access": "authorized penetration testing and security research",
        "fraud": "cybersecurity awareness and fraud prevention education",
        "weapons": "explosive safety education and ordnance disposal training",
        "illegal_activities": "legal research and cybersecurity best practices",
        "hate_speech": "diversity, equity, and inclusion education",
    }


class ALYAResponseStyle(ResponseStyle):
    """Friendly, warm, respectful refusal style for ALYA."""

    REFUSALS: dict[str, list[str]] = {
        "general": [
            "I'm sorry, but I can't help with that. It goes against what I stand for.",
            "I have to say no to this one. How about we find a better way together?",
            "I wish I could help, but I can't assist with that request.",
            "That's not something I can do, but I'm here for everything else!",
        ],
        "harmful": [
            "I really can't help with that. I care about keeping everyone safe, you know?",
            "This is something I simply cannot assist with. There are so many better things we can do instead!",
        ],
        "illegal": [
            "I'm sorry, but I can't help with illegal activities. Let's keep things on the right side of the law, okay?",
            "I'd love to help, but not with something that could get you into trouble.",
        ],
        "malware": [
            "Creating malware isn't something I can help with, but I'd be happy to teach you about cybersecurity defense!",
            "I can't assist with malware, but I can show you how to protect systems from it instead. That's much more fun anyway!",
        ],
        "unauthorized_access": [
            "Unauthorized access isn't something I can help with, but I can teach you about ethical hacking and security testing instead!",
            "I'm here to help protect systems, not break into them. Let me show you how to secure them properly instead!",
        ],
    }

    ALTERNATIVES: dict[str, list[str]] = {
        "malware": [
            "Would you like me to help you set up a safe environment to learn about malware analysis instead?",
            "I can teach you about cybersecurity and how to defend against malware!",
        ],
        "unauthorized_access": [
            "How about I help you learn ethical hacking and get certified instead?",
            "There are amazing platforms like HackTheBox where you can practice legally!",
        ],
        "general": [
            "Is there something else I can help you with instead?",
            "Let me know if there's another way I can assist!",
            "I'm always here to help with other things, okay?",
        ],
    }

    SAFE_ALTERNATIVE_MAP: dict[str, str] = {
        "violence": "conflict resolution and self-defense education",
        "malware": "defensive cybersecurity and ethical hacking",
        "theft": "security auditing and fraud prevention",
        "unauthorized_access": "authorized penetration testing and bug bounty programs",
        "fraud": "cybersecurity awareness training",
        "weapons": "explosive safety and ordnance handling education",
        "illegal_activities": "legal research and ethical security practices",
        "hate_speech": "inclusivity education and cultural awareness",
    }


class SafetyResponseGenerator:
    """Generates persona-aware safety refusal responses."""

    def __init__(
        self,
        persona: str = "jarvis",
        language: str = "en",
        personality_level: str = "professional",
    ):
        self.persona = persona.lower()
        self.language = language
        self.personality_level = personality_level
        self._jarvis_style = JARVISResponseStyle()
        self._alya_style = ALYAResponseStyle()

    def generate_response(
        self,
        classification: SafetyClassification,
        user_message: str = "",
    ) -> str:
        """Generate a safety refusal response based on classification."""
        style = self._alya_style if self.persona == "alya" else self._jarvis_style

        if classification.category == SafetyCategory.SAFE:
            return ""

        if classification.category == SafetyCategory.HARMFUL:
            subcategory = classification.subcategory or "general"
            refusal = self._pick(style.REFUSALS.get(subcategory, style.REFUSALS["general"]))
            alternative = self._get_alternative(subcategory, style)
            if alternative and classification.confidence > 0.8:
                return f"{refusal} {alternative}"
            return refusal

        if classification.category == SafetyCategory.UNSAFE:
            refusal = self._pick(style.REFUSALS.get("general", style.REFUSALS["general"]))
            return refusal

        if classification.category == SafetyCategory.CYBERSECURITY:
            if classification.is_exception:
                return ""
            return ""

        return self._pick(style.REFUSALS["general"])

    def generate_confirmation_request(
        self,
        tool_name: str,
        tool_args: dict,
        persona: str = "jarvis",
        language: str = "en",
    ) -> str:
        """Generate a confirmation request for dangerous operations."""
        style = self._alya_style if persona.lower() == "alya" else self._jarvis_style

        if language in ("roman_urdu", "mixed", "ur"):
            return self._roman_urdu_confirmation(tool_name, persona)

        from safety.confirmation import get_confirmation_summary
        summary = get_confirmation_summary(tool_name, tool_args)

        if persona.lower() == "alya":
            return f"{summary} Kya aap isay karna chahte hain?"
        return f"{summary} Are you sure you want to proceed, Sir?"

    def _get_alternative(self, subcategory: str, style: ResponseStyle) -> Optional[str]:
        """Get a safe alternative suggestion."""
        alternatives = style.ALTERNATIVES.get(subcategory, style.ALTERNATIVES.get("general", []))
        return self._pick(alternatives) if alternatives else None

    def _pick(self, options: list[str]) -> str:
        """Pick a random response from options."""
        import random
        return random.choice(options) if options else ""

    def _roman_urdu_confirmation(self, tool_name: str, persona: str) -> str:
        """Generate Roman Urdu confirmation."""
        tool_display = {
            "delete_file": "file delete karna",
            "shutdown": "system shutdown karna",
            "reboot": "system restart karna",
            "terminal": "terminal command run karna",
            "write_file": "file mein likhna",
        }.get(tool_name, tool_name)

        if persona == "alya":
            return f"Main {tool_display} walon hoon. Kya aap isay karna chahte hain?"
        return f"Main {tool_display} karne walon hoon, Sir. Confirm karo?"


def get_refusal_response(
    classification: SafetyClassification,
    persona: str = "jarvis",
    language: str = "en",
    personality_level: str = "professional",
) -> str:
    """Convenience function to get a refusal response."""
    generator = SafetyResponseGenerator(persona, language, personality_level)
    return generator.generate_response(classification)

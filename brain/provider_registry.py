"""Provider registry: knows about every AI provider and how to pick one.

Priority values supported by `provider_priority`:
  - auto        : first available in order: local_llm, groq, gemini, openrouter
  - groq_first  : groq, then any other available
  - local_first : local_llm, then any other available
  - gemini_first: gemini, then any other available
  - openrouter_first: openrouter, then any other available
  - groq_only / local_only / gemini_only / openrouter_only
"""

from brain.groq_provider import GroqProvider
from brain.local_provider import LocalLLMProvider
from brain.gemini_provider import GeminiProvider
from brain.openrouter_provider import OpenRouterProvider

_ORDER = ["groq", "gemini", "openrouter", "local_llm"]


def create_providers(settings):
    """Instantiate every provider wired to the shared settings object."""
    return {
        "groq": GroqProvider(settings),
        "local_llm": LocalLLMProvider(settings),
        "gemini": GeminiProvider(settings),
        "openrouter": OpenRouterProvider(settings),
    }


def select_provider(providers: dict, priority: str = "auto"):
    """Pick the active provider based on the configured priority."""
    priority = (priority or "auto").lower()

    def available(names):
        for name in names:
            provider = providers.get(name)
            if provider and provider.is_available():
                return provider
        return None

    if priority in ("groq_only", "local_only", "gemini_only", "openrouter_only"):
        name = priority.split("_")[0]
        provider = providers.get(name)
        return provider if provider and provider.is_available() else None

    first = {
        "groq_first": "groq",
        "local_first": "local_llm",
        "gemini_first": "gemini",
        "openrouter_first": "openrouter",
    }.get(priority)

    if first and providers.get(first, None) and providers[first].is_available():
        return providers[first]

    if priority == "auto":
        return available(["local_llm", "groq", "gemini", "openrouter"])

    return available([n for n in _ORDER if n != first])

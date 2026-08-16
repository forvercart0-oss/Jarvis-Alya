"""Skill router: lightweight message-to-skill matching.

Flow
----
USER MESSAGE
      |
      v
INTENT ANALYSIS
      |
      v
SKILL MATCHING
      |
      v
SELECT SKILL
      |
      v
PERMISSION CHECK   (handled downstream by SkillExecutor / PermissionManager)
      |
      v
SAFETY CHECK       (handled downstream by SafetyChecker)
      |
      v
AI / TOOL EXECUTION

If no skill matches, the caller falls back to the existing general AI
system (Groq / local LLM / heuristic router).  A skill must never
override system safety.
"""

from __future__ import annotations

import logging
from typing import Any

from skills.registry import SkillRegistry

logger = logging.getLogger("jarvis.skills.router")

_PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}


class SkillRouter:
    """Matches user messages against enabled skills using trigger keywords.

    The router is deliberately lightweight: it does not call any external
    model or execute skill code.  It simply scans trigger lists and
    returns the best match based on:

    1. trigger relevance (more trigger hits rank higher)
    2. priority (high > normal > low)
    3. enabled state (only enabled skills participate)
    """

    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    def match(self, text: str) -> list[dict[str, Any]]:
        """Return all enabled skills whose triggers match *text*.

        Results are sorted by priority (high first) and then by the
        number of matched triggers (most relevant first).
        """
        text_lower = text.lower()
        scored: list[tuple[int, int, dict[str, Any]]] = []

        for skill in self._registry.list_enabled():
            triggers = skill.get("triggers", [])
            hits = sum(1 for trigger in triggers if trigger.lower() in text_lower)
            if hits == 0:
                continue
            priority_rank = _PRIORITY_RANK.get(skill.get("priority", "normal"), 1)
            scored.append((priority_rank, -hits, skill))

        scored.sort(key=lambda entry: (entry[0], entry[1]))
        return [entry[2] for entry in scored]

    def match_one(self, text: str) -> dict[str, Any] | None:
        """Return the single best matching skill, or ``None``."""
        matches = self.match(text)
        return matches[0] if matches else None

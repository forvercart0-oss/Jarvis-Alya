"""Central safety checker.

Every tool-capable request passes through this layer before reaching a tool or
skill. It combines request classification and tool policy evaluation into a
single verdict: SAFE / CAUTION / REQUIRES_CONFIRMATION / DISALLOWED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from safety.classifier import SafetyCategory, classify_request
from safety.policy import PolicyAction, RiskLevel, get_policy_engine


class SafetyVerdict(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DISALLOWED = "disallowed"


@dataclass
class SafetyCheckResult:
    verdict: SafetyVerdict
    message: str = ""
    risk: str = "low"
    matched_keywords: list[str] = field(default_factory=list)
    subcategory: str | None = None


def _policy_risk(policy) -> str:
    if policy is None:
        return "medium"
    try:
        return policy.risk_level.value if isinstance(policy.risk_level, RiskLevel) else str(policy.risk_level)
    except Exception:
        return "medium"


class SafetyChecker:
    """Combines request classification and tool policy checks."""

    def check_request(self, text: str) -> SafetyCheckResult:
        classification = classify_request(text)
        if classification.category == SafetyCategory.HARMFUL:
            return SafetyCheckResult(
                verdict=SafetyVerdict.DISALLOWED,
                message="This request is not permitted.",
                risk=classification.severity.value,
                matched_keywords=classification.matched_keywords,
                subcategory=classification.subcategory,
            )
        if classification.category == SafetyCategory.UNSAFE:
            return SafetyCheckResult(
                verdict=SafetyVerdict.CAUTION,
                message="This request is risky and will be handled carefully.",
                risk=classification.severity.value,
                matched_keywords=classification.matched_keywords,
                subcategory=classification.subcategory,
            )
        return SafetyCheckResult(verdict=SafetyVerdict.SAFE, risk="low")

    def check_tool(self, tool_name: str, arguments: dict | None = None, confirmed: bool = False) -> SafetyCheckResult:
        policy_engine = get_policy_engine()
        policy = policy_engine.check_tool_policy(tool_name)
        action, message = policy_engine.evaluate_request(tool_name, arguments or {})

        if action == PolicyAction.DENY:
            return SafetyCheckResult(
                verdict=SafetyVerdict.DISALLOWED,
                message=message or f"Tool {tool_name} is not permitted.",
                risk=_policy_risk(policy),
            )
        if action == PolicyAction.ASK and not confirmed:
            return SafetyCheckResult(
                verdict=SafetyVerdict.REQUIRES_CONFIRMATION,
                message=message or f"Confirm execution of {tool_name}?",
                risk=_policy_risk(policy),
            )
        risk = _policy_risk(policy)
        verdict = SafetyVerdict.CAUTION if risk in ("medium", "high", "critical") else SafetyVerdict.SAFE
        return SafetyCheckResult(verdict=verdict, message="", risk=risk)


_checker: SafetyChecker | None = None


def get_safety_checker() -> SafetyChecker:
    global _checker
    if _checker is None:
        _checker = SafetyChecker()
    return _checker

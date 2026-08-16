"""Safety layer for JARVIS 2.0.

Provides request classification, policy enforcement, refusal responses,
and confirmation handling for dangerous operations.
"""

from __future__ import annotations

from safety.classifier import SafetyClassifier, SafetyCategory, classify_request
from safety.confirmation import get_confirmation_manager, get_confirmation_summary
from safety.policy import PolicyEngine, get_policy_engine, PolicyAction
from safety.response import SafetyResponseGenerator, get_refusal_response

__all__ = [
    "SafetyClassifier",
    "SafetyCategory",
    "classify_request",
    "get_confirmation_manager",
    "get_confirmation_summary",
    "PolicyEngine",
    "get_policy_engine",
    "PolicyAction",
    "SafetyResponseGenerator",
    "get_refusal_response",
]

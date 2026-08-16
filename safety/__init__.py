"""Safety layer for JARVIS 2.0.

Provides request classification, policy enforcement, refusal responses,
and confirmation handling for dangerous operations.
"""

from __future__ import annotations

from safety.activity import ActivityLogger, get_activity_logger, mask_sensitive
from safety.checker import SafetyChecker, SafetyCheckResult, SafetyVerdict, get_safety_checker
from safety.classifier import SafetyCategory, SafetyClassifier, classify_request
from safety.confirmation import get_confirmation_manager, get_confirmation_summary
from safety.policy import PolicyAction, PolicyEngine, get_policy_engine
from safety.response import SafetyResponseGenerator, get_refusal_response

__all__ = [
    "ActivityLogger",
    "PolicyAction",
    "PolicyEngine",
    "SafetyCategory",
    "SafetyCheckResult",
    "SafetyChecker",
    "SafetyClassifier",
    "SafetyResponseGenerator",
    "SafetyVerdict",
    "classify_request",
    "get_activity_logger",
    "get_confirmation_manager",
    "get_confirmation_summary",
    "get_policy_engine",
    "get_refusal_response",
    "get_safety_checker",
    "mask_sensitive",
]

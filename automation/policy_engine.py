"""Automation policy engine for JARVIS Phase 22.

Extends the existing safety policy system with authorization scopes
for Full Auto Mode. Instead of asking permission for every individual
action, the user authorizes categories once.

Categories:
FILES, TERMINAL, BROWSER, APPLICATIONS, SYSTEM, CODING,
DOCUMENTS, NETWORK, COMMUNICATION, VISION, AUTOMATION
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from safety.policy import PolicyAction, RiskLevel, get_policy_engine

logger = logging.getLogger("jarvis.automation.policy")

AUTOMATION_SCOPES = [
    "files",
    "terminal",
    "browser",
    "applications",
    "system",
    "coding",
    "documents",
    "network",
    "communication",
    "vision",
    "automation",
]


class ExecutionMode(str, Enum):
    ASSISTED = "assisted"
    FULL_AUTO = "full_auto"
    SAFE = "safe"


@dataclass(frozen=True)
class AutomationScopePolicy:
    """Policy for a single automation scope."""

    scope: str
    enabled: bool = False
    allowed_tools: tuple[str, ...] = ()
    denied_tools: tuple[str, ...] = ()
    max_retries: int = 3
    require_verification: bool = True
    allow_parallel: bool = True


@dataclass(frozen=True)
class AutomationProfile:
    """A named automation profile with preconfigured scopes."""

    name: str
    description: str
    scopes: dict[str, AutomationScopePolicy]


DEFAULT_PROFILES: dict[str, AutomationProfile] = {
    "safe": AutomationProfile(
        name="safe",
        description="Minimal automation with confirmations",
        scopes={
            "files": AutomationScopePolicy(scope="files", enabled=True, allowed_tools=("read_file",)),
            "terminal": AutomationScopePolicy(scope="terminal", enabled=False),
            "browser": AutomationScopePolicy(scope="browser", enabled=False),
            "applications": AutomationScopePolicy(scope="applications", enabled=False),
            "system": AutomationScopePolicy(scope="system", enabled=False),
            "coding": AutomationScopePolicy(scope="coding", enabled=False),
            "documents": AutomationScopePolicy(scope="documents", enabled=True, allowed_tools=("read_file",)),
            "network": AutomationScopePolicy(scope="network", enabled=False),
            "communication": AutomationScopePolicy(scope="communication", enabled=False),
            "vision": AutomationScopePolicy(scope="vision", enabled=False),
            "automation": AutomationScopePolicy(scope="automation", enabled=False),
        },
    ),
    "development": AutomationProfile(
        name="development",
        description="Development workflow automation",
        scopes={
            "files": AutomationScopePolicy(scope="files", enabled=True),
            "terminal": AutomationScopePolicy(scope="terminal", enabled=True),
            "browser": AutomationScopePolicy(scope="browser", enabled=True),
            "applications": AutomationScopePolicy(scope="applications", enabled=True),
            "system": AutomationScopePolicy(scope="system", enabled=False),
            "coding": AutomationScopePolicy(scope="coding", enabled=True),
            "documents": AutomationScopePolicy(scope="documents", enabled=True),
            "network": AutomationScopePolicy(scope="network", enabled=False),
            "communication": AutomationScopePolicy(scope="communication", enabled=False),
            "vision": AutomationScopePolicy(scope="vision", enabled=False),
            "automation": AutomationScopePolicy(scope="automation", enabled=True),
        },
    ),
    "full_auto": AutomationProfile(
        name="full_auto",
        description="Full automation for authorized categories",
        scopes={
            scope: AutomationScopePolicy(scope=scope, enabled=True)
            for scope in AUTOMATION_SCOPES
        },
    ),
}

TOOL_SCOPE_MAP: dict[str, str] = {
    "read_file": "files",
    "write_file": "files",
    "delete_file": "files",
    "list_directory": "files",
    "terminal": "terminal",
    "run_project_command": "terminal",
    "execute_shell": "terminal",
    "open_browser": "browser",
    "browser_navigate": "browser",
    "browser_click": "browser",
    "browser_type": "browser",
    "open_application": "applications",
    "close_application": "applications",
    "shutdown": "system",
    "reboot": "system",
    "suspend": "system",
    "lock_screen": "system",
    "system_info": "system",
    "code_edit": "coding",
    "run_tests": "coding",
    "create_project": "coding",
    "write_project_file": "coding",
    "create_document": "documents",
    "edit_document": "documents",
    "web_search": "network",
    "send_message": "communication",
    "vision_capture_screen": "vision",
    "vision_analyze_screen": "vision",
    "execute_automation": "automation",
    "format_disk": "system",
}


class AutomationPolicyEngine:
    """Enforces automation scopes and execution mode policies."""

    def __init__(
        self,
        execution_mode: str = ExecutionMode.ASSISTED.value,
        enabled_scopes: dict[str, bool] | None = None,
        profile: str = "safe",
    ):
        self._execution_mode = ExecutionMode(execution_mode)
        self._enabled_scopes: dict[str, bool] = enabled_scopes or {
            scope: False for scope in AUTOMATION_SCOPES
        }
        self._profile = profile
        self._policy_engine = get_policy_engine()

    @property
    def execution_mode(self) -> ExecutionMode:
        return self._execution_mode

    @property
    def profile(self) -> str:
        return self._profile

    def set_execution_mode(self, mode: str) -> None:
        self._execution_mode = ExecutionMode(mode)

    def set_profile(self, profile: str) -> None:
        if profile in DEFAULT_PROFILES:
            self._profile = profile
            for scope, policy in DEFAULT_PROFILES[profile].scopes.items():
                self._enabled_scopes[scope] = policy.enabled

    def set_scope(self, scope: str, enabled: bool) -> None:
        if scope in AUTOMATION_SCOPES:
            self._enabled_scopes[scope] = enabled

    def is_scope_enabled(self, scope: str) -> bool:
        return self._enabled_scopes.get(scope, False)

    def get_enabled_scopes(self) -> dict[str, bool]:
        return dict(self._enabled_scopes)

    def evaluate_tool(self, tool_name: str, confirmed: bool = False) -> tuple[PolicyAction, str]:
        """Evaluate a tool call against automation policies.

        Returns (action, message).
        """
        scope = TOOL_SCOPE_MAP.get(tool_name)
        if not scope:
            return PolicyAction.ASK, f"Unknown scope for tool {tool_name}"

        base_policy = self._policy_engine.check_tool_policy(tool_name)
        if base_policy.action == PolicyAction.DENY:
            return PolicyAction.DENY, f"This action ({tool_name}) is not permitted."

        if self._execution_mode == ExecutionMode.FULL_AUTO:
            if self._enabled_scopes.get(scope, False):
                return PolicyAction.ALLOW, None
            return PolicyAction.ASK, f"Scope '{scope}' is not enabled for Full Auto Mode."

        if self._execution_mode == ExecutionMode.SAFE:
            return PolicyAction.ASK, base_policy.confirmation_message or f"Confirm {tool_name}?"

        if confirmed:
            return PolicyAction.ALLOW, None

        if base_policy.action == PolicyAction.ALLOW:
            return PolicyAction.ALLOW, None

        return PolicyAction.ASK, base_policy.confirmation_message or f"Confirm {tool_name}?"

    def should_auto_execute(self, tool_name: str) -> bool:
        """Check if a tool should be auto-executed without confirmation."""
        if self._execution_mode == ExecutionMode.SAFE:
            return False
        scope = TOOL_SCOPE_MAP.get(tool_name)
        if not scope:
            return False
        if not self._enabled_scopes.get(scope, False):
            return False
        base_policy = self._policy_engine.check_tool_policy(tool_name)
        return base_policy.action != PolicyAction.DENY

    def get_profile_summary(self) -> dict[str, Any]:
        return {
            "execution_mode": self._execution_mode.value,
            "profile": self._profile,
            "scopes": self._enabled_scopes,
            "available_profiles": list(DEFAULT_PROFILES.keys()),
        }

    def get_scope_summary(self) -> dict[str, Any]:
        return {
            "scopes": {
                scope: {
                    "enabled": enabled,
                    "profile": self._profile,
                }
                for scope, enabled in self._enabled_scopes.items()
            }
        }


_automation_policy_engine: AutomationPolicyEngine | None = None


def get_automation_policy_engine(
    execution_mode: str = ExecutionMode.ASSISTED.value,
    enabled_scopes: dict[str, bool] | None = None,
    profile: str = "safe",
) -> AutomationPolicyEngine:
    """Get or create the global automation policy engine."""
    global _automation_policy_engine
    if _automation_policy_engine is None:
        _automation_policy_engine = AutomationPolicyEngine(
            execution_mode=execution_mode,
            enabled_scopes=enabled_scopes,
            profile=profile,
        )
    return _automation_policy_engine


def reset_automation_policy_engine() -> None:
    """Reset the global automation policy engine (for tests)."""
    global _automation_policy_engine
    _automation_policy_engine = None

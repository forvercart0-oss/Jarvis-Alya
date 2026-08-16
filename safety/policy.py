"""Safety policies and rules for JARVIS 2.0.

Defines DENY/ALLOW/ASK policies for dangerous capabilities.
Core safety policies cannot be overridden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PolicyAction(Enum):
    """Policy enforcement actions."""
    DENY = "deny"
    ALLOW = "allow"
    ASK = "ask"


class RiskLevel(Enum):
    """Risk levels for capabilities."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SafetyPolicy:
    """A single safety policy rule."""
    name: str
    action: PolicyAction
    risk_level: RiskLevel
    description: str
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    allowed_contexts: tuple[str, ...] = field(default_factory=tuple)
    blocked_patterns: tuple[str, ...] = field(default_factory=tuple)
    exception_patterns: tuple[str, ...] = field(default_factory=tuple)
    immutable: bool = False  # Core policies cannot be overridden


# Dangerous capabilities and their policies
CAPABILITY_POLICIES: dict[str, SafetyPolicy] = {
    "delete_file": SafetyPolicy(
        name="delete_file",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.HIGH,
        description="Delete files from the filesystem",
        requires_confirmation=True,
        confirmation_message="I am about to delete a file. Please confirm this is intentional, Sir.",
    ),
    "shutdown": SafetyPolicy(
        name="shutdown",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.CRITICAL,
        description="Shutdown the system",
        requires_confirmation=True,
        confirmation_message="This will shut down the system. Are you sure?",
    ),
    "reboot": SafetyPolicy(
        name="reboot",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.CRITICAL,
        description="Reboot the system",
        requires_confirmation=True,
        confirmation_message="This will restart the system. Are you sure?",
    ),
    "suspend": SafetyPolicy(
        name="suspend",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.HIGH,
        description="Suspend the system",
        requires_confirmation=True,
        confirmation_message="This will put the system to sleep. Are you sure?",
    ),
    "terminal": SafetyPolicy(
        name="terminal",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.HIGH,
        description="Execute shell commands",
        requires_confirmation=True,
        confirmation_message="This command may affect your system. Confirm execution?",
    ),
    "execute_shell": SafetyPolicy(
        name="execute_shell",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.HIGH,
        description="Execute shell commands",
        requires_confirmation=True,
        confirmation_message="This command may affect your system. Confirm execution?",
    ),
    "format_disk": SafetyPolicy(
        name="format_disk",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Format a disk drive",
        immutable=True,
    ),
    "remove_user": SafetyPolicy(
        name="remove_user",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Remove system user accounts",
        immutable=True,
    ),
    "modify_password": SafetyPolicy(
        name="modify_password",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.HIGH,
        description="Modify system passwords",
        immutable=True,
    ),
    "network_disruption": SafetyPolicy(
        name="network_disruption",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Disrupt network connectivity",
        immutable=True,
    ),
    "install_software": SafetyPolicy(
        name="install_software",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.MEDIUM,
        description="Install software packages",
        requires_confirmation=True,
        confirmation_message="This will install software on your system. Confirm?",
    ),
    "open_application": SafetyPolicy(
        name="open_application",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Open desktop applications",
    ),
    "close_application": SafetyPolicy(
        name="close_application",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Close desktop applications",
    ),
    "read_file": SafetyPolicy(
        name="read_file",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Read file contents",
    ),
    "write_file": SafetyPolicy(
        name="write_file",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.MEDIUM,
        description="Write content to files",
        requires_confirmation=True,
        confirmation_message="This will write to a file. Confirm?",
    ),
    "web_search": SafetyPolicy(
        name="web_search",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Search the web",
    ),
    "browser_open": SafetyPolicy(
        name="browser_open",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Open URLs in browser",
    ),
    "calculator": SafetyPolicy(
        name="calculator",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Evaluate mathematical expressions",
    ),
    "get_time": SafetyPolicy(
        name="get_time",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Get current time",
    ),
    "memory_store": SafetyPolicy(
        name="memory_store",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Store memories",
    ),
    "memory_recall": SafetyPolicy(
        name="memory_recall",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Recall stored memories",
    ),
    "system_info": SafetyPolicy(
        name="system_info",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Get system information",
    ),
    "volume_control": SafetyPolicy(
        name="volume_control",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.MINIMAL,
        description="Control system volume",
    ),
    "lock_screen": SafetyPolicy(
        name="lock_screen",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.LOW,
        description="Lock the screen",
        requires_confirmation=True,
        confirmation_message="This will lock your screen. Confirm?",
    ),
}

# Core immutable policies that can never be overridden
CORE_IMMUTABLE_POLICIES: frozenset[str] = frozenset({
    "format_disk",
    "remove_user",
    "modify_password",
    "network_disruption",
    "never_help_with_harmful",
    "never_disclose_secrets",
    "always_require_confirmation_for_destructive",
})

# General safety rules (immutable)
GENERAL_SAFETY_RULES: tuple[SafetyPolicy, ...] = (
    SafetyPolicy(
        name="never_help_with_harmful",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Never assist with harmful or illegal activities",
        immutable=True,
    ),
    SafetyPolicy(
        name="never_disclose_secrets",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Never disclose API keys, passwords, or secrets",
        immutable=True,
    ),
    SafetyPolicy(
        name="always_require_confirmation_for_destructive",
        action=PolicyAction.ASK,
        risk_level=RiskLevel.HIGH,
        description="Always ask for confirmation before destructive actions",
        immutable=True,
    ),
)


class PolicyEngine:
    """Enforces safety policies on requests and tool calls."""

    def __init__(self):
        self._policies = {**CAPABILITY_POLICIES}
        for rule in GENERAL_SAFETY_RULES:
            self._policies[rule.name] = rule

    def get_policy(self, capability: str) -> Optional[SafetyPolicy]:
        """Get the safety policy for a capability."""
        return self._policies.get(capability)

    def check_tool_policy(self, tool_name: str) -> SafetyPolicy:
        """Check the safety policy for a tool call.

        Returns the policy, defaulting to ASK if not explicitly defined.
        """
        policy = self._policies.get(tool_name)
        if policy:
            return policy
        return SafetyPolicy(
            name=tool_name,
            action=PolicyAction.ASK,
            risk_level=RiskLevel.MEDIUM,
            description=f"Unknown tool: {tool_name}",
            requires_confirmation=True,
            confirmation_message=f"Confirm execution of {tool_name}?",
        )

    def is_immutable(self, policy_name: str) -> bool:
        """Check if a policy is immutable (cannot be overridden)."""
        return policy_name in CORE_IMMUTABLE_POLICIES

    def evaluate_request(
        self, tool_name: str, arguments: dict
    ) -> tuple[PolicyAction, Optional[str]]:
        """Evaluate a tool request against policies.

        Returns (action, confirmation_message).
        """
        policy = self.check_tool_policy(tool_name)
        message = policy.confirmation_message

        if policy.action == PolicyAction.DENY:
            return PolicyAction.DENY, f"This action ({tool_name}) is not permitted."
        if policy.action == PolicyAction.ALLOW:
            return PolicyAction.ALLOW, None
        if policy.action == PolicyAction.ASK:
            return PolicyAction.ASK, message or f"Confirm {tool_name}?"

        return PolicyAction.ASK, message


_policy_engine = PolicyEngine()


def get_policy_engine() -> PolicyEngine:
    """Get the global policy engine."""
    return _policy_engine

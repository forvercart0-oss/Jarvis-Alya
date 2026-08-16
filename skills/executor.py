"""Skill executor: runs skills under their permission sandbox.

The executor NEVER executes code from the skill JSON itself. Skills are
declarative configuration: instructions are prompts, capabilities declare what
the skill wants to do, and the executor enforces that tool calls stay within
the user-granted permissions.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from permissions.manager import PermissionManager
from permissions.policy import required_permissions_for_tool
from permissions.registry import requested_permissions
from skills.registry import SkillRegistry

logger = logging.getLogger("jarvis.skills.executor")


class PermissionDeniedError(Exception):
    """Raised when a skill attempts an action outside its permissions."""


class SkillExecutor:
    """Executes skills through tool permissions and sandbox restrictions."""

    def __init__(
        self,
        registry: SkillRegistry,
        permission_manager: PermissionManager,
        tool_execute: Callable[..., Coroutine[Any, Any, Any]] | None = None,
    ):
        self._registry = registry
        self._permissions = permission_manager
        self._tool_execute = tool_execute

    # ------------------------------------------------------------ permission checks
    def requested_permissions(self, skill_id: str) -> set[str]:
        skill = self._registry.get(skill_id)
        return requested_permissions(skill) if skill else set()

    def missing_permissions(self, skill_id: str) -> dict[str, bool]:
        skill = self._registry.get(skill_id)
        return self._permissions.pending(skill_id, skill) if skill else {}

    def is_tool_allowed(self, skill_id: str, tool_name: str) -> tuple[bool, str]:
        """Check whether a skill may execute a tool under its granted permissions.

        Returns (allowed, reason). Default is deny when a required permission
        was requested by the skill but not granted.
        """
        skill = self._registry.get(skill_id)
        if skill is None:
            return False, f"Skill {skill_id} not found."
        if not skill.get("enabled", True):
            return False, f"Skill {skill_id} is disabled."
        if not self._permissions.is_tool_allowed(skill_id, tool_name, skill):
            required = required_permissions_for_tool(tool_name)
            requested = requested_permissions(skill)
            needed = ", ".join(sorted(set(required) & requested)) or ", ".join(sorted(required))
            return False, (
                f"Skill '{skill.get('name', skill_id)}' is missing required "
                f"permission(s): {needed}."
            )
        return True, ""

    def filter_tools_by_permissions(self, skill_id: str, tool_names: list[str]) -> list[str]:
        """Filter a list of tool names to only those allowed for the skill."""
        skill = self._registry.get(skill_id)
        if skill is None:
            return []
        allowed: list[str] = []
        for tool_name in tool_names:
            ok, _ = self.is_tool_allowed(skill_id, tool_name)
            if ok:
                allowed.append(tool_name)
            else:
                logger.debug("Skill %s denied access to tool %s.", skill_id, tool_name)
        return allowed

    # ------------------------------------------------------------ execution
    async def execute_skill_instructions(
        self,
        skill_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a skill's instructions within its permission sandbox.

        Args:
            skill_id: The skill to execute.
            context: Execution context (user message, tool name, arguments).

        Returns:
            Result dict with status and any output.

        Raises:
            PermissionDeniedError: If the skill lacks required permissions.
            KeyError: If the skill does not exist.
        """
        skill = self._registry.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill not found: {skill_id}")

        if not skill.get("enabled", True):
            raise PermissionDeniedError(f"Skill {skill_id} is disabled.")

        tool_name = context.get("tool_name", "")
        if tool_name:
            allowed, reason = self.is_tool_allowed(skill_id, tool_name)
            if not allowed:
                raise PermissionDeniedError(reason)
            if self._tool_execute is not None:
                result = await self._tool_execute(
                    tool_name, context.get("arguments", {})
                )
                return {
                    "skill_id": skill_id,
                    "status": "executed",
                    "result": result,
                }

        return {
            "skill_id": skill_id,
            "status": "success",
            "instructions": skill.get("instructions", []),
            "capabilities": skill.get("capabilities", []),
            "permissions_used": sorted(requested_permissions(skill)),
        }

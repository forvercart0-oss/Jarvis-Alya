"""Skill executor: runs skills under their permission sandbox."""

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

from skills.registry import SkillRegistry

logger = logging.getLogger("jarvis.skills.executor")


class PermissionDeniedError(Exception):
    """Raised when a skill attempts an action outside its permissions."""


class SkillExecutor:
    """Executes skills through tool permissions and sandbox restrictions.

    The executor NEVER runs code from the skill JSON itself. It only reads
    the skill's instructions and permissions, then routes allowed tool calls
    through the actual tool registry.
    """

    def __init__(self, registry: SkillRegistry, tool_execute: Callable[..., Coroutine[Any, Any, Any]]):
        self._registry = registry
        self._tool_execute = tool_execute

    async def execute_skill_instructions(
        self,
        skill_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a skill's instructions within its permission sandbox.

        Args:
            skill_id: The skill to execute.
            context: Execution context (user message, available tools, etc.).

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

        permissions = self._registry.map_permissions_to_capabilities(skill)
        result: dict[str, Any] = {
            "skill_id": skill_id,
            "status": "success",
            "permissions_used": [],
        }

        if not permissions.get("terminal", False) and context.get("requires_terminal"):
            raise PermissionDeniedError(
                f"Skill {skill_id} does not have terminal permission."
            )

        if not permissions.get("network", False) and context.get("requires_network"):
            raise PermissionDeniedError(
                f"Skill {skill_id} does not have network permission."
            )

        if not permissions.get("filesystem_write", False) and context.get("requires_write"):
            raise PermissionDeniedError(
                f"Skill {skill_id} does not have filesystem_write permission."
            )

        for instruction in skill.get("instructions", []):
            logger.debug("Skill %s instruction: %s", skill_id, instruction)

        result["instructions"] = skill.get("instructions", [])
        result["capabilities"] = skill.get("capabilities", [])
        result["permissions"] = permissions
        return result

    async def filter_tools_by_permissions(
        self,
        skill_id: str,
        tool_names: list[str],
    ) -> list[str]:
        """Filter a list of tool names to only those allowed by the skill's permissions.

        Args:
            skill_id: The skill whose permissions to apply.
            tool_names: List of tool names to filter.

        Returns:
            Filtered list of allowed tool names.
        """
        skill = self._registry.get(skill_id)
        if skill is None:
            return []

        permissions = self._registry.map_permissions_to_capabilities(skill)
        allowed: list[str] = []

        for tool_name in tool_names:
            if self._is_tool_allowed(tool_name, permissions):
                allowed.append(tool_name)
            else:
                logger.debug(
                    "Skill %s denied access to tool %s.", skill_id, tool_name
                )

        return allowed

    def _is_tool_allowed(self, tool_name: str, permissions: dict[str, bool]) -> bool:
        """Map a tool name to a permission category and check if allowed."""
        tool_read_perm = {
            "read_file",
            "system_info",
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "battery_status",
            "get_time",
            "get_date",
            "recall_memories",
            "list_files",
            "list_projects",
            "list_project_files",
        }
        tool_write_perm = {
            "write_file",
            "delete_file",
            "create_project",
            "delete_project",
            "write_project_file",
        }
        tool_terminal_perm = {
            "terminal",
            "run_project_command",
            "shutdown",
            "reboot",
            "suspend",
            "lock_screen",
        }
        tool_network_perm = {
            "open_browser",
            "web_search",
            "generate_image",
            "generate_video",
        }

        if tool_name in tool_write_perm and not permissions.get("filesystem_write", False):
            return False
        if tool_name in tool_terminal_perm and not permissions.get("terminal", False):
            return False
        if tool_name in tool_network_perm and not permissions.get("network", False):
            return False
        if tool_name in tool_read_perm and not permissions.get("filesystem_read", False):
            return False
        return True

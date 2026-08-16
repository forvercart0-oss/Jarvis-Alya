"""Permission policy rules for JARVIS 2.0.

Default-deny policy: a permission is only granted when the user explicitly
approves it. Tool names map to the canonical permission(s) they require.
"""

from __future__ import annotations

from dataclasses import dataclass

from permissions.models import PERMISSION_DESCRIPTIONS


@dataclass(frozen=True)
class PermissionRule:
    permission: str
    risk: str
    default_denied: bool = True


PERMISSION_RULES: dict[str, PermissionRule] = {
    perm: PermissionRule(perm, PERMISSION_DESCRIPTIONS[perm].risk)
    for perm in PERMISSION_DESCRIPTIONS
}

# Tool name -> canonical permission(s) required to execute it.
TOOL_PERMISSION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "read_file": ("filesystem.read",),
    "list_projects": ("filesystem.read",),
    "list_project_files": ("filesystem.read",),
    "read_project_file": ("filesystem.read",),
    "write_file": ("filesystem.write",),
    "delete_file": ("filesystem.write",),
    "create_project": ("filesystem.write",),
    "delete_project": ("filesystem.write",),
    "write_project_file": ("filesystem.write",),
    "terminal": ("terminal.read", "terminal.execute"),
    "run_project_command": ("terminal.read", "terminal.execute"),
    "shutdown": ("terminal.execute",),
    "reboot": ("terminal.execute",),
    "suspend": ("terminal.execute",),
    "lock_screen": ("terminal.execute",),
    "set_screen_brightness": ("terminal.execute",),
    "set_do_not_disturb": ("terminal.execute",),
    "type_text": ("terminal.execute",),
    "click_at": ("terminal.execute",),
    "open_browser": ("network.request",),
    "web_search": ("network.request",),
    "generate_image": ("network.request",),
    "generate_video": ("network.request",),
    "remember": ("memory.write",),
    "forget": ("memory.write",),
    "recall_memories": ("memory.read",),
    "volume_control": ("terminal.execute",),
    "take_screenshot": ("camera",),
}

# Tools that only require read-ish system introspection and are safe by default.
OBSERVATION_ONLY_TOOLS: frozenset[str] = frozenset({
    "system_info",
    "cpu_usage",
    "memory_usage",
    "disk_usage",
    "battery_status",
    "get_time",
    "get_date",
    "calculator",
    "open_application",
    "close_application",
})


def required_permissions_for_tool(tool_name: str) -> tuple[str, ...]:
    """Return the canonical permissions required for a tool name.

    Observation-only tools require no explicit permission grant.
    """
    return TOOL_PERMISSION_REQUIREMENTS.get(tool_name, ())

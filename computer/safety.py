"""Computer control safety for JARVIS Phase 19."""

from __future__ import annotations

import re

_DANGEROUS_COMMANDS = re.compile(
    r"\b(rm\s+-rf|dd\s+|mkfs|fdisk|sudo\s+rm|shutdown|reboot|halt|poweroff|kill\s+-9|pkill\s+-9|chmod\s+777|chown\s+root|format\s+|:\(\)\{\s*:\|\:&\s*\};:)\b",
    re.IGNORECASE,
)
_SENSITIVE_COMMANDS = re.compile(
    r"\b(sudo|su\s|passwd|useradd|userdel|groupadd|groupdel|iptables|ufw\s|firewall-cmd|systemctl\s+(start|stop|restart|enable|disable)|service\s+\w+\s+(stop|restart)|npm\s+install\s+-g|pip\s+install|apt\s+(remove|purge)|yum\s+remove|dnf\s+remove|brew\s+uninstall)\b",
    re.IGNORECASE,
)


class ComputerSafety:
    DANGEROUS_ACTIONS = {"shutdown", "reboot", "suspend", "lock_screen", "close_application", "close_window", "delete_file"}
    CONFIRMATION_ACTIONS = {
        "open_application", "type_text", "click_at", "double_click_at",
        "right_click_at", "mouse_drag", "mouse_scroll", "hotkey",
        "press_key", "focus_window", "move_window", "resize_window",
        "launch_application", "run_command", "create_folder", "rename_file",
        "move_file", "copy_file", "delete_file", "open_file",
        "stop_process", "restart_process",
    }
    ALWAYS_ALLOW = {"get_cursor_position", "get_active_window", "list_windows", "get_screen_info", "list_processes", "get_monitors", "read_clipboard"}

    def is_allowed(self, action: str) -> bool:
        return action not in self.DANGEROUS_ACTIONS

    def requires_confirmation(self, action: str) -> bool:
        if action in self.ALWAYS_ALLOW:
            return False
        return action in self.CONFIRMATION_ACTIONS or action in self.DANGEROUS_ACTIONS

    def is_dangerous(self, action: str) -> bool:
        return action in self.DANGEROUS_ACTIONS

    @staticmethod
    def classify_command(command: str) -> str:
        if _DANGEROUS_COMMANDS.search(command):
            return "DESTRUCTIVE"
        if _SENSITIVE_COMMANDS.search(command):
            return "SENSITIVE"
        return "SAFE"

    @staticmethod
    def is_dangerous_command(command: str) -> bool:
        return ComputerSafety.classify_command(command) == "DESTRUCTIVE"

    @staticmethod
    def is_sensitive_command(command: str) -> bool:
        return ComputerSafety.classify_command(command) == "SENSITIVE"

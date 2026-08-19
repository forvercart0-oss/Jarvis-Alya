import subprocess
from tools.registry import ToolResult


DANGEROUS_PATTERNS = [
    "rm -rf", "mkfs", "dd if", "shutdown", "reboot", "poweroff",
    "fdisk", "parted", "mkfs", "fsck", "> /dev/", "chmod -R 777 /",
    "sudo rm", "sudo dd", "curl | sh", "wget | sh", ":(){", "nc -e",
    "airodump-ng", "aireplay-ng", "mdk3", "mdk4",
]


class TerminalTool:
    name = "terminal"
    description = "Run a terminal command."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to run"},
        },
        "required": ["command"],
    }

    async def execute(self, command: str, **kwargs) -> ToolResult:
        if not command.strip():
            return ToolResult(success=False, error="Empty command.")
        lower = command.lower()
        blocked = ["airodump-ng", "aireplay-ng", "mdk3", "mdk4", "deauth", "nc -e", "/bin/sh"]
        for pat in blocked:
            if pat in lower:
                return ToolResult(success=False, error="Command blocked for safety.")
        for pat in DANGEROUS_PATTERNS:
            if pat in lower:
                return ToolResult(
                    success=False,
                    confirmation_required=True,
                    confirmation_message=f"Confirm execution of: {command}",
                )
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return ToolResult(success=True, stdout=result.stdout.strip(), stderr=result.stderr.strip())
            return ToolResult(success=False, error=result.stderr.strip() or result.stdout.strip())
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Command timed out after 30 seconds.")
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

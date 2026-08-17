"""Secure command executor for JARVIS Phase 13."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shlex
import subprocess
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.automation.commands")


class CommandResult:
    def __init__(self, command: str, exit_code: int, stdout: str, stderr: str, duration: float):
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.success = exit_code == 0


_DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"mkfs",
    r"dd\s+.*\/dev\/(?!zero)",
    r":\(\)\s*\{.*\|\s*:\s*\}",
    r"chmod\s+-R\s+777\s+/",
    r"curl\s+.*\|\s*sh",
    r"wget\s+.*\|\s*sh",
    r"sudo\s+rm",
    r"sudo\s+dd",
    r"fdisk",
    r"parted",
    r"mkfs",
    r"mke2fs",
    r"mkreiserfs",
    r"mnt",
    r"umount\s+/",
    r"init\s+[0-6]",
    r"systemctl\s+(poweroff|reboot|halt|suspend)",
    r"shutdown",
    r"poweroff",
    r"reboot",
    r"halt",
    r"pkill\s+-9",
    r"killall\s+-9",
    r"kill\s+-9\s+1",
]


class CommandExecutor:
    def __init__(self, allowed_dirs: list[str] | None = None, blocked_dirs: list[str] | None = None):
        self._allowed_dirs = [Path(d).resolve() for d in (allowed_dirs or [])]
        self._blocked_dirs = [Path(d).resolve() for d in (blocked_dirs or [])]

    def is_dangerous(self, command: str) -> tuple[bool, str]:
        for pattern in _DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True, f"Command matches dangerous pattern: {pattern}"
        return False, ""

    def validate_path(self, path: str | None, working_dir: str | None = None) -> tuple[bool, str]:
        if not path:
            return True, ""
        try:
            resolved = Path(path).resolve()
        except Exception as exc:
            return False, f"Invalid path: {exc}"

        if self._blocked_dirs:
            for blocked in self._blocked_dirs:
                if str(resolved).startswith(str(blocked)):
                    return False, f"Path blocked: {resolved}"

        if self._allowed_dirs:
            if not any(str(resolved).startswith(str(allowed)) for allowed in self._allowed_dirs):
                return False, f"Path outside allowed directories: {resolved}"

        return True, ""

    def redact_secrets(self, text: str) -> str:
        patterns = [
            (r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[=:]\s*\S+", r"\\1=[REDACTED]"),
            (r"(?i)bearer\s+\S+", "bearer [REDACTED]"),
            (r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]"),
            (r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{5,}", "[REDACTED]"),
            (r"sk-[A-Za-z0-9_-]{12,}", "[REDACTED]"),
            (r"AKIA[0-9A-Z]{16}", "[REDACTED]"),
        ]
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    async def execute(self, command: str, timeout: int = 300, working_dir: str | None = None, env: dict[str, str] | None = None) -> CommandResult:
        dangerous, reason = self.is_dangerous(command)
        if dangerous:
            raise PermissionError(f"Dangerous command blocked: {reason}")

        if working_dir:
            ok, reason = self.validate_path(working_dir)
            if not ok:
                raise PermissionError(reason)

        start = time.time()
        process_env = dict(os.environ)
        if env:
            for k, v in env.items():
                if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower() or "password" in k.lower():
                    process_env[k] = "[REDACTED]"
                else:
                    process_env[k] = v

        try:
            proc = await asyncio_create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=process_env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = time.time() - start
            stdout_text = self.redact_secrets(stdout.decode("utf-8", errors="replace"))
            stderr_text = self.redact_secrets(stderr.decode("utf-8", errors="replace"))
            return CommandResult(command, proc.returncode, stdout_text, stderr_text, duration)
        except asyncio.TimeoutError:
            with suppress(Exception):
                proc.kill()
            duration = time.time() - start
            return CommandResult(command, -1, "", f"Command timed out after {timeout}s", duration)
        except Exception as exc:
            duration = time.time() - start
            return CommandResult(command, -1, "", str(exc), duration)


def asyncio_create_subprocess_shell(cmd: str, **kwargs):
    import asyncio
    return asyncio.create_subprocess_shell(cmd, **kwargs)

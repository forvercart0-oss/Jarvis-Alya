"""Windows-specific computer control for JARVIS Phase 3."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger("jarvis.computer.windows")


def run_command(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return {"success": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def open_application(app: str) -> dict[str, Any]:
    return run_command(["start", app])


def type_text(text: str) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{text}')"])


def take_screenshot(path: str) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds | ForEach-Object {{ $bmp = New-Object System.Drawing.Bitmap($_.Width, $_.Height); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($_.Location, [System.Drawing.Point]::Empty, $_.Size); $bmp.Save('{path}') }}"])


def set_volume(level: int) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]174)"])

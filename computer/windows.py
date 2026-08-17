"""Windows-specific computer control for JARVIS Phase 10."""

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


def close_application(app: str) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Stop-Process -Name '{app}' -Force"])


def type_text(text: str) -> dict[str, Any]:
    safe = text.replace("'", "''")
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{safe}')"])


def keyboard_hotkey(keys: str) -> dict[str, Any]:
    safe = keys.replace("'", "''")
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{safe}')"])


def keyboard_press(key: str) -> dict[str, Any]:
    safe = key.replace("'", "''")
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{safe}')"])


def mouse_move(x: int, y: int) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})"])


def mouse_click(x: int, y: int, button: int = 1) -> dict[str, Any]:
    btn = "Left" if button == 1 else "Right" if button == 3 else "Middle"
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y}); [System.Windows.Forms.SendKeys]::SendWait('{btn[0]}')"])


def mouse_double_click(x: int, y: int) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y}); [System.Windows.Forms.SendKeys]::SendWait('{{L}}')"])


def mouse_right_click(x: int, y: int) -> dict[str, Any]:
    return mouse_click(x, y, 3)


def mouse_scroll(x: int, y: int, direction: str, amount: int = 3) -> dict[str, Any]:
    scroll_map = {"up": "{WHEELUP}", "down": "{WHEELDOWN}", "left": "{WHEELLEFT}", "right": "{WHEELRIGHT}"}
    key = scroll_map.get(direction, "{WHEELDOWN}")
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y}); [System.Windows.Forms.SendKeys]::SendWait('{key * amount}')"])


def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x1}, {y1}); [System.Windows.Forms.SendKeys]::SendWait(' '); [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x2}, {y2}); [System.Windows.Forms.SendKeys]::SendWait(' ')"])  # noqa: E501


def take_screenshot(path: str) -> dict[str, Any]:
    return run_command(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds | ForEach-Object {{ $bmp = New-Object System.Drawing.Bitmap($_.Width, $_.Height); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($_.Location, [System.Drawing.Point]::Empty, $_.Size); $bmp.Save('{path}') }}"])  # noqa: E501


def get_cursor_position() -> dict[str, Any]:
    return run_command(["powershell", "-Command", "[System.Windows.Forms.Cursor]::Position"])


def get_active_window() -> dict[str, Any]:
    return run_command(["powershell", "-Command", "(Get-Process | Where-Object {{ $_.MainWindowTitle -ne '' }} | Select-Object -First 1).MainWindowTitle"])


def list_windows() -> dict[str, Any]:
    result = run_command(["powershell", "-Command", "Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | Select-Object MainWindowTitle, Id | ConvertTo-Json"])
    if result.get("success"):
        return {"success": True, "windows": result["stdout"]}
    return result


def set_volume(level: int) -> dict[str, Any]:
    return run_command(["powershell", "-Command", "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]174)"])

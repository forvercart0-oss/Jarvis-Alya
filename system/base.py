"""Cross-platform system abstraction for JARVIS.

Each platform implements the same operations (power, audio, display, apps,
screenshots) so tools and services never branch on the OS directly. Use
:func:`system.get_platform` to obtain the active implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import shutil
import subprocess


def run(cmd, check=False, timeout=15, **kwargs):
    """Run a command and return the ``subprocess.CompletedProcess``."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=check, **kwargs)


def which(*names):
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


class SystemPlatform(ABC):
    """Abstract interface every OS backend must implement."""

    name = "unknown"

    # -------------------------------------------------------------- power
    @abstractmethod
    async def lock_screen(self) -> dict:
        """Lock the current session."""

    @abstractmethod
    async def shutdown(self) -> dict:
        """Power the machine off."""

    @abstractmethod
    async def reboot(self) -> dict:
        """Restart the machine."""

    @abstractmethod
    async def suspend(self) -> dict:
        """Suspend / sleep the machine."""

    # -------------------------------------------------------------- audio
    @abstractmethod
    async def set_volume(self, level: int) -> dict:
        """Set the default output volume to ``level`` percent (0-100)."""

    @abstractmethod
    async def set_mute(self, mute: bool) -> dict:
        """Mute or unmute the default output sink."""

    @abstractmethod
    async def audio_server_status(self) -> dict:
        """Report whether the audio server (pipewire/pulseaudio) is online."""

    # -------------------------------------------------------- applications
    @abstractmethod
    async def open_application(self, app_name: str) -> dict:
        """Launch a desktop application by name."""

    @abstractmethod
    async def close_application(self, app_name: str) -> dict:
        """Terminate a running desktop application by name."""

    # --------------------------------------------------------------- display
    @abstractmethod
    async def screenshot(self, out_path: str, region: str = "") -> dict:
        """Capture the screen to ``out_path``. Return status details."""

    @abstractmethod
    async def set_brightness(self, level: int) -> dict:
        """Set screen brightness to ``level`` percent (0-100)."""

    @abstractmethod
    async def set_do_not_disturb(self, enabled: bool) -> dict:
        """Enable or disable notification blocking."""

    # ------------------------------------------------------------- identity
    @abstractmethod
    def info(self) -> str:
        """Human-readable one-line platform summary."""

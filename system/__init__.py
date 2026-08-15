"""System platform factory.

Usage::

    from system import get_platform
    platform = get_platform()
    await platform.set_volume(40)
"""

from __future__ import annotations

import platform as _platform

from system.base import SystemPlatform  # noqa: F401


def get_platform() -> SystemPlatform:
    system = _platform.system().lower()
    if system == "windows":
        from system.windows import WindowsPlatform

        return WindowsPlatform()
    if system == "darwin":
        from system.macos import MacOSPlatform

        return MacOSPlatform()
    from system.linux import LinuxPlatform

    return LinuxPlatform()


_platform_instance: SystemPlatform | None = None


def platform_singleton() -> SystemPlatform:
    global _platform_instance
    if _platform_instance is None:
        _platform_instance = get_platform()
    return _platform_instance

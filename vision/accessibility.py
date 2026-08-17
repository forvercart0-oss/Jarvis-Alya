"""Accessibility integration for JARVIS Phase 24.

Uses native accessibility APIs where supported:
- Linux: AT-SPI where available
- Windows: UI Automation
- macOS: Accessibility APIs
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.accessibility")


@dataclass
class AccessibilityElement:
    role: str
    name: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    state: str = ""
    description: str = ""
    children: list[AccessibilityElement] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "state": self.state,
            "description": self.description,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
        }


class AccessibilityAdapter(ABC):
    @abstractmethod
    async def get_active_window(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_element_tree(self) -> list[AccessibilityElement]:
        raise NotImplementedError

    @abstractmethod
    async def find_element(self, role: str, name: str) -> AccessibilityElement | None:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        raise NotImplementedError


class LinuxATSPIAdapter(AccessibilityAdapter):
    async def get_active_window(self) -> dict[str, Any]:
        return {"success": False, "error": "AT-SPI not yet implemented"}

    async def get_element_tree(self) -> list[AccessibilityElement]:
        return []

    async def find_element(self, role: str, name: str) -> AccessibilityElement | None:
        return None

    async def health_check(self) -> dict[str, Any]:
        return {"status": "offline", "backend": "atspi", "error": "Not implemented"}


class WindowsUIAAdapter(AccessibilityAdapter):
    async def get_active_window(self) -> dict[str, Any]:
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            return {"success": True, "title": title}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def get_element_tree(self) -> list[AccessibilityElement]:
        return []

    async def find_element(self, role: str, name: str) -> AccessibilityElement | None:
        return None

    async def health_check(self) -> dict[str, Any]:
        try:
            import importlib.util
            spec = importlib.util.find_spec("win32gui")
            return {"status": "online" if spec else "offline", "backend": "uia"}
        except Exception as exc:
            return {"status": "offline", "backend": "uia", "error": str(exc)}


class MacOSAccessibilityAdapter(AccessibilityAdapter):
    async def get_active_window(self) -> dict[str, Any]:
        return {"success": False, "error": "macOS Accessibility not yet implemented"}

    async def get_element_tree(self) -> list[AccessibilityElement]:
        return []

    async def find_element(self, role: str, name: str) -> AccessibilityElement | None:
        return None

    async def health_check(self) -> dict[str, Any]:
        return {"status": "offline", "backend": "macos_accessibility", "error": "Not implemented"}


def get_accessibility_adapter() -> AccessibilityAdapter | None:
    import platform
    system = platform.system().lower()
    if system == "linux":
        return LinuxATSPIAdapter()
    if system == "windows":
        return WindowsUIAAdapter()
    if system == "darwin":
        return MacOSAccessibilityAdapter()
    return None


accessibility_adapter: AccessibilityAdapter | None = None


def get_adapter() -> AccessibilityAdapter | None:
    global accessibility_adapter
    if accessibility_adapter is None:
        accessibility_adapter = get_accessibility_adapter()
    return accessibility_adapter

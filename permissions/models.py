"""Permission definitions for JARVIS 2.0.

Phase 1 supported permissions (canonical dotted ids):

    filesystem.read        read files and directories
    filesystem.write       create, modify, delete files
    terminal.read          observe terminal output
    terminal.execute       execute terminal commands
    network.request        make network requests
    microphone             access the microphone
    camera                 access the camera
    clipboard.read         read the clipboard
    clipboard.write        write to the clipboard
    notifications          send notifications
    memory.read            read long-term memory
    memory.write           write to long-term memory

Phase 4 supported permissions (vision + computer control):

    vision.read_screen     observe screen content
    vision.capture         capture screenshots
    vision.analyze         send screen content to vision models
    computer.mouse         control mouse pointer
    computer.keyboard      control keyboard input
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDefinition:
    id: str
    label: str
    description: str
    risk: str


PERMISSION_DESCRIPTIONS: dict[str, PermissionDefinition] = {
    "filesystem.read": PermissionDefinition(
        "filesystem.read", "Read files", "Read files and directories on your system.", "low"
    ),
    "filesystem.write": PermissionDefinition(
        "filesystem.write",
        "Modify files",
        "Create, modify, or delete files on your system.",
        "high",
    ),
    "terminal.read": PermissionDefinition(
        "terminal.read", "Read terminal", "Observe terminal / shell output.", "low"
    ),
    "terminal.execute": PermissionDefinition(
        "terminal.execute",
        "Execute terminal commands",
        "Run shell commands on your system.",
        "high",
    ),
    "network.request": PermissionDefinition(
        "network.request", "Network access", "Make outbound network requests.", "medium"
    ),
    "microphone": PermissionDefinition(
        "microphone", "Microphone", "Access the microphone for voice input.", "high"
    ),
    "camera": PermissionDefinition(
        "camera", "Camera", "Access the camera for vision / gestures.", "high"
    ),
    "clipboard.read": PermissionDefinition(
        "clipboard.read", "Read clipboard", "Read the contents of the clipboard.", "medium"
    ),
    "clipboard.write": PermissionDefinition(
        "clipboard.write", "Write clipboard", "Write text to the clipboard.", "medium"
    ),
    "notifications": PermissionDefinition(
        "notifications", "Notifications", "Send desktop notifications.", "low"
    ),
    "memory.read": PermissionDefinition(
        "memory.read", "Read memory", "Read your long-term memories.", "medium"
    ),
    "memory.write": PermissionDefinition(
        "memory.write", "Write memory", "Store information in long-term memory.", "medium"
    ),
    "vision.read_screen": PermissionDefinition(
        "vision.read_screen", "Read screen", "Observe your screen content for analysis.", "high"
    ),
    "vision.capture": PermissionDefinition(
        "vision.capture", "Capture screen", "Capture screenshots of your screen.", "high"
    ),
    "vision.analyze": PermissionDefinition(
        "vision.analyze", "Analyze screen", "Send screen content to AI vision models.", "high"
    ),
    "computer.mouse": PermissionDefinition(
        "computer.mouse", "Mouse control", "Control the mouse pointer and clicks.", "high"
    ),
    "computer.keyboard": PermissionDefinition(
        "computer.keyboard", "Keyboard control", "Control keyboard input and typing.", "high"
    ),
}

ALL_PERMISSIONS: tuple[str, ...] = tuple(PERMISSION_DESCRIPTIONS)

# Legacy skill JSON permission keys -> canonical dotted permission ids.
# Kept for backward compatibility with skills authored against the old schema.
LEGACY_PERMISSION_MAP: dict[str, tuple[str, ...]] = {
    "filesystem_read": ("filesystem.read",),
    "filesystem_write": ("filesystem.write",),
    "terminal": ("terminal.read", "terminal.execute"),
    "terminal_read": ("terminal.read",),
    "terminal_execute": ("terminal.execute",),
    "network": ("network.request",),
    "microphone": ("microphone",),
    "camera": ("camera",),
    "clipboard_read": ("clipboard.read",),
    "clipboard_write": ("clipboard.write",),
    "notifications": ("notifications",),
    "memory_read": ("memory.read",),
    "memory_write": ("memory.write",),
    "vision_read_screen": ("vision.read_screen",),
    "vision_capture": ("vision.capture",),
    "vision_analyze": ("vision.analyze",),
    "computer_mouse": ("computer.mouse",),
    "computer_keyboard": ("computer.keyboard",),
}

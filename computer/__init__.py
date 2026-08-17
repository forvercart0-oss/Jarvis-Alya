"""Computer control module for JARVIS Phase 19."""

from __future__ import annotations

from computer.app_manager import ApplicationManager, app_manager
from computer.clipboard import ClipboardProvider, clipboard_provider
from computer.controller import ComputerController, computer_controller
from computer.file_manager import FileManager, file_manager
from computer.manager import ComputerManager, computer_manager
from computer.platform import CURRENT_PLATFORM, detect_platform
from computer.processes import ProcessManager, process_manager
from computer.provider import ComputerControlProvider, SystemComputerProvider, get_computer_provider
from computer.safety import ComputerSafety
from computer.session import ComputerSession, ComputerSessionManager, get_computer_session_manager
from computer.takeover import ComputerTakeover, computer_takeover
from computer.task_planner import ComputerTask, ComputerTaskPlanner, ComputerTaskState, computer_planner
from computer.terminal import TerminalProvider, terminal_provider
from computer.trust import ComputerPermissionManager, TrustLevel, computer_permission_manager
from computer.window_manager import WindowManager, window_manager

__all__ = [
    "CURRENT_PLATFORM",
    "ApplicationManager",
    "ClipboardProvider",
    "ComputerControlProvider",
    "ComputerController",
    "ComputerManager",
    "ComputerPermissionManager",
    "ComputerSafety",
    "ComputerSession",
    "ComputerSessionManager",
    "ComputerTakeover",
    "ComputerTask",
    "ComputerTaskPlanner",
    "ComputerTaskState",
    "FileManager",
    "ProcessManager",
    "SystemComputerProvider",
    "TerminalProvider",
    "TrustLevel",
    "WindowManager",
    "app_manager",
    "clipboard_provider",
    "computer_controller",
    "computer_manager",
    "computer_permission_manager",
    "computer_planner",
    "computer_takeover",
    "detect_platform",
    "file_manager",
    "get_computer_provider",
    "get_computer_session_manager",
    "process_manager",
    "terminal_provider",
    "window_manager",
]

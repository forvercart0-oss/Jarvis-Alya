"""Vision subsystem for JARVIS Phase 4.

Provides screen capture, OCR, UI element detection, visual targeting,
mouse/keyboard control, and vision analysis abstraction.
"""

from vision.capture import capture_screen, get_active_window, get_screen_info, list_monitors
from vision.manager import VisionManager
from vision.analyzer import analyze_image, describe_screen
from vision.detector import detect_elements, find_target
from vision.ocr import ocr_image, ocr_region
from vision.regions import select_region, parse_region
from vision.ocr import ocr_image, ocr_region, crop_region
from vision.actions import (
    mouse_move, mouse_click, mouse_double_click, mouse_right_click,
    mouse_drag, mouse_scroll, keyboard_type, keyboard_hotkey, keyboard_press,
)
from vision.permissions import (
    vision_read_screen, vision_capture, vision_analyze,
    computer_mouse, computer_keyboard,
)
from vision.providers.base import VisionProvider

__all__ = [
    "VisionManager",
    "capture_screen", "get_active_window", "get_screen_info", "list_monitors",
    "analyze_image", "describe_screen",
    "detect_elements", "find_target",
    "ocr_image", "ocr_region",
    "select_region", "parse_region", "crop_region",
    "mouse_move", "mouse_click", "mouse_double_click", "mouse_right_click",
    "mouse_drag", "mouse_scroll", "keyboard_type", "keyboard_hotkey", "keyboard_press",
    "vision_read_screen", "vision_capture", "vision_analyze",
    "computer_mouse", "computer_keyboard",
    "VisionProvider",
]

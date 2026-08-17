"""Vision subsystem for JARVIS Phase 17.

Provides screen capture, OCR, UI element detection, visual targeting,
mouse/keyboard control, image preprocessing, camera, comparison, and
vision analysis abstraction.
"""

from vision.camera import CameraManager
from vision.capture import capture_screen, get_active_window, get_screen_info, list_monitors
from vision.comparison import compare_images
from vision.image_utils import cleanup_temp_image, image_hash, preprocess_image, validate_image
from vision.manager import VisionManager
from vision.analyzer import analyze_image, describe_screen
from vision.detector import detect_elements, find_target
from vision.ocr import ocr_image, ocr_region
from vision.ocr_preprocessor import ocr_preprocessor
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
from vision.screen import ScreenCaptureProvider, SystemScreenCaptureProvider, get_screen_provider
from vision.visual_context import VisualContext
from vision.ui_detector import detect_ui_elements, classify_command
from vision.grounding import VisualGrounding, GroundedElement
from vision.question_answering import visual_qa
from vision.sensitive import sensitive_detector

__all__ = [
    "VisionManager",
    "CameraManager",
    "capture_screen", "get_active_window", "get_screen_info", "list_monitors",
    "analyze_image", "describe_screen",
    "detect_elements", "find_target", "detect_ui_elements",
    "ocr_image", "ocr_region",
    "select_region", "parse_region", "crop_region",
    "mouse_move", "mouse_click", "mouse_double_click", "mouse_right_click",
    "mouse_drag", "mouse_scroll", "keyboard_type", "keyboard_hotkey", "keyboard_press",
    "vision_read_screen", "vision_capture", "vision_analyze",
    "computer_mouse", "computer_keyboard",
    "VisionProvider",
    "validate_image", "preprocess_image", "cleanup_temp_image", "image_hash",
    "compare_images",
    "ocr_preprocessor",
    "ScreenCaptureProvider", "SystemScreenCaptureProvider", "get_screen_provider",
    "VisualContext",
    "VisualGrounding", "GroundedElement",
    "visual_qa",
    "sensitive_detector",
    "classify_command",
]

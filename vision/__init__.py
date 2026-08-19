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
from vision.ocr import ocr_image, ocr_region, crop_region
from vision.ocr_preprocessor import ocr_preprocessor
from vision.regions import select_region, parse_region
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
from vision.screen_understanding import screen_understanding_engine, ScreenUnderstandingEngine
from vision.action_planner import visual_action_planner, VisualActionPlanner, ActionPlan, PlannedAction
from vision.screen_query import screen_query_engine, ScreenQueryEngine
from vision.screen_diff import screen_diff_engine, ScreenDiffEngine, ScreenDiff
from vision.wait_for_element import wait_for_element, smart_wait, WaitForElement, SmartWait
from vision.accessibility import get_adapter, AccessibilityAdapter, AccessibilityElement
from vision.action_verification import action_verifier, ActionVerifier
from vision.action_log import action_logger, ActionLogger, ActionLogEntry
from vision.screen_intelligence import screen_intelligence, ScreenIntelligenceOrchestrator, ScreenIntelligenceMode
from vision.ocr_providers import ocr_manager, OCRProviderManager, OCRProvider, OCRResult, OCRTextRegion
from vision.application_understanding import application_understanding, ApplicationUnderstanding
from vision.dialog_detection import dialog_detector, DialogDetector, DialogDetectionResult
from vision.workflow_recorder import workflow_recorder, WorkflowRecorder, RecordedWorkflow, RecordedStep
from vision.workflow_replay import workflow_replayer, WorkflowReplayer
from vision.visual_skills import visual_skill_manager, VisualSkillManager, VisualSkill
from vision.gesture import GestureController, GestureDetector, get_gesture, GESTURES

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
    "ScreenUnderstandingEngine", "screen_understanding_engine", "ScreenUnderstanding",
    "VisualActionPlanner", "visual_action_planner", "ActionPlan", "PlannedAction",
    "ScreenQueryEngine", "screen_query_engine",
    "ScreenDiffEngine", "screen_diff_engine", "ScreenDiff",
    "WaitForElement", "SmartWait", "wait_for_element", "smart_wait",
    "AccessibilityAdapter", "AccessibilityElement", "get_adapter",
    "ActionVerifier", "action_verifier",
    "ActionLogger", "action_logger", "ActionLogEntry",
    "ScreenIntelligenceOrchestrator", "screen_intelligence", "ScreenIntelligenceMode",
    "OCRProvider", "OCRProviderManager", "ocr_manager", "OCRResult", "OCRTextRegion",
    "application_understanding", "ApplicationUnderstanding",
    "dialog_detector", "DialogDetector", "DialogDetectionResult",
    "workflow_recorder", "WorkflowRecorder", "RecordedWorkflow", "RecordedStep",
    "workflow_replayer", "WorkflowReplayer",
    "visual_skill_manager", "VisualSkillManager", "VisualSkill",
    "GestureController", "GestureDetector", "get_gesture", "GESTURES",
]

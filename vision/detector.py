"""UI element detection for JARVIS Phase 4."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.detector")


async def detect_elements(image_path: str) -> dict[str, Any]:
    """Detect UI elements in an image."""
    from vision.manager import vision_manager
    provider = vision_manager.get_provider()
    if provider is None:
        return {"success": False, "error": "No vision provider configured."}
    result = await provider.detect_elements(image_path)
    return {
        "success": result.success,
        "elements": result.elements,
        "error": result.error,
        "metadata": result.metadata,
    }


async def find_target(image_path: str, target: str) -> dict[str, Any]:
    """Find a specific UI target by name/description."""
    from vision.manager import vision_manager
    provider = vision_manager.get_provider()
    if provider is None:
        return {"success": False, "error": "No vision provider configured."}
    result = await provider.find_target(image_path, target)
    return {
        "found": result.success and result.confidence >= vision_manager.confidence_threshold,
        "target": target,
        "x": result.metadata.get("x", 0),
        "y": result.metadata.get("y", 0),
        "width": result.metadata.get("width", 0),
        "height": result.metadata.get("height", 0),
        "confidence": result.confidence,
        "description": result.description,
        "error": result.error,
    }

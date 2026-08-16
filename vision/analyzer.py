"""Vision analysis utilities for JARVIS Phase 4."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.analyzer")


async def analyze_image(image_path: str, prompt: str = "") -> dict[str, Any]:
    """Analyze an image using the configured vision provider."""
    from vision.manager import vision_manager
    provider = vision_manager.get_provider()
    if provider is None:
        return {"success": False, "error": "No vision provider configured."}
    result = await provider.analyze_image(image_path, prompt)
    return {
        "success": result.success,
        "description": result.description,
        "text": result.text,
        "elements": result.elements,
        "confidence": result.confidence,
        "error": result.error,
        "metadata": result.metadata,
    }


async def describe_screen(image_path: str) -> dict[str, Any]:
    """Get a high-level description of the screen."""
    from vision.manager import vision_manager
    provider = vision_manager.get_provider()
    if provider is None:
        return {"success": False, "error": "No vision provider configured."}
    result = await provider.describe_screen(image_path)
    return {
        "success": result.success,
        "description": result.description,
        "error": result.error,
        "metadata": result.metadata,
    }

"""Image comparison utilities for JARVIS Phase 14."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.comparison")


async def compare_images(image_a: str, image_b: str) -> dict[str, Any]:
    try:
        from PIL import Image
        img_a = Image.open(image_a)
        img_b = Image.open(image_b)
        if img_a.size != img_b.size:
            return {
                "success": True,
                "identical": False,
                "difference": "Image dimensions differ",
                "details": {
                    "size_a": img_a.size,
                    "size_b": img_b.size,
                },
            }
        diff = Image.new("RGB", img_a.size, (255, 0, 0))
        for x in range(img_a.width):
            for y in range(img_a.height):
                if img_a.getpixel((x, y)) != img_b.getpixel((x, y)):
                    diff.putpixel((x, y), (255, 0, 0))
        return {
            "success": True,
            "identical": False,
            "difference": "Pixel differences detected",
            "details": {
                "size": img_a.size,
            },
        }
    except ImportError:
        return {"success": False, "error": "Pillow not available for image comparison."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

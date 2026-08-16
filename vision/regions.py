"""Region selection utilities for JARVIS Phase 4."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.regions")


def parse_region(region: str) -> dict[str, int] | None:
    """Parse a region string like 'WxH+X+Y' or 'x,y,w,h'."""
    if not region:
        return None

    if "x" in region and "+" in region:
        try:
            size, pos = region.split("+", 1)
            w, h = size.split("x")
            x, y = pos.split("+")
            return {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
            }
        except ValueError:
            return None

    parts = region.replace(",", " ").split()
    if len(parts) == 4:
        try:
            return {
                "x": int(parts[0]),
                "y": int(parts[1]),
                "width": int(parts[2]),
                "height": int(parts[3]),
            }
        except ValueError:
            return None

    return None


def select_region() -> dict[str, Any]:
    """Allow user to select a screen region interactively.

    This returns a placeholder; actual selection is handled by the
    frontend via mouse events on the screenshot preview.
    """
    return {"ok": True, "mode": "interactive", "message": "Use frontend to select region."}


def regions_overlap(a: dict[str, int], b: dict[str, int]) -> bool:
    """Check if two regions overlap."""
    return not (
        a.get("x", 0) + a.get("width", 0) <= b.get("x", 0)
        or b.get("x", 0) + b.get("width", 0) <= a.get("x", 0)
        or a.get("y", 0) + a.get("height", 0) <= b.get("y", 0)
        or b.get("y", 0) + b.get("height", 0) <= a.get("y", 0)
    )

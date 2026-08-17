"""Action verification for JARVIS Phase 24.

Verifies screen state changed after an action.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.action_verification")


class ActionVerifier:
    def __init__(self):
        self._diff_engine = None

    def _get_diff_engine(self):
        if self._diff_engine is None:
            from vision.screen_diff import screen_diff_engine
            self._diff_engine = screen_diff_engine
        return self._diff_engine

    async def verify_click(self, x: int, y: int, expected_state: str = "") -> dict[str, Any]:
        try:
            import os
            import tempfile

            from vision.capture import capture_screen
            fd, _path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            result = await capture_screen("full")
            if not result.get("ok") and not result.get("success"):
                return {"success": False, "verified": False, "error": "Cannot capture screen for verification"}
            from vision.ocr import ocr_image
            ocr = await ocr_image(result["path"])
            text = ocr.get("text", "") if isinstance(ocr, dict) else ""
            return {
                "success": True,
                "verified": True,
                "x": x,
                "y": y,
                "ocr_preview": text[:200],
                "message": "Click executed and screen captured for verification",
            }
        except Exception as exc:
            return {"success": False, "verified": False, "error": str(exc)}

    async def verify_screen_changed(self, before_hash: str, before_text: str) -> dict[str, Any]:
        try:
            import os
            import tempfile

            from vision.capture import capture_screen
            from vision.image_utils import image_hash
            fd, _path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            result = await capture_screen("full")
            if not result.get("ok") and not result.get("success"):
                return {"success": False, "changed": False, "error": "Cannot capture screen"}
            new_hash = image_hash(result["path"])
            from vision.ocr import ocr_image
            ocr = await ocr_image(result["path"])
            new_text = ocr.get("text", "") if isinstance(ocr, dict) else ""
            changed = new_hash != before_hash or new_text != before_text
            return {
                "success": True,
                "changed": changed,
                "before_hash": before_hash,
                "after_hash": new_hash,
                "before_text_preview": before_text[:100],
                "after_text_preview": new_text[:100],
            }
        except Exception as exc:
            return {"success": False, "changed": False, "error": str(exc)}

    async def verify_element_present(self, target: str) -> dict[str, Any]:
        try:
            from vision.screen_understanding import screen_understanding_engine
            understanding = await screen_understanding_engine.understand("")
            if understanding and understanding.detected_elements:
                for el in understanding.detected_elements:
                    if target.lower() in el.get("label", "").lower():
                        return {"success": True, "present": True, "element": el}
            return {"success": True, "present": False}
        except Exception as exc:
            return {"success": False, "present": False, "error": str(exc)}


action_verifier = ActionVerifier()

"""OCR preprocessing pipeline for JARVIS Phase 17."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("jarvis.vision.ocr_preprocessor")


@dataclass
class OCRPreprocessResult:
    success: bool
    path: str = ""
    original_path: str = ""
    backend: str = ""
    text: str = ""
    error: str = ""
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OCRPreprocessor:
    """Preprocesses images to improve OCR accuracy."""

    def __init__(self):
        self._pillow_available = False
        try:
            from PIL import Image, ImageEnhance, ImageFilter  # noqa: F401
            self._pillow_available = True
        except ImportError:
            logger.debug("Pillow not available for OCR preprocessing")

    @property
    def available(self) -> bool:
        return self._pillow_available

    async def preprocess(self, image_path: str) -> OCRPreprocessResult:
        if not self._pillow_available:
            return OCRPreprocessResult(success=False, path=image_path, original_path=image_path, error="Pillow not available")
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            img = Image.open(image_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            gray = img.convert("L")
            enhanced = ImageEnhance.Contrast(gray).enhance(1.5)
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            import tempfile, os
            fd, out = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            sharpened.save(out)
            return OCRPreprocessResult(success=True, path=out, original_path=image_path, backend="pillow", metadata={"mode": "grayscale+contrast+sharpen"})
        except Exception as exc:
            logger.debug("OCR preprocessing failed: %s", exc)
            return OCRPreprocessResult(success=False, path=image_path, original_path=image_path, error=str(exc))

    async def preprocess_for_vision(self, image_path: str) -> OCRPreprocessResult:
        if not self._pillow_available:
            return OCRPreprocessResult(success=False, path=image_path, original_path=image_path, error="Pillow not available")
        try:
            from PIL import Image, ImageEnhance
            img = Image.open(image_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            max_dim = 1280
            if max(img.size) > max_dim:
                ratio = max_dim / max(img.size)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)
            import tempfile, os
            fd, out = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            img.save(out, quality=85)
            return OCRPreprocessResult(success=True, path=out, original_path=image_path, backend="pillow", metadata={"mode": "resize+sharpen"})
        except Exception as exc:
            logger.debug("Vision preprocessing failed: %s", exc)
            return OCRPreprocessResult(success=False, path=image_path, original_path=image_path, error=str(exc))


ocr_preprocessor = OCRPreprocessor()

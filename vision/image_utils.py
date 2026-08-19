"""Image preprocessing utilities for JARVIS Phase 14."""

from __future__ import annotations

import hashlib
import logging
import re
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.vision.image_utils")


class ImageValidationError(Exception):
    pass


_SECRET_PATTERNS = [
    re.compile(r"[A-Za-z0-9]{32,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{35}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
    re.compile(r"(?i)api[_-]?key\s*[:=]"),
    re.compile(r"(?i)password\s*[:=]"),
    re.compile(r"(?i)secret\s*[:=]"),
    re.compile(r"(?i)token\s*[:=]"),
]


def validate_image(image_path: str, max_size_mb: float = 20.0, allowed_extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp")) -> dict[str, Any]:
    path = Path(image_path)
    if not path.exists():
        raise ImageValidationError(f"Image not found: {image_path}")
    if path.suffix.lower() not in allowed_extensions:
        raise ImageValidationError(f"Unsupported image format: {path.suffix}")
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ImageValidationError(f"Image too large: {size_mb:.1f}MB (max {max_size_mb}MB)")
    return {
        "valid": True,
        "path": str(path),
        "size_bytes": size_bytes,
        "size_mb": round(size_mb, 2),
        "extension": path.suffix.lower(),
    }


def preprocess_image(image_path: str, max_width: int = 1920, max_height: int = 1080, quality: int = 85) -> dict[str, Any]:
    try:
        from PIL import Image
        img = Image.open(image_path)
        original_width, original_height = img.size
        if original_width > max_width or original_height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        if image_path.lower().endswith((".jpg", ".jpeg")):
            img.save(image_path, "JPEG", quality=quality, optimize=True)
        elif image_path.lower().endswith(".webp"):
            img.save(image_path, "WEBP", quality=quality)
        else:
            img.save(image_path, "PNG", optimize=True)
        result = validate_image(image_path)
        result["resized"] = original_width != img.width or original_height != img.height
        result["width"] = img.width
        result["height"] = img.height
        return result
    except ImportError:
        logger.debug("Pillow not available, skipping preprocessing")
        return validate_image(image_path)
    except Exception as exc:
        logger.warning("Image preprocessing failed: %s", exc)
        return validate_image(image_path)


def redact_secrets_in_image(image_path: str) -> str:
    return image_path


def detect_secrets_in_text(text: str) -> list[dict[str, Any]]:
    if not text:
        return []
    findings: list[dict[str, Any]] = []
    for pattern in _SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({
                "pattern": pattern.pattern,
                "match": match.group(0)[:20] + "...",
                "start": match.start(),
                "end": match.end(),
            })
    return findings


def image_hash(image_path: str) -> str:
    hasher = hashlib.sha256()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def cleanup_temp_image(image_path: str) -> None:
    try:
        path = Path(image_path)
        if path.exists() and path.parent.name == tempfile.gettempdir():
            path.unlink()
    except Exception:
        pass

"""OCR utilities for JARVIS Phase 4."""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger("jarvis.vision.ocr")


async def ocr_image(image_path: str) -> dict[str, Any]:
    """Run OCR on an image and return recognized text."""
    system = os.environ.get("OS", "linux").lower()

    if system == "windows":
        return await _ocr_windows(image_path)
    if system == "darwin":
        return await _ocr_macos(image_path)
    return await _ocr_linux(image_path)


async def _ocr_linux(image_path: str) -> dict[str, Any]:
    if _has_cmd("tesseract"):
        result = await _run(["tesseract", image_path, "stdout", "--psm", "6"])
        if result.get("success"):
            return {"text": result["stdout"].strip(), "backend": "tesseract"}
        return {"success": False, "error": result.get("error", "tesseract failed")}

    if _has_cmd("ocrmypdf"):
        return {"success": False, "error": "ocrmypdf not suitable for single image OCR"}

    return {"success": False, "error": "No OCR tool available (tesseract)."}


async def _ocr_windows(image_path: str) -> dict[str, Any]:
    if _has_cmd("tesseract"):
        result = await _run(["tesseract", image_path, "stdout", "--psm", "6"])
        if result.get("success"):
            return {"text": result["stdout"].strip(), "backend": "tesseract"}
        return {"success": False, "error": result.get("error", "tesseract failed")}
    return {"success": False, "error": "No OCR tool available on Windows."}


async def _ocr_macos(image_path: str) -> dict[str, Any]:
    if _has_cmd("tesseract"):
        result = await _run(["tesseract", image_path, "stdout", "--psm", "6"])
        if result.get("success"):
            return {"text": result["stdout"].strip(), "backend": "tesseract"}
        return {"success": False, "error": result.get("error", "tesseract failed")}
    return {"success": False, "error": "No OCR tool available on macOS."}


async def ocr_region(image_path: str, region: dict[str, int]) -> dict[str, Any]:
    """OCR a specific region of an image by cropping first."""
    cropped = crop_region(image_path, region)
    if not cropped.get("ok"):
        return cropped
    return await ocr_image(cropped["path"])


def _has_cmd(cmd: str) -> bool:
    return any(
        os.path.isfile(os.path.join(p, cmd))
        for p in os.environ.get("PATH", "").split(os.pathsep)
        if p
    )


async def _run(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    import asyncio
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {"success": False, "error": "Command timed out"}
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "code": proc.returncode,
        }
    except FileNotFoundError:
        return {"success": False, "error": f"Command not found: {cmd[0]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def crop_region(image_path: str, region: dict[str, int]) -> dict[str, Any]:
    """Crop a region from an image."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        x = region.get("x", 0)
        y = region.get("y", 0)
        w = region.get("width", img.width - x)
        h = region.get("height", img.height - y)
        cropped = img.crop((x, y, x + w, y + h))
        fd, out = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        cropped.save(out)
        return {"ok": True, "path": out, "width": w, "height": h}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

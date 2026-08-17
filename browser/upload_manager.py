"""Upload manager for JARVIS Phase 25.

Supports file uploads with safety checks.
Never uploads arbitrary sensitive files without user intent.
"""

from __future__ import annotations

import logging
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.browser.upload_manager")


@dataclass
class UploadTask:
    file_path: str = ""
    filename: str = ""
    mime_type: str = ""
    size: int = 0
    selector: str = ""
    status: str = "pending"
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size": self.size,
            "selector": self.selector,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }


class BrowserUploadManager:
    SENSITIVE_EXTENSIONS = {".key", ".pem", ".p12", ".pfx", ".env", ".secret", ".priv"}
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024

    def validate_file(self, file_path: str) -> UploadTask:
        path = Path(file_path)
        if not path.exists():
            return UploadTask(file_path=file_path, status="error", error="File not found")
        if not path.is_file():
            return UploadTask(file_path=file_path, status="error", error="Not a regular file")
        if path.suffix.lower() in self.SENSITIVE_EXTENSIONS:
            return UploadTask(file_path=file_path, status="error", error="Sensitive file type blocked")
        size = path.stat().st_size
        if size > self.MAX_UPLOAD_SIZE:
            return UploadTask(file_path=file_path, status="error", error="File too large for upload")
        mime_type, _ = mimetypes.guess_type(str(path))
        return UploadTask(
            file_path=str(path),
            filename=path.name,
            mime_type=mime_type or "application/octet-stream",
            size=size,
            status="validated",
        )

    async def upload(self, page: Any, selector: str, file_path: str) -> dict[str, Any]:
        validation = self.validate_file(file_path)
        if validation.status == "error":
            return {"success": False, "error": validation.error}
        try:
            if hasattr(page, "set_input_files"):
                await page.set_input_files(selector, file_path)
                validation.status = "complete"
                validation.selector = selector
                return {"success": True, "filename": validation.filename, "path": file_path}
            return {"success": False, "error": "Upload not supported by this browser backend"}
        except Exception as exc:
            validation.status = "error"
            validation.error = str(exc)
            return {"success": False, "error": str(exc)}


browser_upload_manager = BrowserUploadManager()

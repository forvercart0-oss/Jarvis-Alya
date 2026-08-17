"""Clipboard provider for JARVIS Phase 19."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.computer.clipboard")


class ClipboardProvider:
    def read(self) -> dict[str, Any]:
        try:
            import pyperclip
            content = pyperclip.paste()
            return {"success": True, "content": content}
        except ImportError:
            return {"success": False, "error": "pyperclip not available"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def write(self, text: str) -> dict[str, Any]:
        try:
            import pyperclip
            pyperclip.copy(text)
            return {"success": True}
        except ImportError:
            return {"success": False, "error": "pyperclip not available"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def clear(self) -> dict[str, Any]:
        try:
            import pyperclip
            pyperclip.copy("")
            return {"success": True}
        except ImportError:
            return {"success": False, "error": "pyperclip not available"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


clipboard_provider = ClipboardProvider()

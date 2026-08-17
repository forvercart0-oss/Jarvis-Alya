"""Browser permissions for JARVIS Phase 18."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.browser.permissions")

_BROWSER_PERMISSIONS = {
    "READ_PAGE": {"trusted": True, "description": "Read page content"},
    "NAVIGATE": {"trusted": True, "description": "Navigate to URLs"},
    "CLICK": {"trusted": True, "description": "Click elements"},
    "TYPE": {"trusted": True, "description": "Type text"},
    "SCROLL": {"trusted": True, "description": "Scroll pages"},
    "UPLOAD": {"trusted": False, "description": "Upload files"},
    "DOWNLOAD": {"trusted": False, "description": "Download files"},
    "SEND_MESSAGE": {"trusted": False, "description": "Send messages"},
    "POST": {"trusted": False, "description": "Post content"},
    "DELETE": {"trusted": False, "description": "Delete content"},
    "PURCHASE": {"trusted": False, "description": "Make purchases"},
    "ACCOUNT_CHANGE": {"trusted": False, "description": "Change account settings"},
}


class BrowserPermissionManager:
    def is_allowed(self, action: str) -> bool:
        perm = _BROWSER_PERMISSIONS.get(action.upper())
        if perm:
            return perm["trusted"]
        return True

    def requires_confirmation(self, action: str) -> bool:
        perm = _BROWSER_PERMISSIONS.get(action.upper())
        if perm:
            return not perm["trusted"]
        return False

    def list_permissions(self) -> dict[str, dict[str, Any]]:
        return dict(_BROWSER_PERMISSIONS)


browser_permission_manager = BrowserPermissionManager()

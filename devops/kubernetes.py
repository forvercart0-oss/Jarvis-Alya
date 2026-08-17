"""Kubernetes support for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.kubernetes")


class KubernetesManager:
    def __init__(self):
        self._available = False
        try:
            import shutil
            self._available = shutil.which("kubectl") is not None
        except Exception:
            pass

    @property
    def available(self) -> bool:
        return self._available

    def get_pods(self, namespace: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "kubectl not available"}
        try:
            import subprocess
            result = subprocess.run(["kubectl", "get", "pods", "-n", namespace, "-o", "json"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr[-500:]}
            return {"success": True, "pods": result.stdout[-2000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_services(self, namespace: str = "default") -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "kubectl not available"}
        try:
            import subprocess
            result = subprocess.run(["kubectl", "get", "services", "-n", namespace, "-o", "json"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr[-500:]}
            return {"success": True, "services": result.stdout[-2000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_logs(self, pod: str, namespace: str = "default", tail: int = 100) -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "kubectl not available"}
        try:
            import subprocess
            result = subprocess.run(["kubectl", "logs", pod, "-n", namespace, "--tail", str(tail)], capture_output=True, text=True, check=False)
            return {"success": result.returncode == 0, "logs": result.stdout[-4000:] + result.stderr[-1000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


kubernetes_manager = KubernetesManager()

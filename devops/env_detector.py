"""Environment detector for JARVIS Phase 28."""

from __future__ import annotations

import logging
import platform
import shutil
from typing import Any

logger = logging.getLogger("jarvis.devops.env_detector")


class EnvironmentDetector:
    def detect(self) -> dict[str, Any]:
        tools = {
            "docker": shutil.which("docker"),
            "podman": shutil.which("podman"),
            "kubectl": shutil.which("kubectl"),
            "helm": shutil.which("helm"),
            "terraform": shutil.which("terraform"),
            "ansible": shutil.which("ansible"),
            "npm": shutil.which("npm"),
            "node": shutil.which("node"),
            "python": shutil.which("python"),
            "pip": shutil.which("pip"),
            "git": shutil.which("git"),
            "ssh": shutil.which("ssh"),
            "systemctl": shutil.which("systemctl"),
            "aws": shutil.which("aws"),
            "gcloud": shutil.which("gcloud"),
            "az": shutil.which("az"),
        }
        available = {k: v for k, v in tools.items() if v}
        return {
            "os": platform.system(),
            "arch": platform.machine(),
            "shell": "unknown",
            "tools": available,
            "docker_available": "docker" in available,
            "kubernetes_available": "kubectl" in available,
        }


environment_detector = EnvironmentDetector()

"""Container registry and image publishing for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.registry")


class ContainerRegistry:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    async def push(self, image: str, tag: str) -> dict[str, Any]:
        return {"success": False, "error": f"Registry {self.name} push not configured"}

    async def pull(self, image: str, tag: str) -> dict[str, Any]:
        return {"success": False, "error": f"Registry {self.name} pull not configured"}


class RegistryManager:
    def __init__(self):
        self._registries: dict[str, ContainerRegistry] = {}

    def register(self, registry: ContainerRegistry) -> None:
        self._registries[registry.name] = registry

    def get(self, name: str) -> ContainerRegistry | None:
        return self._registries.get(name)

    def detect_configured(self) -> list[str]:
        import shutil
        available = []
        if shutil.which("docker"):
            available.append("docker")
        if shutil.which("buildah"):
            available.append("buildah")
        return available

    def build_tag_push(self, project_path: str, image: str, tag: str) -> dict[str, Any]:
        try:
            import subprocess
            build = subprocess.run(["docker", "build", "-t", f"{image}:{tag}", project_path], capture_output=True, text=True, check=False)
            if build.returncode != 0:
                return {"success": False, "error": build.stderr[-500:]}
            tag_cmd = ["docker", "tag", f"{image}:{tag}", f"{image}:{tag}"]
            subprocess.run(tag_cmd, capture_output=True, text=True, check=False)
            push = subprocess.run(["docker", "push", f"{image}:{tag}"], capture_output=True, text=True, check=False)
            return {"success": push.returncode == 0, "stdout": push.stdout[-1000:], "stderr": push.stderr[-500:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


registry_manager = RegistryManager()

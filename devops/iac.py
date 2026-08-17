"""Terraform and Ansible support for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.iac")


class TerraformManager:
    def __init__(self):
        self._available = False
        try:
            import shutil
            self._available = shutil.which("terraform") is not None
        except Exception:
            pass

    @property
    def available(self) -> bool:
        return self._available

    def validate(self, path: str) -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "terraform not available"}
        try:
            import subprocess
            result = subprocess.run(["terraform", "init", "-backend=false"], cwd=path, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr[-500:]}
            result2 = subprocess.run(["terraform", "validate"], cwd=path, capture_output=True, text=True, check=False)
            return {"success": result2.returncode == 0, "stdout": result2.stdout[-1000:], "stderr": result2.stderr[-500:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def plan(self, path: str) -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "terraform not available"}
        try:
            import subprocess
            result = subprocess.run(["terraform", "plan", "-input=false"], cwd=path, capture_output=True, text=True, check=False)
            return {"success": result.returncode == 0, "stdout": result.stdout[-2000:], "stderr": result.stderr[-1000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


class AnsibleManager:
    def __init__(self):
        self._available = False
        try:
            import shutil
            self._available = shutil.which("ansible") is not None
        except Exception:
            pass

    @property
    def available(self) -> bool:
        return self._available

    def validate_playbook(self, path: str) -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "ansible not available"}
        try:
            import subprocess
            result = subprocess.run(["ansible-playbook", "--syntax-check", path], capture_output=True, text=True, check=False)
            return {"success": result.returncode == 0, "stdout": result.stdout[-1000:], "stderr": result.stderr[-500:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def list_inventory(self, path: str) -> dict[str, Any]:
        if not self._available:
            return {"success": False, "error": "ansible not available"}
        try:
            import subprocess
            result = subprocess.run(["ansible-inventory", "--list", "-i", path], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr[-500:]}
            return {"success": True, "inventory": result.stdout[-2000:]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


terraform_manager = TerraformManager()
ansible_manager = AnsibleManager()

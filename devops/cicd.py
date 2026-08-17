"""CI/CD manager for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.cicd")


class CICDManager:
    def __init__(self):
        self._github_available = False
        self._gitlab_available = False
        try:
            import shutil
            self._github_available = shutil.which("gh") is not None
            self._gitlab_available = shutil.which("glab") is not None
        except Exception:
            logger.debug("CI tool detection failed")

    def detect_system(self, project_path: str) -> str:
        path = __import__("pathlib").Path(project_path)
        if (path / ".github" / "workflows").exists():
            return "github_actions"
        if (path / ".gitlab-ci.yml").exists():
            return "gitlab_ci"
        if (path / "Jenkinsfile").exists():
            return "jenkins"
        return "none"

    def generate_github_workflow(self, project: dict[str, Any]) -> str:
        return """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: pytest
"""

    def generate_gitlab_ci(self, project: dict[str, Any]) -> str:
        return """stages:
  - test
  - build
test:
  stage: test
  script:
    - pytest
"""


cicd_manager = CICDManager()

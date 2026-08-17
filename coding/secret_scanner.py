"""Secret scanner for JARVIS Phase 27."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.coding.secret_scanner")


class SecretScanner:
    def __init__(self):
        self._patterns = [
            re.compile(r"api[_-]?key[\"':= ]+([a-zA-Z0-9_\-]{20,})", re.IGNORECASE),
            re.compile(r"token[\"':= ]+([a-zA-Z0-9_\-]{20,})", re.IGNORECASE),
            re.compile(r"password[\"':= ]+([^\s\"']+)", re.IGNORECASE),
            re.compile(r"secret[\"':= ]+([^\s\"']+)", re.IGNORECASE),
            re.compile(r"private[_-]?key[\"':= ]+([a-zA-Z0-9_\-]{20,})", re.IGNORECASE),
            re.compile(r"aws[_-]?access[_-]?key[_-]?id[\"':= ]+([a-zA-Z0-9]{20})", re.IGNORECASE),
            re.compile(r"aws[_-]?secret[_-]?access[_-]?key[\"':= ]+([a-zA-Z0-9/+=]{40})", re.IGNORECASE),
            re.compile(r"Bearer [a-zA-Z0-9_\-\.]+"),
        ]

    def scan_file(self, path: Path) -> list[dict[str, Any]]:
        findings = []
        try:
            content = path.read_text(errors="ignore")
            for pattern in self._patterns:
                for match in pattern.finditer(content):
                    findings.append({
                        "pattern": pattern.pattern[:50],
                        "match": match.group(0)[:80],
                        "line": content[:match.start()].count("\n") + 1,
                    })
        except Exception:
            pass
        return findings

    def scan_directory(self, path: Path) -> list[dict[str, Any]]:
        findings = []
        if not path.exists():
            return findings
        for f in path.rglob("*"):
            if f.is_file() and not f.name.startswith(".") and f.suffix in (".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env", ".txt"):
                file_findings = self.scan_file(f)
                for finding in file_findings:
                    finding["file"] = str(f.relative_to(path))
                    findings.append(finding)
        return findings

    def scan_before_git(self, project: str, changed_files: list[str]) -> dict[str, Any]:
        findings = []
        for rel in changed_files:
            path = Path(project) / rel
            if path.exists():
                findings.extend(self.scan_file(path))
        return {"success": True, "findings": findings, "count": len(findings)}


secret_scanner = SecretScanner()

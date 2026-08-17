"""Project index for JARVIS Phase 27."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.coding.project_index")


class ProjectIndex:
    def __init__(self, project_path: Path):
        self._path = project_path
        self._files: dict[str, dict[str, Any]] = {}
        self._symbols: dict[str, list[dict[str, Any]]] = {}
        self._dependencies: dict[str, list[str]] = {}

    def build(self) -> None:
        self._files.clear()
        self._symbols.clear()
        self._dependencies.clear()
        if not self._path.exists():
            return
        for f in self._path.rglob("*"):
            if f.is_file() and not f.name.startswith(".") and f.suffix in (
                ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".html", ".css", ".scss", ".sql"
            ):
                rel = str(f.relative_to(self._path))
                try:
                    content = f.read_text(errors="ignore")
                    self._files[rel] = {
                        "path": rel,
                        "size": len(content),
                        "extension": f.suffix,
                        "lines": content.count("\n"),
                    }
                    self._extract_symbols(rel, content)
                    self._extract_dependencies(rel, content)
                except Exception:
                    continue

    def _extract_symbols(self, path: str, content: str) -> None:
        symbols = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("function ") or stripped.startswith("const ") or stripped.startswith("let ") or stripped.startswith("var "):
                symbols.append({"line": i, "text": stripped[:120], "type": "definition"})
            elif "import " in stripped or "require(" in stripped:
                symbols.append({"line": i, "text": stripped[:120], "type": "import"})
        if symbols:
            self._symbols[path] = symbols[:50]

    def _extract_dependencies(self, path: str, content: str) -> None:
        deps = []
        if path == "package.json":
            try:
                import json
                pkg = json.loads(content)
                deps = list(pkg.get("dependencies", {}).keys()) + list(pkg.get("devDependencies", {}).keys())
            except Exception:
                pass
        elif path == "requirements.txt":
            deps = [line.strip().split("==")[0] for line in content.splitlines() if line.strip() and not line.startswith("#")]
        elif path == "pyproject.toml":
            deps = self._parse_toml_deps(content)
        self._dependencies[path] = deps

    def _parse_toml_deps(self, content: str) -> list[str]:
        deps = []
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "[project]":
                in_deps = True
            elif stripped.startswith("[") and in_deps:
                in_deps = False
            elif in_deps and "=" in stripped:
                deps.append(stripped.split("=")[0].strip().strip('"').strip("'"))
        return deps

    def get_file(self, path: str) -> dict[str, Any] | None:
        return self._files.get(path)

    def get_symbols(self, path: str) -> list[dict[str, Any]]:
        return self._symbols.get(path, [])

    def get_dependencies(self, path: str) -> list[str]:
        return self._dependencies.get(path, [])

    def search(self, query: str) -> list[dict[str, Any]]:
        results = []
        lower = query.lower()
        for path, data in self._files.items():
            if lower in path.lower():
                results.append({"path": path, "type": "file", "data": data})
        for path, symbols in self._symbols.items():
            for sym in symbols:
                if lower in sym["text"].lower():
                    results.append({"path": path, "type": "symbol", "data": sym})
        return results[:50]

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": list(self._files.keys()),
            "file_count": len(self._files),
            "symbol_count": sum(len(v) for v in self._symbols.values()),
            "dependencies": self._dependencies,
        }


project_index = ProjectIndex

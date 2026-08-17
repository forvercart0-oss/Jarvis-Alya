"""File manager for JARVIS Phase 19."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.computer.files")


class FileManager:
    def __init__(self):
        self._home = Path.home()

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self._home / p
        return p.resolve()

    def list(self, path: str = "") -> dict[str, Any]:
        try:
            target = self._resolve(path) if path else self._home
            if not target.exists() or not target.is_dir():
                return {"success": False, "error": f"Not a directory: {target}"}
            entries = []
            for child in sorted(target.iterdir()):
                try:
                    entries.append({
                        "name": child.name,
                        "path": str(child),
                        "is_dir": child.is_dir(),
                        "size": child.stat().st_size if child.is_file() else 0,
                        "modified": child.stat().st_mtime,
                    })
                except OSError:
                    continue
            return {"success": True, "path": str(target), "entries": entries}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def search(self, query: str, path: str = "") -> dict[str, Any]:
        try:
            target = self._resolve(path) if path else self._home
            results = []
            for root, dirs, files in os.walk(str(target)):
                for name in files:
                    if query.lower() in name.lower():
                        results.append({"path": str(Path(root) / name), "name": name})
                if len(results) >= 50:
                    break
            return {"success": True, "query": query, "results": results}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def create_folder(self, path: str) -> dict[str, Any]:
        try:
            target = self._resolve(path)
            target.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(target)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def rename(self, old_path: str, new_name: str) -> dict[str, Any]:
        try:
            src = self._resolve(old_path)
            dst = src.parent / new_name
            src.rename(dst)
            return {"success": True, "path": str(dst)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def move(self, src: str, dst: str) -> dict[str, Any]:
        try:
            src_path = self._resolve(src)
            dst_path = self._resolve(dst)
            import shutil
            shutil.move(str(src_path), str(dst_path))
            return {"success": True, "path": str(dst_path)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def copy(self, src: str, dst: str) -> dict[str, Any]:
        try:
            src_path = self._resolve(src)
            dst_path = self._resolve(dst)
            import shutil
            if src_path.is_dir():
                shutil.copytree(str(src_path), str(dst_path))
            else:
                shutil.copy2(str(src_path), str(dst_path))
            return {"success": True, "path": str(dst_path)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def delete(self, path: str) -> dict[str, Any]:
        try:
            target = self._resolve(path)
            import shutil
            if target.is_dir():
                shutil.rmtree(str(target))
            else:
                target.unlink()
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def open(self, path: str) -> dict[str, Any]:
        try:
            target = self._resolve(path)
            import subprocess
            subprocess.run(["xdg-open", str(target)] if os.name != "nt" else ["start", str(target)], check=False)
            return {"success": True, "path": str(target)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


file_manager = FileManager()

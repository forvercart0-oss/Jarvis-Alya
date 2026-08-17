"""Downloader for JARVIS updater."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx

from updater.models import UpdateInfo, UpdateProgress, UpdateState

logger = logging.getLogger("jarvis.updater.downloader")


class UpdateDownloader:
    def __init__(self, repository: str = "forvercart0-oss/Jarvis-Alya"):
        self.repository = repository
        self._client = httpx.AsyncClient(timeout=120.0, follow_redirects=True)

    async def close(self) -> None:
        await self._client.aclose()

    async def download_commit(
        self,
        commit_sha: str,
        progress: UpdateProgress,
        destination: Path | None = None,
    ) -> Path | None:
        if destination is None:
            destination = Path(tempfile.mkdtemp(prefix="jarvis_update_"))

        url = f"https://github.com/{self.repository}/archive/{commit_sha}.zip"
        try:
            progress.state = UpdateState.DOWNLOADING
            progress.message = f"Downloading {commit_sha[:7]}..."
            async with self._client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    progress.error = f"Download failed: HTTP {resp.status_code}"
                    progress.state = UpdateState.FAILED
                    return None
                total = int(resp.headers.get("content-length", 0))
                progress.total = total
                progress.current = 0
                zip_path = destination / f"{commit_sha}.zip"
                with open(zip_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
                        progress.current += len(chunk)
                progress.message = "Download complete"
                progress.state = UpdateState.DOWNLOADED
                return zip_path
        except Exception as exc:
            progress.error = str(exc)
            progress.state = UpdateState.FAILED
            logger.warning("Download failed: %s", exc)
            return None

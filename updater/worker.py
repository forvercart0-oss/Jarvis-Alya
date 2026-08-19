"""Separate updater worker for JARVIS.

This script is designed to be run as a standalone process
to perform atomic updates without depending on the running
JARVIS process.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from updater.installer import UpdateInstaller
from updater.models import UpdateProgress
from updater.downloader import UpdateDownloader
from updater.verifier import UpdateVerifier
from updater.github import GitHubClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis.updater.worker")


async def run_update(repo_root: Path, commit_sha: str) -> int:
    progress = UpdateProgress()
    installer = UpdateInstaller(repo_root)
    downloader = UpdateDownloader()
    verifier = UpdateVerifier()
    github = GitHubClient()
    try:
        update_info = await github.get_latest_commit()
        if update_info is None:
            logger.error("Cannot reach GitHub")
            return 1
        zip_path = await downloader.download_commit(commit_sha or update_info.commit_sha, progress)
        if zip_path is None:
            logger.error("Download failed")
            return 1
        if not verifier.verify_zip(zip_path, commit_sha or update_info.commit_sha):
            logger.error("Verification failed")
            return 1
        success = await installer.install(zip_path, commit_sha or update_info.commit_sha, progress)
        return 0 if success else 1
    finally:
        await downloader.close()
        await github.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="JARVIS Updater Worker")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--commit", type=str, default="")
    args = parser.parse_args()
    return asyncio.run(run_update(args.repo_root, args.commit))


if __name__ == "__main__":
    sys.exit(main())

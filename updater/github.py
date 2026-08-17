"""GitHub API client for JARVIS updater."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from updater.models import UpdateInfo

logger = logging.getLogger("jarvis.updater.github")

GITHUB_API = "https://api.github.com"
REPO = "forvercart0-oss/Jarvis-Alya"
BRANCH = "main"


class GitHubClient:
    def __init__(self, repository: str = REPO, branch: str = BRANCH):
        self.repository = repository
        self.branch = branch
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_latest_commit(self) -> UpdateInfo | None:
        url = f"{GITHUB_API}/repos/{self.repository}/commits/{self.branch}"
        try:
            resp = await self._client.get(url)
            if resp.status_code == 404:
                return None
            if resp.status_code == 403:
                logger.warning("GitHub API rate limited")
                return None
            if resp.status_code != 200:
                logger.warning("GitHub API unexpected status: %d", resp.status_code)
                return None
            data = resp.json()
            if not isinstance(data, dict):
                return None
            commit = data.get("commit", {})
            sha = data.get("sha", "")
            message = commit.get("message", "")
            author = commit.get("author", {})
            author_name = author.get("name", "")
            committed_at = author.get("date", "")
            html_url = data.get("html_url", "")
            return UpdateInfo(
                commit_sha=sha,
                commit_message=message.split("\n")[0],
                commit_author=author_name,
                committed_at=committed_at,
                url=html_url,
                branch=self.branch,
                repository=self.repository,
            )
        except Exception as exc:
            logger.warning("GitHub commit check failed: %s", exc)
            return None

    async def get_commit_compare(self, base: str, head: str) -> dict[str, Any] | None:
        url = f"{GITHUB_API}/repos/{self.repository}/compare/{base}...{head}"
        try:
            resp = await self._client.get(url)
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception as exc:
            logger.warning("GitHub compare failed: %s", exc)
            return None

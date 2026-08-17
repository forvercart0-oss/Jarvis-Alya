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
                logger.warning("GitHub API 404: repo/branch not found (%s)", url)
                return None
            if resp.status_code == 403:
                logger.warning("GitHub API 403: rate limited or forbidden")
                return None
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", "unknown")
                logger.warning("GitHub API 429: rate limited, retry after %ss", retry_after)
                return None
            if resp.status_code >= 500:
                logger.error("GitHub API %d server error: %s", resp.status_code, resp.text[:500])
                return None
            if resp.status_code != 200:
                logger.warning("GitHub API unexpected status %d: %s", resp.status_code, resp.text[:500])
                return None
            data = resp.json()
            if not isinstance(data, dict):
                logger.warning("GitHub API returned non-dict: %s", type(data).__name__)
                return None
            commit = data.get("commit", {})
            sha = data.get("sha", "")
            message = commit.get("message", "")
            author = commit.get("author", {})
            author_name = author.get("name", "")
            committed_at = author.get("date", "")
            html_url = data.get("html_url", "")
            if not sha:
                logger.warning("GitHub API response missing 'sha' field")
                return None
            return UpdateInfo(
                commit_sha=sha,
                commit_message=message.split("\n")[0],
                commit_author=author_name,
                committed_at=committed_at,
                url=html_url,
                branch=self.branch,
                repository=self.repository,
            )
        except httpx.TimeoutException as exc:
            logger.error("GitHub API timeout: %s", exc)
            return None
        except httpx.NetworkError as exc:
            logger.error("GitHub API network error: %s", exc)
            return None
        except Exception as exc:
            logger.error("GitHub commit check failed: %s", exc, exc_info=True)
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

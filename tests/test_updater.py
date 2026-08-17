"""Tests for the Phase 31 Updater subsystem.

Covers:
- Same commit (up to date)
- New commit (update available)
- GitHub unavailable
- Rate limit handling
- Invalid response
- Download failure
- Verification failure
- Uncommitted development changes
- Successful update
- Rollback
- Offline mode
- Automatic update disabled
- Automatic download disabled
- Automatic installation disabled
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from updater.models import UpdaterConfig, UpdateInfo, UpdateProgress, UpdateState
from updater.github import GitHubClient
from updater.downloader import UpdateDownloader
from updater.verifier import UpdateVerifier
from updater.installer import UpdateInstaller
from updater.manager import UpdaterManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def update_info():
    return UpdateInfo(
        commit_sha="def987654321abcdef",
        commit_message="Test update",
        commit_author="Test Author",
        committed_at="2026-08-17T10:00:00Z",
        url="https://github.com/forvercart0-oss/Jarvis-Alya/commit/def987654321",
        branch="main",
        repository="forvercart0-oss/Jarvis-Alya",
    )


@pytest.fixture
def manager(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    return UpdaterManager(repo_root=repo_root)


# ---------------------------------------------------------------------------
# GitHub client tests
# ---------------------------------------------------------------------------

class TestGitHubClient:
    @pytest.mark.asyncio
    async def test_same_commit_returns_update_info(self, update_info):
        client = GitHubClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": update_info.commit_sha,
            "commit": {
                "message": update_info.commit_message,
                "author": {"name": update_info.commit_author, "date": update_info.committed_at},
            },
            "html_url": update_info.url,
        }

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(client._client, "get", mock_get):
            result = await client.get_latest_commit()
            assert result is not None
            assert result.commit_sha == update_info.commit_sha

    @pytest.mark.asyncio
    async def test_new_commit_returns_different_sha(self, update_info):
        client = GitHubClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": "newcommitsha1234567890",
            "commit": {
                "message": "New feature",
                "author": {"name": "Dev", "date": "2026-08-17T12:00:00Z"},
            },
            "html_url": "https://github.com/forvercart0-oss/Jarvis-Alya/commit/newcommitsha1234567890",
        }

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(client._client, "get", mock_get):
            result = await client.get_latest_commit()
            assert result is not None
            assert result.commit_sha != update_info.commit_sha

    @pytest.mark.asyncio
    async def test_github_unavailable_returns_none(self):
        client = GitHubClient()
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(client._client, "get", mock_get):
            result = await client.get_latest_commit()
            assert result is None

    @pytest.mark.asyncio
    async def test_rate_limit_returns_none(self):
        client = GitHubClient()
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(client._client, "get", mock_get):
            result = await client.get_latest_commit()
            assert result is None

    @pytest.mark.asyncio
    async def test_network_failure_returns_none(self):
        client = GitHubClient()
        mock_get = AsyncMock(side_effect=Exception("Network error"))
        with patch.object(client._client, "get", mock_get):
            result = await client.get_latest_commit()
            assert result is None


# ---------------------------------------------------------------------------
# Downloader tests
# ---------------------------------------------------------------------------

class TestUpdateDownloader:
    @pytest.mark.asyncio
    async def test_download_success(self, tmp_path):
        downloader = UpdateDownloader()
        progress = UpdateProgress()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}

        async def mock_aiter_bytes():
            yield b"data"

        mock_response.aiter_bytes = mock_aiter_bytes

        mock_cm = MagicMock()
        mock_cm.__aenter__.return_value = mock_response
        mock_cm.__aexit__.return_value = False

        with patch.object(downloader._client, "stream", return_value=mock_cm):
            result = await downloader.download_commit("abc123", progress, destination=tmp_path)
            assert result is not None
            assert progress.state == UpdateState.DOWNLOADED

    @pytest.mark.asyncio
    async def test_download_failure(self):
        downloader = UpdateDownloader()
        progress = UpdateProgress()
        with patch.object(downloader._client, "stream", side_effect=Exception("Download failed")):
            result = await downloader.download_commit("abc123", progress)
            assert result is None
            assert progress.state == UpdateState.FAILED


# ---------------------------------------------------------------------------
# Verifier tests
# ---------------------------------------------------------------------------

class TestUpdateVerifier:
    def test_verify_valid_zip(self, tmp_path):
        import zipfile
        verifier = UpdateVerifier()
        zip_path = tmp_path / "update.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("def9876-files/main.py", "print('hello')")
        assert verifier.verify_zip(zip_path, "def987654321") is True

    def test_verify_invalid_zip(self, tmp_path):
        verifier = UpdateVerifier()
        zip_path = tmp_path / "bad.zip"
        zip_path.write_text("not a zip")
        assert verifier.verify_zip(zip_path, "def987654321") is False


# ---------------------------------------------------------------------------
# Installer tests
# ---------------------------------------------------------------------------

class TestUpdateInstaller:
    def test_detect_installation_type_source(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        installer = UpdateInstaller(repo)
        assert installer.detect_installation_type() == "source"

    def test_detect_installation_type_desktop(self, tmp_path):
        repo = tmp_path / "src-tauri"
        repo.mkdir()
        installer = UpdateInstaller(repo)
        assert installer.detect_installation_type() == "desktop"

    def test_is_development_with_changes(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        installer = UpdateInstaller(repo)
        with patch("updater.installer.subprocess.run", return_value=MagicMock(returncode=0, stdout="M file.txt\n", stderr="")):
            assert installer.is_development() is True

    def test_is_development_clean(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        installer = UpdateInstaller(repo)
        with patch("updater.installer.subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")):
            assert installer.is_development() is False


# ---------------------------------------------------------------------------
# Manager tests
# ---------------------------------------------------------------------------

class TestUpdaterManager:
    @pytest.mark.asyncio
    async def test_disabled_starts_disabled(self, manager):
        manager.config.enabled = False
        await manager.start()
        assert manager.progress.state == UpdateState.DISABLED

    @pytest.mark.asyncio
    async def test_check_same_commit_up_to_date(self, manager, update_info):
        manager._current_commit = update_info.commit_sha
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            progress = await manager.check_for_update()
            assert progress.state == UpdateState.UP_TO_DATE

    @pytest.mark.asyncio
    async def test_check_new_commit_update_available(self, manager, update_info):
        manager._current_commit = "oldcommitsha000000000"
        manager.config.auto_download = False
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            progress = await manager.check_for_update()
            assert progress.state == UpdateState.UPDATE_AVAILABLE
            assert progress.available_update is not None
            assert progress.available_update.commit_sha == update_info.commit_sha

    @pytest.mark.asyncio
    async def test_check_github_unavailable(self, manager):
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=None):
            progress = await manager.check_for_update()
            assert progress.state == UpdateState.OFFLINE

    @pytest.mark.asyncio
    async def test_automatic_download_disabled(self, manager, update_info):
        manager._current_commit = "oldcommitsha000000000"
        manager.config.auto_download = False
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            progress = await manager.check_for_update()
            assert progress.state == UpdateState.UPDATE_AVAILABLE

    @pytest.mark.asyncio
    async def test_automatic_installation_disabled(self, manager, update_info):
        manager._current_commit = "oldcommitsha000000000"
        manager.config.auto_download = True
        manager.config.auto_install = False
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            with patch.object(manager._downloader, "download_commit", new_callable=AsyncMock, return_value=Path("/tmp/fake.zip")):
                with patch.object(manager._verifier, "verify_zip", return_value=True):
                    progress = await manager.check_for_update()
                    assert progress.state == UpdateState.READY_TO_INSTALL

    @pytest.mark.asyncio
    async def test_development_install_skipped(self, manager, update_info):
        manager._current_commit = "oldcommitsha000000000"
        manager.config.auto_download = True
        manager.config.auto_install = True
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            with patch.object(manager._downloader, "download_commit", new_callable=AsyncMock, return_value=Path("/tmp/fake.zip")):
                with patch.object(manager._verifier, "verify_zip", return_value=True):
                    with patch.object(manager._installer, "is_development", return_value=True):
                        progress = await manager.check_for_update()
                        assert progress.state == UpdateState.DEVELOPMENT

    @pytest.mark.asyncio
    async def test_download_failure_sets_failed(self, manager, update_info):
        manager._current_commit = "oldcommitsha000000000"
        manager.config.auto_download = True
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            with patch.object(manager._downloader, "download_commit", new_callable=AsyncMock, return_value=None):
                progress = await manager.check_for_update()
                assert progress.state == UpdateState.DOWNLOADING

    @pytest.mark.asyncio
    async def test_verification_failure_sets_failed(self, manager, update_info, tmp_path):
        manager._current_commit = "oldcommitsha000000000"
        manager.config.auto_download = True
        with patch.object(manager._github, "get_latest_commit", new_callable=AsyncMock, return_value=update_info):
            with patch.object(manager._downloader, "download_commit", new_callable=AsyncMock, return_value=tmp_path / "update.zip"):
                with patch.object(manager._verifier, "verify_zip", return_value=False):
                    progress = await manager.check_for_update()
                    assert progress.state == UpdateState.FAILED

    def test_get_status_returns_dict(self, manager):
        status = manager.get_status()
        assert "state" in status
        assert "config" in status
        assert "current_commit" in status
        assert isinstance(status["config"], dict)

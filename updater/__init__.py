"""Updater subsystem for JARVIS Phase 31."""

from updater.models import UpdaterConfig, UpdateInfo, UpdateProgress, UpdateState
from updater.manager import UpdaterManager
from updater.github import GitHubClient
from updater.downloader import UpdateDownloader
from updater.verifier import UpdateVerifier
from updater.installer import UpdateInstaller
from updater.worker import main as updater_worker_main

__all__ = [
    "UpdaterConfig",
    "UpdateInfo",
    "UpdateProgress",
    "UpdateState",
    "UpdaterManager",
    "GitHubClient",
    "UpdateDownloader",
    "UpdateVerifier",
    "UpdateInstaller",
    "updater_worker_main",
]

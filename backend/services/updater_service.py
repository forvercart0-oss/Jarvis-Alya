"""Updater service for JARVIS Phase 31."""

from __future__ import annotations

import logging

from updater.manager import UpdaterManager

logger = logging.getLogger("jarvis.updater.service")

updater_service = UpdaterManager()

"""Updater service for JARVIS Phase 31."""

from __future__ import annotations

import logging
from typing import Any

from updater.manager import UpdaterManager

logger = logging.getLogger("jarvis.updater.service")

updater_service = UpdaterManager()

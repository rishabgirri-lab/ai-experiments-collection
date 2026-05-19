"""Logging configuration."""
from __future__ import annotations

import logging

from orchestrator.config import get_settings


def configure_logging() -> None:
    """Set up root logger using LOG_LEVEL from settings."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

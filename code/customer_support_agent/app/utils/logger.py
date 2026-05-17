"""
logger.py — Centralised logging configuration.

Creates a named logger for the application with consistent formatting.
Import `get_logger(__name__)` in any module to obtain a module-specific
logger that inherits this configuration.
"""

import logging
import sys
from app.config.settings import settings


def _build_formatter() -> logging.Formatter:
    """Return a formatter with timestamp, level, module name, and message."""
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _configure_root_logger() -> None:
    """Configure the root logger once on first import."""
    root = logging.getLogger()

    # Avoid adding duplicate handlers if this module is re-imported
    if root.handlers:
        return

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    root.addHandler(handler)


_configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)

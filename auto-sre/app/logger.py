"""Lightweight structured logger for Auto-SRE."""

from __future__ import annotations

import logging

_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
_configured = False


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given name."""
    global _configured
    if not _configured:
        logging.basicConfig(level=logging.INFO, format=_FORMAT)
        _configured = True
    return logging.getLogger(name)

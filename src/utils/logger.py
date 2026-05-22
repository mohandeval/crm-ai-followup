"""
src/utils/logger.py
────────────────────
Centralized logger with Rich formatting.
Every module calls get_logger(__name__) — no print() statements.
"""

import logging
import sys
from config.settings import settings

# Use rich if available for pretty output in dev
try:
    from rich.logging import RichHandler
    HANDLER = RichHandler(rich_tracebacks=True, markup=True)
    FORMAT = "%(message)s"
except ImportError:
    HANDLER = logging.StreamHandler(sys.stdout)
    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        handler = HANDLER
        handler.setFormatter(logging.Formatter(FORMAT))
        logger.addHandler(handler)
        logger.propagate = False
    return logger

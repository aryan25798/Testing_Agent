"""
Structured Logging Configuration for Testing Agent Platform.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.config.settings import settings

# Ensure logs directory exists
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = settings.LOGS_DIR / "platform.log"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_root_logger() -> logging.Logger:
    """Configures the root application logger."""
    root_logger = logging.getLogger("testing_platform")
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if not root_logger.handlers:
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Rotating File Handler (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Returns a child logger scoped to the specified module."""
    return logging.getLogger(f"testing_platform.{name}")

"""Central logging configuration for the application."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

from app.core.config import Settings


_LOGGING_CONFIGURED = False


def configure_logging(settings: Settings) -> None:
    """Configure application logging with rotating file handlers."""

    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    log_directory = Path(settings.log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)

    log_file = log_directory / settings.log_file_name

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": settings.log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": settings.log_level,
                "filename": str(log_file),
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
    logging.captureWarnings(True)

    _LOGGING_CONFIGURED = True

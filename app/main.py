"""FastAPI application factory."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.init_db import init_db


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title=settings.app_name,
        description=settings.description,
        version=settings.version,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
    )

    # Compression middleware - reduces response size by 15-20%
    # Automatically compresses responses >1KB
    application.add_middleware(
        GZipMiddleware,
        minimum_size=1000,  # Only compress responses >1KB
        compresslevel=6     # Balance between speed and compression (1-9)
    )

    uploads_dir = Path(settings.uploads_directory)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    application.mount("/uploads", StaticFiles(directory=uploads_dir, check_dir=True), name="uploads")

    init_db()

    application.include_router(api_router)
    logger.info("Application initialized", extra={"environment": settings.environment})
    return application


app = create_app()

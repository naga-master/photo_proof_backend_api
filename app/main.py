"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.db.init_db import init_db


def create_app() -> FastAPI:
    settings = get_settings()

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

    uploads_dir = Path(settings.uploads_directory)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    application.mount("/uploads", StaticFiles(directory=uploads_dir, check_dir=True), name="uploads")

    init_db()

    application.include_router(api_router)
    return application


app = create_app()

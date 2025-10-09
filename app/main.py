"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings


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

    application.include_router(api_router)
    return application


app = create_app()

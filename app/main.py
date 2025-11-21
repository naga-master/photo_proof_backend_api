"""FastAPI application factory."""

import logging
import re
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.init_db import init_db
from app.middleware.tenant import tenant_middleware


logger = logging.getLogger(__name__)


def origin_matches_pattern(origin: str, patterns: list[str]) -> bool:
    """Check if origin matches any of the allowed patterns (supports wildcards)."""
    for pattern in patterns:
        if pattern == origin:
            return True
        # Convert wildcard pattern to regex
        if '*' in pattern:
            regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^:/]+')
            if re.match(f'^{regex_pattern}$', origin):
                return True
    return False


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title=settings.app_name,
        description=settings.description,
        version=settings.version,
    )

    # Add exception handler for HTTPException to ensure CORS headers
    @application.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Custom exception handler that adds CORS headers to error responses."""
        origin = request.headers.get("origin", "")
        
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",  # Prevent caching errors
            "Pragma": "no-cache",
            "Expires": "0"
        }
        if origin and origin_matches_pattern(origin, settings.cors_origins):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = "*"
            headers["Access-Control-Allow-Headers"] = "*"
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers
        )

    # Convert CORS origins to regex pattern for wildcard support
    # Separate exact origins from wildcard patterns
    exact_origins = [o for o in settings.cors_origins if '*' not in o]
    wildcard_patterns = [o for o in settings.cors_origins if '*' in o]
    
    # Build regex pattern from wildcards
    regex_parts = []
    for pattern in wildcard_patterns:
        regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^:/]+')
        regex_parts.append(regex_pattern)
    
    # Combine exact origins with regex
    if regex_parts:
        combined_regex = '|'.join([f'({r})' for r in regex_parts])
        application.add_middleware(
            CORSMiddleware,
            allow_origins=exact_origins,
            allow_origin_regex=combined_regex,
            allow_credentials=settings.allow_credentials,
            allow_methods=settings.allow_methods,
            allow_headers=settings.allow_headers,
        )
    else:
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
    
    # Multi-tenant middleware - detect studio from domain
    application.middleware("http")(tenant_middleware)
    logger.info("✅ Tenant detection middleware enabled")

    uploads_dir = Path(settings.uploads_directory)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    init_db()
    
    # Include API router (which now handles /uploads via files router with proper CORS)
    application.include_router(api_router)
    
    # Note: We DON'T mount StaticFiles here anymore - using API endpoint instead
    # This ensures CORS headers are properly applied to all file requests
    logger.info("Application initialized", extra={"environment": settings.environment})
    return application


app = create_app()

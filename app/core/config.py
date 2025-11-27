"""Application configuration and settings management."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field, field_validator

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use environment variables directly


class Settings(BaseModel):
    """Application runtime configuration."""

    app_name: str = "Photo Proof API"
    description: str = "Professional photo proofing gallery system API"
    version: str = Field(default="1.0.0", description="application release version")
    environment: str = Field(default=os.getenv("APP_ENV", "development"), description="environment identifier")
    api_prefix: str = Field(default="/api")
    cors_origins: List[str] = Field(
        default_factory=lambda: (
            # Check environment variable first
            [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
            if os.getenv("CORS_ORIGINS")
            else [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002",
                "http://localhost:5173",
                # Multi-tenant studio domains
                "http://*.photoapp.local:3001",  # Wildcard for all studio subdomains
                "http://demo.photoapp.local:3001",
                "http://alpha.photoapp.local:3001",
                "http://beta.photoapp.local:3001",
                "http://gamma.photoapp.local:3001",
            ]
        )
    )
    allow_credentials: bool = Field(default=True)
    # Restrict to specific methods for security (not "*")
    allow_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    # Restrict to specific headers for security (not "*")
    allow_headers: List[str] = Field(default_factory=lambda: [
        "Content-Type", "Authorization", "Accept", "Origin",
        "X-Requested-With", "Cache-Control", "X-Studio-ID"
    ])
    data_directory: str = Field(default=os.getenv("DATA_DIR", "data"))
    database_url: str = Field(default=os.getenv("DATABASE_URL", "postgresql://photo_proof_user:PhotoProof2024!@localhost/photo_proof_production"))
    uploads_directory: str = Field(default=os.getenv("UPLOADS_DIR", "uploads"))
    log_directory: str = Field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    log_file_name: str = Field(default_factory=lambda: os.getenv("LOG_FILE", "photo_proof_api.log"))
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL")
        or ("DEBUG" if os.getenv("APP_ENV", "development") == "development" else "INFO")
    )
    log_max_bytes: int = Field(default_factory=lambda: int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024)))
    log_backup_count: int = Field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", 10)))
    
    # Photo Version Settings
    max_photo_versions: int = Field(
        default_factory=lambda: int(os.getenv("MAX_PHOTO_VERSIONS", 100)),
        description="Maximum versions per photo"
    )
    max_upload_file_size_mb: int = Field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_FILE_SIZE_MB", 100)),
        description="Max file size in MB"
    )
    min_match_confidence: float = Field(
        default_factory=lambda: float(os.getenv("MIN_MATCH_CONFIDENCE", 0.7)),
        description="Min confidence for auto-match"
    )
    version_storage_prefix: str = Field(
        default="versions",
        description="Storage prefix for versions"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("log_level", mode="after")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()

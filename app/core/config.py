"""Application configuration and settings management."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Application runtime configuration."""

    app_name: str = Field(default="Photo Proof API")
    description: str = Field(
        default="Professional photo proofing gallery system API"
    )
    version: str = Field(default="1.0.0")
    environment: str = Field(default=os.getenv("APP_ENV", "development"))
    api_prefix: str = Field(default="/api")
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )
    allow_credentials: bool = Field(default=True)
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])
    data_directory: str = Field(default=os.getenv("DATA_DIR", "data"))
    database_url: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./photo_proof.db"))
    uploads_directory: str = Field(default=os.getenv("UPLOADS_DIR", "uploads"))

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


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()

"""Health and service status endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings


router = APIRouter(tags=["Health"])


@router.get("/")
async def root(settings: Settings = Depends(get_settings)):
    return {"message": f"{settings.app_name} is running", "version": settings.version}


@router.get("/api/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.version,
    }

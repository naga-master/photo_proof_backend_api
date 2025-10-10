"""Studio related endpoints."""

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.dependencies import get_data_manager
from app.schemas import Studio
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/studios", tags=["Studios"])


@router.get("/", response_model=List[Studio])
async def list_studios(data_manager: DataManager = Depends(get_data_manager)) -> List[Studio]:
    return data_manager.get_studios()


@router.post("/", response_model=Studio)
async def create_studio(studio_data: dict, data_manager: DataManager = Depends(get_data_manager)) -> Studio:
    """Create a new studio."""
    now = datetime.utcnow()
    studio = Studio(
        id=str(uuid4()),
        name=studio_data["name"],
        email=studio_data.get("email", ""),
        phone=studio_data.get("phone", ""),
        address=studio_data.get("address", ""),
        created_at=now,
        updated_at=now
    )
    return data_manager.create_studio(studio)


@router.get("/{studio_id}", response_model=Studio)
async def get_studio(studio: Studio = Depends(deps.get_studio)) -> Studio:
    return studio

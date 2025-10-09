"""Studio related endpoints."""

from typing import List

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.dependencies import get_data_manager
from app.schemas import Studio
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/studios", tags=["Studios"])


@router.get("/", response_model=List[Studio])
async def list_studios(data_manager: DataManager = Depends(get_data_manager)) -> List[Studio]:
    return data_manager.get_studios()


@router.get("/{studio_id}", response_model=Studio)
async def get_studio(studio: Studio = Depends(deps.get_studio)) -> Studio:
    return studio

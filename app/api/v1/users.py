"""User related endpoints."""

from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import User
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=List[User])
async def list_users(data_manager: DataManager = Depends(get_data_manager)) -> List[User]:
    return data_manager.get_users()


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> User:
    return current_user

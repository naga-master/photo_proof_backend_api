"""Common application dependencies."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas import User
from app.services.data_manager import DataManager


@lru_cache
def _create_data_manager(data_directory: str) -> DataManager:
    return DataManager(data_dir=data_directory)


def get_data_manager(settings: Settings = Depends(get_settings)) -> DataManager:
    """Provide a cached DataManager instance."""

    return _create_data_manager(settings.data_directory)


async def get_current_user(
    data_manager: DataManager = Depends(get_data_manager),
) -> User:
    """Retrieve the active user.

    In production this would validate tokens; for now we return the studio user.
    """

    user = data_manager.get_user_by_id("user-001")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found",
        )
    return user

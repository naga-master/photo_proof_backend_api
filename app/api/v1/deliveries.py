"""Digital delivery API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.deliveries import (
    DeliveryPackage,
    CreateDeliveryRequest,
    DeliverySettings,
    DeliveryAnalytics,
    ClientDeliveryPreferences,
)
from app.schemas.users import UserRead
from app.services.delivery_service import DeliveryService


router = APIRouter(prefix="/api/v1/deliveries", tags=["deliveries"])


@router.get("/", response_model=List[DeliveryPackage])
async def get_delivery_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get all delivery packages for the studio."""
    service = DeliveryService(db)
    return await service.get_studio_packages(
        current_user.studio_id, skip, limit, status_filter, client_id
    )


@router.post("/", response_model=DeliveryPackage)
async def create_delivery_package(
    request: CreateDeliveryRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new delivery package."""
    service = DeliveryService(db)
    return await service.create_package(current_user.studio_id, request)


@router.get("/{package_id}", response_model=DeliveryPackage)
async def get_delivery_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get a specific delivery package."""
    service = DeliveryService(db)
    package = await service.get_package(package_id)
    
    if not package or package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Delivery package not found"
        )
    
    return package


@router.put("/{package_id}/send")
async def send_delivery_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Send a delivery package to the client."""
    service = DeliveryService(db)
    package = await service.get_package(package_id)
    
    if not package or package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Delivery package not found"
        )
    
    await service.send_package(package_id)
    return {"message": "Delivery package sent successfully"}


@router.put("/{package_id}/regenerate-link")
async def regenerate_download_link(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Regenerate download link for a package."""
    service = DeliveryService(db)
    package = await service.get_package(package_id)
    
    if not package or package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Delivery package not found"
        )
    
    new_package = await service.regenerate_link(package_id)
    return {"message": "Download link regenerated", "new_url": new_package.download_url}


@router.delete("/{package_id}")
async def delete_delivery_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete a delivery package."""
    service = DeliveryService(db)
    package = await service.get_package(package_id)
    
    if not package or package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Delivery package not found"
        )
    
    await service.delete_package(package_id)
    return {"message": "Delivery package deleted"}


@router.get("/settings/studio", response_model=DeliverySettings)
async def get_delivery_settings(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get delivery settings for the studio."""
    service = DeliveryService(db)
    return await service.get_studio_settings(current_user.studio_id)


@router.put("/settings/studio", response_model=DeliverySettings)
async def update_delivery_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update delivery settings for the studio."""
    service = DeliveryService(db)
    return await service.update_studio_settings(current_user.studio_id, settings)


@router.get("/analytics", response_model=DeliveryAnalytics)
async def get_delivery_analytics(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get delivery performance analytics."""
    service = DeliveryService(db)
    return await service.get_analytics(current_user.studio_id)


@router.get("/clients/{client_id}/preferences", response_model=ClientDeliveryPreferences)
async def get_client_delivery_preferences(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get delivery preferences for a specific client."""
    service = DeliveryService(db)
    return await service.get_client_preferences(client_id)


@router.put("/clients/{client_id}/preferences", response_model=ClientDeliveryPreferences)
async def update_client_delivery_preferences(
    client_id: str,
    preferences: dict,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update delivery preferences for a specific client."""
    service = DeliveryService(db)
    return await service.update_client_preferences(client_id, preferences)


# Public endpoint for clients to access their deliveries
@router.get("/public/{token}")
async def access_delivery_package(
    token: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Public endpoint for clients to access delivery packages."""
    service = DeliveryService(db)
    
    package = await service.get_package_by_token(token)
    if not package:
        raise HTTPException(
            status_code=404,
            detail="Delivery package not found or expired"
        )
    
    if package.password_protected and not password:
        raise HTTPException(
            status_code=401,
            detail="Password required"
        )
    
    if package.password_protected and not await service.verify_password(token, password):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )
    
    # Track access
    await service.track_access(token)
    
    return {
        "package": package,
        "files": await service.get_package_files(package.id),
        "access_info": {
            "downloads_remaining": package.download_limit - package.download_count if package.download_limit else None,
            "expires_at": package.expiry_date,
        }
    }


@router.post("/public/{token}/download/{file_id}")
async def download_delivery_file(
    token: str,
    file_id: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Download a specific file from a delivery package."""
    service = DeliveryService(db)
    
    package = await service.get_package_by_token(token)
    if not package:
        raise HTTPException(
            status_code=404,
            detail="Delivery package not found or expired"
        )
    
    if package.password_protected and not await service.verify_password(token, password):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )
    
    download_url = await service.generate_file_download_url(token, file_id)
    return {"download_url": download_url}
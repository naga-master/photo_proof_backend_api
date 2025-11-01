"""Service Packages router for V2 API."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.db.models import ServicePackage, User
from app.schemas.invoice import (
    ServicePackageCreate,
    ServicePackageResponse,
    ServicePackageUpdate,
    ServicePackageListResponse,
)


router = APIRouter()


@router.get("/", response_model=ServicePackageListResponse)
async def get_service_packages(
    studio_id: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServicePackageListResponse:
    """
    Get all service packages for the current studio or specified studio.
    
    - **studio_id**: Optional studio ID filter
    - **category**: Optional category filter (e.g., "Wedding", "Portrait")
    """
    # Determine which studio to query
    if current_user.role == "studio":
        target_studio_id = studio_id or current_user.studio_id
    elif studio_id:
        target_studio_id = studio_id
    else:
        target_studio_id = current_user.studio_id
    
    # Build query
    query = select(ServicePackage).where(ServicePackage.studio_id == target_studio_id)
    
    if category:
        query = query.where(ServicePackage.category == category)
    
    query = query.order_by(ServicePackage.category, ServicePackage.price)
    
    result = await db.execute(query)
    packages = result.scalars().all()
    
    return ServicePackageListResponse(
        packages=[ServicePackageResponse.model_validate(pkg) for pkg in packages]
    )


@router.get("/{package_id}", response_model=ServicePackageResponse)
async def get_service_package(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServicePackageResponse:
    """Get a single service package by ID."""
    result = await db.execute(
        select(ServicePackage).where(ServicePackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service package not found"
        )
    
    # Check permissions
    if current_user.role == "studio" and package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this service package"
        )
    
    return ServicePackageResponse.model_validate(package)


@router.post("/", response_model=ServicePackageResponse, status_code=status.HTTP_201_CREATED)
async def create_service_package(
    package_data: ServicePackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServicePackageResponse:
    """
    Create a new service package.
    
    Only studio users can create service packages for their studio.
    """
    if current_user.role != "studio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can create service packages"
        )
    
    # Create new package
    new_package = ServicePackage(
        id=str(uuid4()),
        studio_id=current_user.studio_id,
        name=package_data.name,
        category=package_data.category,
        description=package_data.description,
        price=package_data.price,
        features=package_data.features,
    )
    
    db.add(new_package)
    await db.commit()
    await db.refresh(new_package)
    
    return ServicePackageResponse.model_validate(new_package)


@router.patch("/{package_id}", response_model=ServicePackageResponse)
async def update_service_package(
    package_id: str,
    package_data: ServicePackageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServicePackageResponse:
    """
    Update a service package.
    
    Only the owning studio can update their packages.
    """
    if current_user.role != "studio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can update service packages"
        )
    
    # Get package
    result = await db.execute(
        select(ServicePackage).where(ServicePackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service package not found"
        )
    
    # Check ownership
    if package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this service package"
        )
    
    # Update fields
    if package_data.name is not None:
        package.name = package_data.name
    if package_data.category is not None:
        package.category = package_data.category
    if package_data.description is not None:
        package.description = package_data.description
    if package_data.price is not None:
        package.price = package_data.price
    if package_data.features is not None:
        package.features = package_data.features
    
    await db.commit()
    await db.refresh(package)
    
    return ServicePackageResponse.model_validate(package)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_package(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a service package.
    
    Only the owning studio can delete their packages.
    """
    if current_user.role != "studio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can delete service packages"
        )
    
    # Get package
    result = await db.execute(
        select(ServicePackage).where(ServicePackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service package not found"
        )
    
    # Check ownership
    if package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this service package"
        )
    
    await db.delete(package)
    await db.commit()

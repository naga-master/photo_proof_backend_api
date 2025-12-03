"""Service Packages router for V2 API."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, is_studio_user
from app.db.models import ServicePackage, User
from app.core.permissions import require_manage_services
from app.schemas.invoice import (
    ServicePackageCreate,
    ServicePackageResponse,
    ServicePackageUpdate,
    ServicePackageListResponse,
)


router = APIRouter()


@router.get("/", response_model=ServicePackageListResponse)
def get_service_packages(
    studio_id: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServicePackageListResponse:
    """
    Get all service packages for the current studio or specified studio.
    
    - **studio_id**: Optional studio ID filter
    - **category**: Optional category filter (e.g., "Wedding", "Portrait")
    """
    # Determine which studio to query
    if is_studio_user(current_user.role):
        target_studio_id = studio_id or current_user.studio_id
    elif studio_id:
        target_studio_id = studio_id
    else:
        target_studio_id = current_user.studio_id
    
    # Build query
    query = db.query(ServicePackage).filter(ServicePackage.studio_id == target_studio_id)
    
    if category:
        query = query.filter(ServicePackage.category == category)
    
    query = query.order_by(ServicePackage.category, ServicePackage.price)
    
    packages = query.all()
    
    return ServicePackageListResponse(
        packages=[ServicePackageResponse.model_validate(pkg) for pkg in packages],
        total=len(packages)
    )


@router.get("/{package_id}", response_model=ServicePackageResponse)
def get_service_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServicePackageResponse:
    """Get a single service package by ID."""
    package = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service package not found"
        )
    
    # Check permissions
    if is_studio_user(current_user.role) and package.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this service package"
        )
    
    return ServicePackageResponse.model_validate(package)


@router.post("/", response_model=ServicePackageResponse, status_code=status.HTTP_201_CREATED)
def create_service_package(
    package_data: ServicePackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manage_services),
) -> ServicePackageResponse:
    """
    Create a new service package.
    
    Requires canManageServices permission.
    """
    
    # Create new package
    new_package = ServicePackage(
        id=str(uuid4()),
        studio_id=current_user.studio_id,
        name=package_data.name,
        category=package_data.category,
        description=package_data.description,
        price=package_data.price,
        package_type_id=package_data.package_type_id,
        features=package_data.features,
        restrictions=package_data.restrictions,
        deliverables=package_data.deliverables,
        lifecycle_config=package_data.lifecycle_config,
    )
    
    db.add(new_package)
    db.commit()
    db.refresh(new_package)
    
    return ServicePackageResponse.model_validate(new_package)


@router.patch("/{package_id}", response_model=ServicePackageResponse)
def update_service_package(
    package_id: str,
    package_data: ServicePackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manage_services),
) -> ServicePackageResponse:
    """
    Update a service package.
    
    Requires canManageServices permission.
    """
    
    # Get package
    package = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    
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
    if package_data.package_type_id is not None:
        package.package_type_id = package_data.package_type_id
    if package_data.features is not None:
        package.features = package_data.features
    if package_data.deliverables is not None:
        package.deliverables = package_data.deliverables
    if package_data.restrictions is not None:
        package.restrictions = package_data.restrictions
    if package_data.lifecycle_config is not None:
        package.lifecycle_config = package_data.lifecycle_config
    
    db.commit()
    db.refresh(package)
    
    return ServicePackageResponse.model_validate(package)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manage_services),
) -> None:
    """
    Delete a service package.
    
    Requires canManageServices permission.
    """
    
    # Get package
    package = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    
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
    
    db.delete(package)
    db.commit()

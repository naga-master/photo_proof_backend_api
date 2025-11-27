"""Package Types router for dynamic package system."""

from typing import List, Optional
from uuid import uuid4
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, is_studio_user
from app.db.models import PackageType, User
from app.schemas.package_types import (
    PackageTypeCreate,
    PackageTypeUpdate,
    PackageTypeResponse,
    PackageTypeListResponse,
    PackageTypeSimple,
    PackageTypeWithSchema,
)


router = APIRouter()


@router.get("/", response_model=PackageTypeListResponse)
def get_package_types(
    include_inactive: bool = False,
    only_predefined: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PackageTypeListResponse:
    """
    Get all package types.
    
    - **include_inactive**: Include inactive package types (default: False)
    - **only_predefined**: Only return predefined system types (default: False)
    """
    query = db.query(PackageType)
    
    # Filter by active status
    if not include_inactive:
        query = query.filter(PackageType.is_active == True)
    
    # Filter by predefined status
    if only_predefined:
        query = query.filter(PackageType.is_predefined == True)
    
    # Order by predefined first, then by display name
    query = query.order_by(
        PackageType.is_predefined.desc(),
        PackageType.display_name
    )
    
    package_types = query.all()
    
    # Parse attribute_schema JSON for each type
    response_types = []
    for pt in package_types:
        schema_dict = json.loads(pt.attribute_schema) if isinstance(pt.attribute_schema, str) else pt.attribute_schema
        response_types.append(PackageTypeResponse(
            id=pt.id,
            name=pt.name,
            display_name=pt.display_name,
            description=pt.description,
            icon=pt.icon,
            is_predefined=pt.is_predefined,
            is_active=pt.is_active,
            attribute_schema=schema_dict,
            created_by=pt.created_by,
            created_at=pt.created_at,
            updated_at=pt.updated_at
        ))
    
    return PackageTypeListResponse(
        package_types=response_types,
        total=len(response_types)
    )


@router.get("/simple", response_model=List[PackageTypeSimple])
def get_package_types_simple(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PackageTypeSimple]:
    """
    Get simplified list of active package types for dropdowns/selectors.
    """
    package_types = db.query(PackageType).filter(
        PackageType.is_active == True
    ).order_by(
        PackageType.is_predefined.desc(),
        PackageType.display_name
    ).all()
    
    return [
        PackageTypeSimple(
            id=pt.id,
            name=pt.name,
            display_name=pt.display_name,
            icon=pt.icon,
            is_predefined=pt.is_predefined
        )
        for pt in package_types
    ]


@router.get("/{type_id}", response_model=PackageTypeResponse)
def get_package_type(
    type_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PackageTypeResponse:
    """Get a single package type by ID with its full schema."""
    package_type = db.query(PackageType).filter(PackageType.id == type_id).first()
    
    if not package_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package type not found"
        )
    
    # Parse attribute_schema JSON
    schema_dict = json.loads(package_type.attribute_schema) if isinstance(package_type.attribute_schema, str) else package_type.attribute_schema
    
    return PackageTypeResponse(
        id=package_type.id,
        name=package_type.name,
        display_name=package_type.display_name,
        description=package_type.description,
        icon=package_type.icon,
        is_predefined=package_type.is_predefined,
        is_active=package_type.is_active,
        attribute_schema=schema_dict,
        created_by=package_type.created_by,
        created_at=package_type.created_at,
        updated_at=package_type.updated_at
    )


@router.get("/{type_id}/schema")
def get_package_type_schema(
    type_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get just the attribute schema for a package type.
    Useful for dynamic form rendering without full type details.
    """
    package_type = db.query(PackageType).filter(PackageType.id == type_id).first()
    
    if not package_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package type not found"
        )
    
    # Parse and return just the schema
    schema_dict = json.loads(package_type.attribute_schema) if isinstance(package_type.attribute_schema, str) else package_type.attribute_schema
    return schema_dict


@router.post("/", response_model=PackageTypeResponse, status_code=status.HTTP_201_CREATED)
def create_package_type(
    package_type_data: PackageTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PackageTypeResponse:
    """
    Create a new custom package type.
    
    Only studio users can create custom package types.
    Predefined types cannot be created via API.
    """
    if not is_studio_user(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can create package types"
        )
    
    # Check if name already exists
    existing = db.query(PackageType).filter(
        PackageType.name == package_type_data.name.lower()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Package type with name '{package_type_data.name}' already exists"
        )
    
    # Convert attribute schema to JSON string
    schema_json = json.dumps(package_type_data.attribute_schema.dict())
    
    # Create new package type
    new_package_type = PackageType(
        id=str(uuid4()),
        name=package_type_data.name.lower(),
        display_name=package_type_data.display_name,
        description=package_type_data.description,
        icon=package_type_data.icon,
        is_predefined=False,  # Custom types are never predefined
        is_active=package_type_data.is_active,
        attribute_schema=schema_json,
        created_by=current_user.id,
    )
    
    db.add(new_package_type)
    db.commit()
    db.refresh(new_package_type)
    
    # Parse schema for response
    schema_dict = json.loads(new_package_type.attribute_schema)
    
    return PackageTypeResponse(
        id=new_package_type.id,
        name=new_package_type.name,
        display_name=new_package_type.display_name,
        description=new_package_type.description,
        icon=new_package_type.icon,
        is_predefined=new_package_type.is_predefined,
        is_active=new_package_type.is_active,
        attribute_schema=schema_dict,
        created_by=new_package_type.created_by,
        created_at=new_package_type.created_at,
        updated_at=new_package_type.updated_at
    )


@router.patch("/{type_id}", response_model=PackageTypeResponse)
def update_package_type(
    type_id: str,
    package_type_data: PackageTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PackageTypeResponse:
    """
    Update a package type.
    
    Only custom (non-predefined) package types can be updated.
    Only studio users can update package types.
    """
    if not is_studio_user(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can update package types"
        )
    
    # Get package type
    package_type = db.query(PackageType).filter(PackageType.id == type_id).first()
    
    if not package_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package type not found"
        )
    
    # Prevent updating predefined types
    if package_type.is_predefined:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update predefined package types"
        )
    
    # Update fields
    if package_type_data.name is not None:
        # Check if new name conflicts
        existing = db.query(PackageType).filter(
            PackageType.name == package_type_data.name.lower(),
            PackageType.id != type_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Package type with name '{package_type_data.name}' already exists"
            )
        package_type.name = package_type_data.name.lower()
    
    if package_type_data.display_name is not None:
        package_type.display_name = package_type_data.display_name
    
    if package_type_data.description is not None:
        package_type.description = package_type_data.description
    
    if package_type_data.icon is not None:
        package_type.icon = package_type_data.icon
    
    if package_type_data.is_active is not None:
        package_type.is_active = package_type_data.is_active
    
    if package_type_data.attribute_schema is not None:
        schema_json = json.dumps(package_type_data.attribute_schema.dict())
        package_type.attribute_schema = schema_json
    
    db.commit()
    db.refresh(package_type)
    
    # Parse schema for response
    schema_dict = json.loads(package_type.attribute_schema)
    
    return PackageTypeResponse(
        id=package_type.id,
        name=package_type.name,
        display_name=package_type.display_name,
        description=package_type.description,
        icon=package_type.icon,
        is_predefined=package_type.is_predefined,
        is_active=package_type.is_active,
        attribute_schema=schema_dict,
        created_by=package_type.created_by,
        created_at=package_type.created_at,
        updated_at=package_type.updated_at
    )


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package_type(
    type_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Soft delete (deactivate) a package type.
    
    Only custom (non-predefined) package types can be deleted.
    Only studio users can delete package types.
    """
    if not is_studio_user(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can delete package types"
        )
    
    # Get package type
    package_type = db.query(PackageType).filter(PackageType.id == type_id).first()
    
    if not package_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package type not found"
        )
    
    # Prevent deleting predefined types
    if package_type.is_predefined:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete predefined package types"
        )
    
    # Soft delete by deactivating
    package_type.is_active = False
    db.commit()

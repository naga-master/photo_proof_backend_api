"""Package Type schemas for API validation and serialization."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ============================================================================
# Field Schema Models (for dynamic form rendering)
# ============================================================================

class FieldOption(BaseModel):
    """Option for select/multi-select fields."""
    label: str
    value: str


class FieldDependency(BaseModel):
    """Dependency condition for conditional field visibility."""
    field: str  # Field name to check
    value: Any  # Value that field must have for this field to show


class FieldSchema(BaseModel):
    """Schema definition for a single form field."""
    name: str
    type: str  # 'text', 'number', 'toggle', 'select', 'multi-select', 'textarea'
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    min: Optional[int] = None
    max: Optional[int] = None
    options: Optional[List[FieldOption]] = None  # For select/multi-select
    dependency: Optional[FieldDependency] = None  # Conditional visibility
    
    @validator('type')
    def validate_field_type(cls, v):
        """Validate field type."""
        allowed_types = ['text', 'number', 'toggle', 'select', 'multi-select', 'textarea']
        if v not in allowed_types:
            raise ValueError(f'Field type must be one of {allowed_types}')
        return v


class FormSection(BaseModel):
    """A section of the dynamic form containing related fields."""
    title: str
    fields: List[FieldSchema]


class PackageTypeAttributeSchema(BaseModel):
    """Complete attribute schema for a package type."""
    sections: List[FormSection]


# ============================================================================
# Package Type CRUD Schemas
# ============================================================================

class PackageTypeBase(BaseModel):
    """Base schema for package type."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True


class PackageTypeCreate(PackageTypeBase):
    """Schema for creating a new package type."""
    attribute_schema: PackageTypeAttributeSchema
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "birthday",
                "display_name": "Birthday Photography",
                "description": "Birthday party and celebration photography",
                "icon": "cake",
                "is_active": True,
                "attribute_schema": {
                    "sections": [
                        {
                            "title": "Basic Information",
                            "fields": [
                                {
                                    "name": "name",
                                    "type": "text",
                                    "label": "Package Name",
                                    "required": True
                                },
                                {
                                    "name": "price",
                                    "type": "number",
                                    "label": "Price (INR)",
                                    "required": True,
                                    "min": 0
                                }
                            ]
                        }
                    ]
                }
            }
        }


class PackageTypeUpdate(BaseModel):
    """Schema for updating a package type."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    attribute_schema: Optional[PackageTypeAttributeSchema] = None


class PackageTypeResponse(PackageTypeBase):
    """Schema for package type response."""
    id: str
    is_predefined: bool
    attribute_schema: Dict[str, Any]  # JSON object
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PackageTypeListResponse(BaseModel):
    """Schema for list of package types."""
    package_types: List[PackageTypeResponse]
    total: int


# ============================================================================
# Simplified Schema for Dropdowns/Selectors
# ============================================================================

class PackageTypeSimple(BaseModel):
    """Simplified package type for dropdowns."""
    id: str
    name: str
    display_name: str
    icon: Optional[str] = None
    is_predefined: bool
    
    class Config:
        from_attributes = True


class PackageTypeWithSchema(PackageTypeResponse):
    """Package type with parsed attribute schema."""
    parsed_schema: PackageTypeAttributeSchema
    
    @classmethod
    def from_package_type(cls, package_type):
        """Create from PackageType model with parsed schema."""
        import json
        schema_dict = json.loads(package_type.attribute_schema) if isinstance(package_type.attribute_schema, str) else package_type.attribute_schema
        
        return cls(
            id=package_type.id,
            name=package_type.name,
            display_name=package_type.display_name,
            description=package_type.description,
            icon=package_type.icon,
            is_predefined=package_type.is_predefined,
            is_active=package_type.is_active,
            attribute_schema=schema_dict,
            parsed_schema=PackageTypeAttributeSchema(**schema_dict),
            created_by=package_type.created_by,
            created_at=package_type.created_at,
            updated_at=package_type.updated_at
        )

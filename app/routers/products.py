"""Products router for store functionality."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.db.models import Product, ProductOption, User
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


router = APIRouter()


# Response schemas
class ProductOptionResponse(BaseModel):
    """Product option response."""
    id: int
    product_id: str
    option_type: str
    name: str
    price: Decimal
    order_index: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    """Product response."""
    id: str
    name: str
    short_description: str
    detailed_description: str
    specs: dict
    mockup_images: list
    is_active: bool
    options: Optional[List[ProductOptionResponse]] = None
    
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[ProductResponse])
def list_products(
    active_only: bool = Query(True, description="Show only active products"),
    db: Session = Depends(get_db),
) -> List[Product]:
    """
    List all products available in the store.
    
    Public endpoint - no authentication required.
    """
    query = db.query(Product)
    
    if active_only:
        query = query.filter(Product.is_active == True)
    
    products = query.all()
    
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
) -> Product:
    """
    Get a specific product with its options.
    
    Public endpoint - no authentication required.
    """
    product = (
        db.query(Product)
        .options(joinedload(Product.options))
        .filter(Product.id == product_id)
        .first()
    )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.get("/{product_id}/options", response_model=List[ProductOptionResponse])
def get_product_options(
    product_id: str,
    option_type: Optional[str] = Query(None, description="Filter by option type: size or type"),
    db: Session = Depends(get_db),
) -> List[ProductOption]:
    """
    Get all options for a specific product.
    
    Can filter by option_type (size/type).
    Public endpoint - no authentication required.
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    query = (
        db.query(ProductOption)
        .filter(
            ProductOption.product_id == product_id,
            ProductOption.is_active == True
        )
    )
    
    if option_type:
        query = query.filter(ProductOption.option_type == option_type)
    
    options = query.order_by(ProductOption.order_index).all()
    
    return options

"""E-commerce store schemas."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductOptionValue(BaseModel):
    """Individual product option value."""
    label: str
    value: str


class ProductOption(BaseModel):
    """Product customization option."""
    name: str
    type: str  # 'select', 'text', 'number'
    required: bool = False
    values: Optional[List[ProductOptionValue]] = None


class ProductBase(BaseModel):
    """Base product fields."""
    name: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    price: Decimal = Field(..., ge=0)
    category: str = Field(..., min_length=1)
    image: Optional[str] = None


class ProductCreate(ProductBase):
    """Product creation schema."""
    stock: int = Field(default=0, ge=0)
    options: List[ProductOption] = []


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    category: Optional[str] = None
    image: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    options: Optional[List[ProductOption]] = None


class ProductResponse(ProductBase):
    """Product response schema."""
    id: int
    studio_id: str
    stock: int
    options: List[ProductOption]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """List of products response."""
    products: List[ProductResponse]
    total: int


# ============================================================================
# CART SCHEMAS
# ============================================================================

class CartItemBase(BaseModel):
    """Base cart item fields."""
    product_id: int
    quantity: int = Field(..., gt=0)


class CartItemCreate(CartItemBase):
    """Cart item creation schema."""
    selected_options: Dict[str, Any] = {}


class CartItemUpdate(BaseModel):
    """Cart item update schema."""
    quantity: Optional[int] = Field(None, gt=0)
    selected_options: Optional[Dict[str, Any]] = None


class CartItemResponse(CartItemBase):
    """Cart item response schema."""
    id: int
    user_id: str
    selected_options: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    # Product details
    product: ProductResponse
    subtotal: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Shopping cart response."""
    items: List[CartItemResponse]
    total_items: int
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal


# ============================================================================
# ORDER SCHEMAS
# ============================================================================

class OrderItemData(BaseModel):
    """Order line item data."""
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    selected_options: Dict[str, Any] = {}
    subtotal: Decimal


class ShippingAddressData(BaseModel):
    """Shipping address data."""
    full_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "USA"


class OrderBase(BaseModel):
    """Base order fields."""
    shipping_address: ShippingAddressData


class OrderCreate(OrderBase):
    """Order creation schema."""
    payment_method: str = Field(..., pattern="^(Credit Card|PayPal|Stripe)$")


class OrderUpdate(BaseModel):
    """Order update schema."""
    status: str = Field(..., pattern="^(Pending|Processing|Shipped|Delivered|Cancelled)$")
    tracking_number: Optional[str] = None


class OrderResponse(OrderBase):
    """Order response schema."""
    id: int
    order_number: str
    user_id: str
    studio_id: str
    items: List[OrderItemData]
    subtotal: Decimal
    tax: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    status: str
    payment_method: str
    payment_status: str
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """List of orders response."""
    orders: List[OrderResponse]
    total: int

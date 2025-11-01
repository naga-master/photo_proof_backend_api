"""Orders router for order management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
import uuid

from app.db.session import get_db
from app.db.models import Order, User, CartItem
from app.api.deps import get_current_user


router = APIRouter()


# Request/Response schemas
class ShippingAddress(BaseModel):
    """Shipping address."""
    name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "US"
    phone: str


class OrderCreate(BaseModel):
    """Create order from cart."""
    shipping_address: ShippingAddress
    billing_address: ShippingAddress
    payment_method: str = "credit_card"
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response."""
    id: str
    order_number: str
    user_id: Optional[str] = None
    client_id: Optional[int] = None
    items: list
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    status: str
    payment_status: str
    shipping_address: dict
    billing_address: dict
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Order]:
    """
    List orders for the current user.
    
    Studio users see all orders for their studio's clients.
    Clients see only their own orders.
    """
    query = db.query(Order)
    
    # Filter based on user role
    if current_user.studio_id:
        # Studio users see all orders from their clients
        # This requires joining with clients table
        pass  # For now, show user's orders
    else:
        # Clients see their own orders
        query = query.filter(Order.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = (
        query
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    """
    Get a specific order by ID.
    
    Users can only access their own orders (or studio users can access all).
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check access permissions
    if order.user_id != current_user.id:
        # For now, deny access. In production, check if studio user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )
    
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    """
    Create an order from the current cart.
    
    Converts cart items to an order and clears the cart.
    """
    # Get cart items
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .all()
    )
    
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    # Convert cart items to order items
    order_items = []
    subtotal = Decimal("0.00")
    
    for item in cart_items:
        order_item = {
            "photo_id": item.photo_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "total_price": float(item.total_price),
        }
        order_items.append(order_item)
        subtotal += item.total_price
    
    # Calculate totals
    tax_rate = Decimal("0.08")  # 8% tax - should be configurable
    tax = subtotal * tax_rate
    shipping = Decimal("10.00")  # Flat rate - should be configurable
    total = subtotal + tax + shipping
    
    # Generate order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Create order
    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        client_id=current_user.client_profile.id if current_user.client_profile else None,
        items=order_items,
        subtotal=subtotal,
        tax=tax,
        shipping=shipping,
        total=total,
        status="pending",
        payment_status="unpaid",
        shipping_address=order_data.shipping_address.model_dump(),
        billing_address=order_data.billing_address.model_dump(),
        payment_method=order_data.payment_method,
        notes=order_data.notes,
    )
    
    db.add(order)
    
    # Clear cart
    for item in cart_items:
        db.delete(item)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    status: str = Query(..., description="New status: pending, confirmed, processing, shipped, delivered, cancelled"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    """
    Update order status.
    
    Only studio users can update order status.
    """
    # Only studio users can update orders
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can update order status"
        )
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate status
    valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    order.status = status
    db.commit()
    db.refresh(order)
    
    return order


@router.patch("/{order_id}/payment", response_model=OrderResponse)
def update_payment_status(
    order_id: str,
    payment_status: str = Query(..., description="Payment status: unpaid, paid, refunded"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    """
    Update payment status.
    
    Only studio users can update payment status.
    """
    # Only studio users can update
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can update payment status"
        )
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate payment status
    valid_statuses = ['unpaid', 'paid', 'refunded']
    if payment_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    order.payment_status = payment_status
    db.commit()
    db.refresh(order)
    
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Cancel an order.
    
    Sets status to 'cancelled'. Only pending orders can be cancelled.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check access - user owns order or is studio user
    if order.user_id != current_user.id and not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order"
        )
    
    if order.status not in ['pending', 'confirmed']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or confirmed orders can be cancelled"
        )
    
    order.status = 'cancelled'
    db.commit()

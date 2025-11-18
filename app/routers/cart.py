"""Cart router for shopping cart functionality."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

from app.db.session import get_db
from app.db.models import CartItem, User, Photo, Product, ProductOption
from app.api.deps import get_current_user


router = APIRouter()


# Request/Response schemas
class CartItemCreate(BaseModel):
    """Add item to cart."""
    photo_id: int
    product_id: str
    selected_size_option_id: int
    selected_type_option_id: Optional[int] = None
    quantity: int = 1


class CartItemUpdate(BaseModel):
    """Update cart item quantity."""
    quantity: int


class CartItemResponse(BaseModel):
    """Cart item response."""
    id: str
    photo_id: int
    product_id: str
    selected_size_option_id: int
    selected_type_option_id: Optional[int] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    
    # Nested data for convenience
    photo: Optional[dict] = None
    product: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class CartSummary(BaseModel):
    """Cart summary response."""
    items: List[CartItemResponse]
    total_items: int
    subtotal: Decimal
    tax: Decimal
    total: Decimal


@router.get("/", response_model=List[CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CartItem]:
    """
    Get current user's cart items.
    
    Returns all items in the cart with product and photo details.
    """
    cart_items = (
        db.query(CartItem)
        .options(
            joinedload(CartItem.photo),
            joinedload(CartItem.product),
        )
        .filter(CartItem.user_id == current_user.id)
        .all()
    )
    
    return cart_items


@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartItem:
    """
    Add an item to the cart.
    
    Creates a new cart item or updates quantity if same item exists.
    """
    # Verify photo exists
    photo = db.query(Photo).filter(Photo.id == item.photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Verify product exists
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Verify size option exists
    size_option = (
        db.query(ProductOption)
        .filter(ProductOption.id == item.selected_size_option_id)
        .first()
    )
    if not size_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size option not found"
        )
    
    # Check for existing cart item with same configuration
    existing = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.photo_id == item.photo_id,
            CartItem.product_id == item.product_id,
            CartItem.selected_size_option_id == item.selected_size_option_id,
            CartItem.selected_type_option_id == item.selected_type_option_id,
        )
        .first()
    )
    
    if existing:
        # Update quantity
        existing.quantity += item.quantity
        db.commit()
        db.refresh(existing)
        return existing
    
    # Calculate unit price based on selected options
    unit_price = size_option.price
    if item.selected_type_option_id:
        type_option = (
            db.query(ProductOption)
            .filter(ProductOption.id == item.selected_type_option_id)
            .first()
        )
        if type_option:
            unit_price += type_option.price
    
    total_price = unit_price * item.quantity
    
    # Create new cart item
    cart_item = CartItem(
        user_id=current_user.id,
        photo_id=item.photo_id,
        product_id=item.product_id,
        selected_size_option_id=item.selected_size_option_id,
        selected_type_option_id=item.selected_type_option_id,
        quantity=item.quantity,
        unit_price=unit_price,
        total_price=total_price,
    )
    
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    return cart_item


@router.patch("/{cart_item_id}", response_model=CartItemResponse)
def update_cart_item(
    cart_item_id: str,
    update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartItem:
    """
    Update a cart item's quantity.
    
    Set quantity to 0 to remove the item.
    """
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == cart_item_id,
            CartItem.user_id == current_user.id
        )
        .first()
    )
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    if update.quantity <= 0:
        # Remove item
        db.delete(cart_item)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Cart item removed"
        )
    
    # Update quantity and total price
    cart_item.quantity = update.quantity
    cart_item.total_price = cart_item.unit_price * update.quantity
    
    db.commit()
    db.refresh(cart_item)
    
    return cart_item


@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    cart_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Remove an item from the cart.
    """
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == cart_item_id,
            CartItem.user_id == current_user.id
        )
        .first()
    )
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    db.delete(cart_item)
    db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Clear all items from the cart.
    """
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()


@router.get("/summary", response_model=CartSummary)
def get_cart_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get cart summary with totals.
    
    Calculates subtotal, tax, and total.
    """
    cart_items = (
        db.query(CartItem)
        .options(
            joinedload(CartItem.photo),
            joinedload(CartItem.product),
        )
        .filter(CartItem.user_id == current_user.id)
        .all()
    )
    
    subtotal = sum(item.total_price for item in cart_items)
    tax_rate = Decimal("0.08")  # 8% tax - should be configurable
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    return {
        "items": cart_items,
        "total_items": len(cart_items),
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }

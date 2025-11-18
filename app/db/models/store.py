"""Store product, cart, and order models."""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    """Store product (prints, canvases, albums, etc.)."""

    __tablename__ = "products"

    id = Column(String(50), primary_key=True)  # Slug-based: 'prints', 'canvases', etc.
    
    name = Column(String(255), nullable=False)
    short_description = Column(String(500), nullable=False)
    detailed_description = Column(Text, nullable=False)
    
    # Specifications stored as JSON object
    # Format: {"Paper Type": "Kodak Endura", "Finish": "Lustre", ...}
    specs = Column(JSON, nullable=False)
    
    # Mockup images stored as JSON array
    # Format: ["https://...", "https://...", ...]
    mockup_images = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    options = relationship("ProductOption", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name})>"


class ProductOption(Base, TimestampMixin):
    """Product size/type variant options."""

    __tablename__ = "product_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    option_type = Column(String(50), nullable=False)  # 'size' or 'type'
    name = Column(String(100), nullable=False)  # '8x10', 'Lustre', etc.
    price = Column(Numeric(10, 2), nullable=False)
    
    order_index = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    product = relationship("Product", back_populates="options")

    def __repr__(self):
        return f"<ProductOption(id={self.id}, product={self.product_id}, name={self.name}, price={self.price})>"


class CartItem(Base, TimestampMixin):
    """Shopping cart item."""

    __tablename__ = "cart_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Session-based for guest users, user-based for logged-in users
    session_id = Column(String(100), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Product and photo
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Selected options
    selected_size_option_id = Column(Integer, ForeignKey("product_options.id", ondelete="CASCADE"), nullable=False)
    selected_type_option_id = Column(Integer, ForeignKey("product_options.id", ondelete="CASCADE"), nullable=True)
    
    # Quantity and pricing
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)  # Cached at time of add to cart

    # Relationships
    user = relationship("User")
    photo = relationship("Photo", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    size_option = relationship("ProductOption", foreign_keys=[selected_size_option_id])
    type_option = relationship("ProductOption", foreign_keys=[selected_type_option_id])

    def __repr__(self):
        return f"<CartItem(id={self.id}, product={self.product_id}, quantity={self.quantity})>"


class Order(Base, TimestampMixin):
    """Customer order."""

    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    
    # Customer identification
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    
    # Order items stored as JSON array
    # Format: [{"photo_id": 1, "product_id": "prints", "size": "8x10", "type": "Lustre", "quantity": 2, "unit_price": 30, "photo_src": "..."}, ...]
    items = Column(JSON, nullable=False)
    
    # Financial details
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    shipping = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, default='pending', index=True)
    # Statuses: 'pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'
    
    payment_status = Column(String(50), nullable=False, default='unpaid')
    # Payment statuses: 'unpaid', 'paid', 'refunded'
    
    # Addresses stored as JSON objects
    shipping_address = Column(JSON, nullable=False)
    billing_address = Column(JSON, nullable=False)
    
    # Payment info
    payment_method = Column(String(50), nullable=True)
    
    # Additional info
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User")
    client = relationship("Client", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status})>"

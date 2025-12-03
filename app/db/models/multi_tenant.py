"""Multi-tenant models for domains, subscriptions, and features."""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Integer, Numeric, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base, TimestampMixin


class StudioDomain(Base, TimestampMixin):
    """Custom domains and subdomains for studios."""

    __tablename__ = "studio_domains"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Domain configuration
    domain = Column(String(255), unique=True, nullable=False, index=True)
    subdomain = Column(String(100), unique=True, nullable=True, index=True)
    
    # Status and verification
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False, index=True)
    verification_token = Column(String(255), nullable=True)
    verification_method = Column(String(50), nullable=True)  # 'dns', 'http', 'email'
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    studio = relationship("Studio", back_populates="domains")

    def __repr__(self):
        return f"<StudioDomain(domain={self.domain}, studio_id={self.studio_id}, verified={self.is_verified})>"


class SubscriptionPlan(Base, TimestampMixin):
    """Subscription plans for studios."""

    __tablename__ = "subscription_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Plan details
    name = Column(String(100), nullable=False, unique=True)  # 'starter', 'professional', 'enterprise'
    display_name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Pricing
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2), nullable=True)
    
    # Limits
    max_projects = Column(Integer, nullable=False)
    max_storage_gb = Column(Integer, nullable=False)
    max_users = Column(Integer, nullable=False)
    max_clients = Column(Integer, nullable=True)
    
    # Features (JSONB for PostgreSQL, JSON for SQLite)
    features = Column(JSON, nullable=True)
    # Example: {"custom_domain": true, "white_label": true, "api_access": false}
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_visible = Column(Boolean, default=True)  # Show in pricing page
    
    # Display order
    sort_order = Column(Integer, nullable=False, default=0)

    # Relationships
    subscriptions = relationship("StudioSubscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price=${self.price_monthly}/mo)>"


class StudioSubscription(Base, TimestampMixin):
    """Active subscription for a studio."""

    __tablename__ = "studio_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    
    # Subscription status
    status = Column(String(50), nullable=False, default='trial', index=True)
    # Statuses: 'trial', 'active', 'past_due', 'cancelled', 'expired'
    
    # Trial period
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Billing period
    current_period_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=False)
    
    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Payment integration (Stripe, Razorpay, etc.)
    external_subscription_id = Column(String(255), nullable=True, unique=True)
    external_customer_id = Column(String(255), nullable=True)

    # Relationships
    studio = relationship("Studio", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

    def __repr__(self):
        return f"<StudioSubscription(studio_id={self.studio_id}, status={self.status})>"


class StudioFeature(Base, TimestampMixin):
    """Feature flags for studios (override plan defaults)."""

    __tablename__ = "studio_features"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    feature_key = Column(String(100), nullable=False)
    # Examples: 'custom_domain', 'white_label', 'api_access', 'priority_support'
    
    enabled = Column(Boolean, nullable=False, default=True)
    
    # Optional metadata
    config = Column(JSON, nullable=True)
    # Example: {"rate_limit": 1000, "custom_value": "something"}

    # Relationships
    studio = relationship("Studio", back_populates="features")

    def __repr__(self):
        return f"<StudioFeature(studio_id={self.studio_id}, key={self.feature_key}, enabled={self.enabled})>"


class StudioUsageStats(Base):
    """Track usage statistics for billing and limits."""

    __tablename__ = "studio_usage_stats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Date tracking
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    # Usage metrics
    projects_count = Column(Integer, default=0)
    photos_uploaded = Column(Integer, default=0)
    storage_used_bytes = Column(Integer, default=0)
    api_requests = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    active_clients = Column(Integer, default=0)
    
    # Calculated at
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    studio = relationship("Studio", back_populates="usage_stats")

    def __repr__(self):
        return f"<StudioUsageStats(studio_id={self.studio_id}, period={self.period_start.date()})>"

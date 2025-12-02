"""Aggregate API router for the application."""

from fastapi import APIRouter

# V1 APIs - Kept for compatibility
from app.api.v1 import (
    health,    # Universal health check - keep
    projects,  # Used by frontend - will migrate to V2 later
)

# V2 APIs - Modern architecture (preferred)
from app.routers import auth as auth_v2
from app.routers import upload as upload_v2
from app.routers import comments as comments_v2
from app.routers import photos as photos_v2
from app.routers import clients as clients_v2
from app.routers import products as products_v2
from app.routers import cart as cart_v2
from app.routers import orders as orders_v2
from app.routers import invoices as invoices_v2
from app.routers import service_packages as service_packages_v2
from app.routers import package_types as package_types_v2

from app.routers import files as files_v2
from app.routers import ai_tools as ai_tools_v2
from app.routers import studios as studios_v2
from app.routers import onboarding as onboarding_v2
from app.routers import contracts as contracts_v2
from app.routers import data_rights as data_rights_v2
from app.routers import admin as admin_v2
from app.routers import network_test as network_test_v2
from app.routers import notifications as notifications_v2
from app.routers import studio_users as studio_users_v2
from app.routers import project_members as project_members_v2


api_router = APIRouter()

# ============================================================================
# V1 APIs (Legacy - Being Phased Out)
# ============================================================================
# Keep only essential V1 endpoints for backward compatibility

api_router.include_router(health.router)      # Health check - universal
api_router.include_router(projects.router)    # TODO: Migrate to V2


# ============================================================================
# V2 APIs (Modern - Preferred)
# ============================================================================
# All new development should use V2 APIs

# Authentication & Authorization (V2 router but V1 path for compatibility)
# Note: auth_v2.router already has prefix="/api/auth" defined in routers/auth.py
api_router.include_router(auth_v2.router, tags=["v2-auth"])

# File Management
api_router.include_router(files_v2.router, tags=["files"])  # Serves /uploads/* with CORS
api_router.include_router(upload_v2.router, prefix="/v2/upload", tags=["v2-upload"])
api_router.include_router(photos_v2.router, prefix="/v2/photos", tags=["v2-photos"])
api_router.include_router(comments_v2.router, prefix="/v2/comments", tags=["v2-comments"])
# Compatibility route for frontend still using /api/comments
api_router.include_router(comments_v2.router, prefix="/api/comments", tags=["comments-compat"])

# Client Management
api_router.include_router(clients_v2.router, prefix="/v2/clients", tags=["v2-clients"])

# E-Commerce
api_router.include_router(products_v2.router, prefix="/v2/products", tags=["v2-products"])
api_router.include_router(cart_v2.router, prefix="/v2/cart", tags=["v2-cart"])
api_router.include_router(orders_v2.router, prefix="/v2/orders", tags=["v2-orders"])

# Billing & Services
api_router.include_router(invoices_v2.router, prefix="/v2/invoices", tags=["v2-invoices"])
api_router.include_router(service_packages_v2.router, prefix="/v2/packages", tags=["v2-service-packages"])
api_router.include_router(package_types_v2.router, prefix="/v2/package-types", tags=["v2-package-types"])



# AI Tools
api_router.include_router(ai_tools_v2.router, prefix="/v2", tags=["v2-ai-tools"])

# Multi-Tenant Studio Management
api_router.include_router(studios_v2.router, prefix="/api", tags=["studios"])  # /api/studio/*

# Studio Onboarding
api_router.include_router(onboarding_v2.router, prefix="/api", tags=["onboarding"])  # /api/onboarding/*

# Contracts Management
api_router.include_router(contracts_v2.router, prefix="/v2/contracts", tags=["v2-contracts"])

# Data Subject Rights (DPDPA 2023 Compliance)
api_router.include_router(data_rights_v2.router, prefix="/v2/data-rights", tags=["v2-data-rights"])

# Admin & System Management
api_router.include_router(admin_v2.router, prefix="/v2", tags=["v2-admin"])

# Network Testing (for performance-based network detection)
api_router.include_router(network_test_v2.router, prefix="/api", tags=["network"])

# Notifications (in-app notifications for comments, etc.)
api_router.include_router(notifications_v2.router, tags=["notifications"])

# Studio Users Management (invite, list, update, delete team members)
api_router.include_router(studio_users_v2.router, tags=["studio-users"])

# Project Members Management (team assignment to specific projects)
api_router.include_router(project_members_v2.router, prefix="/v2", tags=["project-members"])


# ============================================================================
# Removed V1 APIs (Cleaned Up - 2025-11-01)
# ============================================================================
# The following V1 APIs have been removed. Use V2 equivalents:
#
# ❌ auth.router              → Use /v2/auth
# ❌ studios.router           → Use /v2/studios (to be created)
# ❌ clients.router           → Use /v2/clients
# ❌ users.router             → Use /v2/users (to be created)
# ❌ project_categories.router → Merge into /v2/projects
# ❌ project_images.router    → Use /v2/photos
# ❌ project_comments.router  → Use /v2/comments
# ❌ stats.router             → Use /v2/analytics (to be created)
# ❌ uploads.router           → Use /v2/upload
# ❌ settings.router          → Use /v2/settings (to be created)
# ❌ batch_actions.router     → Use /v2/batch (to be created)
# ❌ layouts.router           → Use /v2/layouts (to be created)
# ❌ gallery_layouts.router   → Use /v2/layouts
# ❌ invoices.router          → Use /v2/invoices
# ❌ analytics.router         → Use /v2/analytics (to be created)
# ❌ notifications.router     → Use /v2/notifications (to be created)
# ❌ workflows.router         → Use /v2/workflows (to be created)
# ❌ deliveries.router        → Use /v2/deliveries (to be created)
# ❌ ui_customization.router  → Use /v2/ui (to be created)
# ============================================================================

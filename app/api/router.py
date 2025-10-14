"""Aggregate API router for the application."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    batch_actions,
    clients,
    deliveries,
    health,
    invoices,
    layouts,
    notifications,
    project_categories,
    project_comments,
    project_images,
    projects,
    settings,
    stats,
    studios,
    ui_customization,
    uploads,
    users,
    workflows,
)


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(studios.router)
api_router.include_router(clients.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(project_categories.router)
api_router.include_router(project_images.router)
api_router.include_router(project_images.gallery_router)
api_router.include_router(project_comments.router)
api_router.include_router(stats.router)
api_router.include_router(uploads.router)
api_router.include_router(settings.router)
api_router.include_router(batch_actions.router)
# New feature endpoints
api_router.include_router(layouts.router)
api_router.include_router(invoices.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(workflows.router)
api_router.include_router(deliveries.router)
api_router.include_router(ui_customization.router)

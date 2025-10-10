"""Aggregate API router for the application."""

from fastapi import APIRouter

from app.api.v1 import (
    batch_actions,
    health,
    project_categories,
    project_comments,
    project_images,
    projects,
    settings,
    stats,
    studios,
    uploads,
    users,
)


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(studios.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(project_categories.router)
api_router.include_router(project_images.router)
api_router.include_router(project_comments.router)
api_router.include_router(stats.router)
api_router.include_router(uploads.router)
api_router.include_router(settings.router)
api_router.include_router(batch_actions.router)

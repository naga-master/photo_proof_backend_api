"""Permission decorators and dependencies for RBAC."""

from functools import wraps
from typing import Callable, Optional, Union

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.permission_service import PermissionService


class PermissionChecker:
    """Dependency class for checking user permissions."""

    def __init__(self, *required_permissions: str, require_all: bool = True):
        """
        Initialize permission checker.
        
        Args:
            required_permissions: Permission names to check
            require_all: If True, user must have ALL permissions. 
                        If False, user needs ANY one of them.
        """
        self.required_permissions = required_permissions
        self.require_all = require_all

    def __call__(self, current_user: UserRead = Depends(get_current_user)) -> UserRead:
        """Check if user has required permissions."""
        # Studio owner always has all permissions
        if current_user.role == "studio_owner":
            return current_user

        # Get user's effective permissions
        user_permissions = self._get_user_permissions(current_user)

        if self.require_all:
            # Check if user has ALL required permissions
            missing = [p for p in self.required_permissions if not user_permissions.get(p, False)]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing)}"
                )
        else:
            # Check if user has ANY of the required permissions
            has_any = any(user_permissions.get(p, False) for p in self.required_permissions)
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires one of: {', '.join(self.required_permissions)}"
                )

        return current_user

    def _get_user_permissions(self, user: UserRead) -> dict:
        """Get user's permissions, either custom or role defaults."""
        # Check if user has custom permissions in their object
        if hasattr(user, 'permissions') and user.permissions:
            return user.permissions
        
        # Otherwise use role defaults
        return PermissionService.get_default_permissions(user.role)


def require_permission(*permissions: str, require_all: bool = True):
    """
    Dependency factory for permission checking.
    
    Usage:
        @router.get("/projects")
        def list_projects(user: UserRead = Depends(require_permission("canViewProjects"))):
            ...
        
        @router.delete("/projects/{id}")  
        def delete_project(user: UserRead = Depends(require_permission("canDeleteProjects", "canEditProjects", require_all=False))):
            ...
    """
    return PermissionChecker(*permissions, require_all=require_all)


def require_any_permission(*permissions: str):
    """
    Dependency that requires ANY of the specified permissions.
    
    Usage:
        @router.get("/resource")
        def get_resource(user: UserRead = Depends(require_any_permission("canEdit", "canView"))):
            ...
    """
    return PermissionChecker(*permissions, require_all=False)


def require_all_permissions(*permissions: str):
    """
    Dependency that requires ALL of the specified permissions.
    
    Usage:
        @router.post("/resource")
        def create_resource(user: UserRead = Depends(require_all_permissions("canCreate", "canManage"))):
            ...
    """
    return PermissionChecker(*permissions, require_all=True)


# Pre-built permission dependencies for common operations
# Projects
require_view_projects = require_permission("canViewProjects")
require_create_projects = require_permission("canCreateProjects")
require_edit_projects = require_permission("canEditProjects")
require_delete_projects = require_permission("canDeleteProjects")

# Clients
require_view_clients = require_permission("canViewClients")
require_create_clients = require_permission("canCreateClients")
require_edit_clients = require_permission("canEditClients")
require_delete_clients = require_permission("canDeleteClients")

# Photos
require_upload_photos = require_permission("canUploadPhotos")
require_edit_photos = require_permission("canEditPhotos")
require_delete_photos = require_permission("canDeletePhotos")

# Invoices
require_view_invoices = require_permission("canViewInvoices")
require_create_invoices = require_permission("canCreateInvoices")
require_edit_invoices = require_permission("canEditInvoices")
require_delete_invoices = require_permission("canDeleteInvoices")

# Analytics
require_view_analytics = require_permission("canViewAnalytics")

# Settings
require_manage_settings = require_permission("canManageSettings")
require_manage_users = require_permission("canManageUsers")
require_manage_branding = require_permission("canManageBranding")

# Services & Packages
require_manage_services = require_permission("canManageServices")
require_manage_packages = require_permission("canManagePackages")

# Communication
require_send_notifications = require_permission("canSendNotifications")
require_manage_communication = require_permission("canManageCommunication")

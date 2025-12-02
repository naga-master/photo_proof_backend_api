"""Permission service for RBAC (Role-Based Access Control)."""

from typing import Any, Optional

# All available permissions in the system
ALL_PERMISSIONS = [
    # Project Management
    "canCreateProjects",
    "canEditProjects",
    "canDeleteProjects",
    "canViewProjects",
    # Client Management
    "canCreateClients",
    "canEditClients",
    "canDeleteClients",
    "canViewClients",
    # Financial
    "canCreateInvoices",
    "canEditInvoices",
    "canDeleteInvoices",
    "canViewInvoices",
    "canViewAnalytics",
    # Content Management
    "canUploadPhotos",
    "canEditPhotos",
    "canDeletePhotos",
    # Contracts
    "canViewContracts",
    "canCreateContracts",
    "canEditContracts",
    "canDeleteContracts",
    # Services & Packages
    "canManageServices",
    "canManagePackages",
    # Studio Settings
    "canManageSettings",
    "canManageUsers",
    "canManageBranding",
    # Communication
    "canSendNotifications",
    "canManageCommunication",
    # Advanced / Fine-grained
    "canDownloadOriginals",
    "canManageComments",
    "canApplyDiscounts",
    "canViewRevenue",
    "canShareExternally",
]

# Default permissions per role
ROLE_DEFAULTS = {
    "studio_owner": {
        # Full access to everything
        "canCreateProjects": True,
        "canEditProjects": True,
        "canDeleteProjects": True,
        "canViewProjects": True,
        "canCreateClients": True,
        "canEditClients": True,
        "canDeleteClients": True,
        "canViewClients": True,
        "canCreateInvoices": True,
        "canEditInvoices": True,
        "canDeleteInvoices": True,
        "canViewInvoices": True,
        "canViewAnalytics": True,
        "canUploadPhotos": True,
        "canEditPhotos": True,
        "canDeletePhotos": True,
        "canViewContracts": True,
        "canCreateContracts": True,
        "canEditContracts": True,
        "canDeleteContracts": True,
        "canManageServices": True,
        "canManagePackages": True,
        "canManageSettings": True,
        "canManageUsers": True,
        "canManageBranding": True,
        "canSendNotifications": True,
        "canManageCommunication": True,
        "canDownloadOriginals": True,
        "canManageComments": True,
        "canApplyDiscounts": True,
        "canViewRevenue": True,
        "canShareExternally": True,
    },
    "studio_admin": {
        # Admin: Full access except some owner-only settings
        "canCreateProjects": True,
        "canEditProjects": True,
        "canDeleteProjects": True,
        "canViewProjects": True,
        "canCreateClients": True,
        "canEditClients": True,
        "canDeleteClients": True,
        "canViewClients": True,
        "canCreateInvoices": True,
        "canEditInvoices": True,
        "canDeleteInvoices": True,
        "canViewInvoices": True,
        "canViewAnalytics": True,
        "canUploadPhotos": True,
        "canEditPhotos": True,
        "canDeletePhotos": True,
        "canViewContracts": True,
        "canCreateContracts": True,
        "canEditContracts": True,
        "canDeleteContracts": True,
        "canManageServices": True,
        "canManagePackages": True,
        "canManageSettings": True,
        "canManageUsers": True,
        "canManageBranding": True,
        "canSendNotifications": True,
        "canManageCommunication": True,
        "canDownloadOriginals": True,
        "canManageComments": True,
        "canApplyDiscounts": True,
        "canViewRevenue": True,
        "canShareExternally": True,
    },
    "studio_photographer": {
        # Photographer/Editor: Content focused, limited admin
        "canCreateProjects": False,
        "canEditProjects": True,
        "canDeleteProjects": False,
        "canViewProjects": True,
        "canCreateClients": False,
        "canEditClients": False,
        "canDeleteClients": False,
        "canViewClients": True,
        "canCreateInvoices": False,
        "canEditInvoices": False,
        "canDeleteInvoices": False,
        "canViewInvoices": False,
        "canViewAnalytics": True,
        "canUploadPhotos": True,
        "canEditPhotos": True,
        "canDeletePhotos": False,
        "canViewContracts": False,
        "canCreateContracts": False,
        "canEditContracts": False,
        "canDeleteContracts": False,
        "canManageServices": False,
        "canManagePackages": False,
        "canManageSettings": False,
        "canManageUsers": False,
        "canManageBranding": False,
        "canSendNotifications": False,
        "canManageCommunication": False,
        "canDownloadOriginals": True,
        "canManageComments": False,
        "canApplyDiscounts": False,
        "canViewRevenue": False,
        "canShareExternally": True,
    },
    "client": {
        # Client: View only, very limited
        "canCreateProjects": False,
        "canEditProjects": False,
        "canDeleteProjects": False,
        "canViewProjects": True,
        "canCreateClients": False,
        "canEditClients": False,
        "canDeleteClients": False,
        "canViewClients": False,
        "canCreateInvoices": False,
        "canEditInvoices": False,
        "canDeleteInvoices": False,
        "canViewInvoices": True,
        "canViewAnalytics": False,
        "canUploadPhotos": False,
        "canEditPhotos": False,
        "canDeletePhotos": False,
        "canViewContracts": True,
        "canCreateContracts": False,
        "canEditContracts": False,
        "canDeleteContracts": False,
        "canManageServices": False,
        "canManagePackages": False,
        "canManageSettings": False,
        "canManageUsers": False,
        "canManageBranding": False,
        "canSendNotifications": False,
        "canManageCommunication": False,
        "canDownloadOriginals": False,
        "canManageComments": False,
        "canApplyDiscounts": False,
        "canViewRevenue": False,
        "canShareExternally": False,
    },
}


class PermissionService:
    """Service for managing user permissions."""

    @staticmethod
    def get_default_permissions(role: str) -> dict:
        """Get default permissions for a role."""
        return ROLE_DEFAULTS.get(role, ROLE_DEFAULTS.get("client", {})).copy()

    @staticmethod
    def get_user_permissions(user: Any) -> dict:
        """
        Get effective permissions for a user.
        If user has custom permissions, use those DIRECTLY (no merge).
        Otherwise, use role defaults.
        """
        # Safely get permissions attribute (may not exist on older model instances)
        user_perms = getattr(user, 'permissions', None)
        
        # If user has custom permissions stored, use them directly
        # Don't merge with defaults - admin explicitly set these permissions
        if user_perms and isinstance(user_perms, dict) and len(user_perms) > 0:
            return user_perms
        
        # Only fall back to role defaults if NO custom permissions exist
        return PermissionService.get_default_permissions(user.role)

    @staticmethod
    def has_permission(user: Any, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Studio owner always has all permissions
        if user.role == "studio_owner":
            return True
        
        permissions = PermissionService.get_user_permissions(user)
        return permissions.get(permission, False)

    @staticmethod
    def has_any_permission(user: Any, permissions: list[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(PermissionService.has_permission(user, p) for p in permissions)

    @staticmethod
    def has_all_permissions(user: Any, permissions: list[str]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(PermissionService.has_permission(user, p) for p in permissions)

    @staticmethod
    def validate_permissions(permissions: dict) -> tuple[bool, Optional[str]]:
        """
        Validate a permissions object.
        Returns (is_valid, error_message).
        """
        if not isinstance(permissions, dict):
            return False, "Permissions must be a dictionary"
        
        for key, value in permissions.items():
            if key not in ALL_PERMISSIONS:
                return False, f"Unknown permission: {key}"
            if not isinstance(value, bool):
                return False, f"Permission {key} must be a boolean"
        
        return True, None

    @staticmethod
    def normalize_permissions(permissions: dict, role: str) -> dict:
        """
        Normalize permissions by filling in missing values with role defaults.
        """
        defaults = PermissionService.get_default_permissions(role)
        if permissions:
            defaults.update(permissions)
        return defaults

    @staticmethod
    def get_all_permissions() -> list[str]:
        """Get list of all available permission names."""
        return ALL_PERMISSIONS.copy()

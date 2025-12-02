# Backend Implementation

## File Structure

```
app/
├── core/
│   └── permissions.py      # Permission decorators and dependencies
├── services/
│   └── permission_service.py  # Core permission logic
└── routers/
    ├── auth.py             # Returns permissions in login response
    ├── clients.py          # Uses permission decorators
    ├── invoices.py         # Uses permission decorators
    └── ...
```

## PermissionService

**Location:** `app/services/permission_service.py`

Core service for permission logic.

### Constants

```python
# All available permissions
ALL_PERMISSIONS = [
    "canCreateProjects", "canEditProjects", "canDeleteProjects", "canViewProjects",
    "canCreateClients", "canEditClients", "canDeleteClients", "canViewClients",
    "canCreateInvoices", "canEditInvoices", "canDeleteInvoices", "canViewInvoices",
    "canViewAnalytics",
    "canUploadPhotos", "canEditPhotos", "canDeletePhotos",
    "canManageServices", "canManagePackages",
    "canManageSettings", "canManageUsers", "canManageBranding",
    "canSendNotifications", "canManageCommunication",
]

# Default permissions per role
ROLE_DEFAULTS = {
    "studio_owner": { ... },    # All true
    "studio_admin": { ... },    # All true
    "studio_photographer": { ... },  # Limited
    "client": { ... },          # View only
}
```

### Methods

```python
class PermissionService:
    @staticmethod
    def get_default_permissions(role: str) -> dict:
        """Get default permissions for a role."""
        return ROLE_DEFAULTS.get(role, ROLE_DEFAULTS["client"]).copy()

    @staticmethod
    def get_user_permissions(user: Any) -> dict:
        """
        Get effective permissions for a user.
        - If custom permissions exist, use them directly (no merge)
        - Otherwise, use role defaults
        """
        user_perms = getattr(user, 'permissions', None)
        
        if user_perms and isinstance(user_perms, dict) and len(user_perms) > 0:
            return user_perms  # Custom permissions, no merge
        
        return PermissionService.get_default_permissions(user.role)

    @staticmethod
    def has_permission(user: Any, permission: str) -> bool:
        """Check if user has a specific permission."""
        if user.role == "studio_owner":
            return True  # Owner bypass
        
        permissions = PermissionService.get_user_permissions(user)
        return permissions.get(permission, False)

    @staticmethod
    def validate_permissions(permissions: dict) -> tuple[bool, Optional[str]]:
        """Validate a permissions object."""
        for key, value in permissions.items():
            if key not in ALL_PERMISSIONS:
                return False, f"Unknown permission: {key}"
            if not isinstance(value, bool):
                return False, f"Permission {key} must be boolean"
        return True, None
```

## PermissionChecker

**Location:** `app/core/permissions.py`

FastAPI dependency for endpoint protection.

### Class Definition

```python
class PermissionChecker:
    def __init__(self, *required_permissions: str, require_all: bool = True):
        """
        Args:
            required_permissions: Permission names to check
            require_all: If True, need ALL permissions. If False, need ANY.
        """
        self.required_permissions = required_permissions
        self.require_all = require_all

    def __call__(self, current_user: UserRead = Depends(get_current_user)) -> UserRead:
        # Studio owner bypass
        if current_user.role == "studio_owner":
            return current_user

        user_permissions = self._get_user_permissions(current_user)

        if self.require_all:
            missing = [p for p in self.required_permissions 
                      if not user_permissions.get(p, False)]
            if missing:
                raise HTTPException(403, f"Missing: {', '.join(missing)}")
        else:
            has_any = any(user_permissions.get(p, False) 
                         for p in self.required_permissions)
            if not has_any:
                raise HTTPException(403, f"Requires one of: {', '.join(self.required_permissions)}")

        return current_user
```

### Factory Functions

```python
def require_permission(*permissions: str, require_all: bool = True):
    """Create a permission checker dependency."""
    return PermissionChecker(*permissions, require_all=require_all)

def require_any_permission(*permissions: str):
    """Require ANY of the specified permissions."""
    return PermissionChecker(*permissions, require_all=False)

def require_all_permissions(*permissions: str):
    """Require ALL of the specified permissions."""
    return PermissionChecker(*permissions, require_all=True)
```

### Pre-built Dependencies

```python
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
```

## Usage in Routers

### Basic Usage

```python
from app.core.permissions import require_view_clients, require_create_clients

@router.get("/clients")
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_clients),  # Permission check
):
    # Only users with canViewClients can access
    return db.query(Client).filter(Client.studio_id == current_user.studio_id).all()

@router.post("/clients")
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_clients),  # Permission check
):
    # Only users with canCreateClients can access
    ...
```

### Multiple Permissions (ANY)

```python
from app.core.permissions import require_any_permission

@router.get("/reports")
def get_reports(
    current_user: User = Depends(require_any_permission("canViewAnalytics", "canManageSettings")),
):
    # Users with EITHER permission can access
    ...
```

### Multiple Permissions (ALL)

```python
from app.core.permissions import require_all_permissions

@router.delete("/studio")
def delete_studio(
    current_user: User = Depends(require_all_permissions("canManageSettings", "canManageUsers")),
):
    # Users must have BOTH permissions
    ...
```

### Custom Permission Check

```python
from app.core.permissions import require_permission

@router.patch("/projects/{id}/archive")
def archive_project(
    current_user: User = Depends(require_permission("canEditProjects", "canDeleteProjects", require_all=False)),
):
    # Users with canEditProjects OR canDeleteProjects can archive
    ...
```

## Auth Router Integration

**Location:** `app/routers/auth.py`

Permissions are included in login response:

```python
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user, access_token = AuthService.authenticate(...)
    
    # Get effective permissions
    permissions = PermissionService.get_user_permissions(user)
    
    # Include in JWT refresh token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "studio_id": user.studio_id,
        "permissions": permissions,  # Include permissions
    }
    
    # Include in response
    user_response = UserResponse.model_validate(user)
    user_response.permissions = permissions
    
    return LoginResponse(token=access_token, user=user_response)
```

## Adding New Permissions

1. Add to `ALL_PERMISSIONS` list in `permission_service.py`
2. Add to each role in `ROLE_DEFAULTS`
3. Create pre-built dependency in `permissions.py`
4. Update frontend `ROLE_DEFAULT_PERMISSIONS`
5. Apply to relevant endpoints

```python
# 1. permission_service.py
ALL_PERMISSIONS = [
    ...
    "canExportData",  # New permission
]

ROLE_DEFAULTS = {
    "studio_owner": { ..., "canExportData": True },
    "studio_admin": { ..., "canExportData": True },
    "studio_photographer": { ..., "canExportData": False },
    "client": { ..., "canExportData": False },
}

# 2. permissions.py
require_export_data = require_permission("canExportData")

# 3. Router
@router.get("/export")
def export_data(current_user: User = Depends(require_export_data)):
    ...
```

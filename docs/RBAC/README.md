# Role-Based Access Control (RBAC) System

## Overview

Photo Proof implements a **two-layer permission system** that combines:

1. **Studio Features (Global)** - Feature flags from admin app / subscription plan
2. **User Permissions (RBAC)** - Per-user granular permissions

This architecture allows:
- Super admin to enable/disable features for entire studios
- Studio owners to customize permissions per team member
- Granular control over who can do what

## Documentation Structure

- [Architecture](./architecture.md) - System design and data flow
- [Permissions](./permissions.md) - Complete permission reference
- [Backend Implementation](./backend.md) - API and decorators
- [Frontend Implementation](./frontend.md) - React components and hooks
- [Database Schema](./database.md) - Data storage details
- [Usage Guide](./usage-guide.md) - How to use the system

## Quick Start

### Protecting a Backend Endpoint

```python
from app.core.permissions import require_view_clients

@router.get("/clients")
def list_clients(
    current_user: User = Depends(require_view_clients)
):
    # Only users with canViewClients permission can access
    ...
```

### Protecting a Frontend Button

```tsx
import { CanCreate } from '../components/AccessGate';

function ClientsPage() {
    return (
        <CanCreate module="clients">
            <button>Add New Client</button>
        </CanCreate>
    );
}
```

### Checking Permissions in Code

```tsx
import { useAccessControl } from '../contexts/AccessControlContext';

function MyComponent() {
    const { hasPermission, canAccess } = useAccessControl();
    
    if (hasPermission('canEditClients')) {
        // Show edit functionality
    }
    
    if (canAccess('clients_module', 'canDeleteClients')) {
        // Feature enabled AND user has permission
    }
}
```

## Roles

| Role | Description | Default Permissions |
|------|-------------|---------------------|
| `studio_owner` | Full access to everything | All permissions |
| `studio_admin` | Administrative access | Most permissions, some restrictions |
| `studio_photographer` | Content-focused | Upload, edit photos, view projects |
| `client` | External client | View projects, view invoices |

## Key Design Decisions

1. **No Merge Policy**: When custom permissions are set, they replace role defaults entirely. Missing permissions = `false`.

2. **Studio Owner Bypass**: `studio_owner` role always has all permissions (hardcoded bypass).

3. **Dual Layer**: Features can be disabled at studio level, permissions at user level.

4. **Frontend + Backend**: Both must enforce permissions for security.

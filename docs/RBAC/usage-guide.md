# RBAC Usage Guide

## For Developers

### Adding Permission Protection to a New Endpoint

1. **Import the permission checker:**

```python
from app.core.permissions import require_view_clients
# or
from app.core.permissions import require_permission
```

2. **Add as dependency:**

```python
@router.get("/my-endpoint")
def my_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_view_clients),  # Add this
):
    # Endpoint code
    ...
```

3. **For custom permission combinations:**

```python
from app.core.permissions import require_permission, require_any_permission

# Require specific permission
@router.post("/custom")
def custom_endpoint(
    current_user: User = Depends(require_permission("canCustomAction")),
):
    ...

# Require any of multiple permissions
@router.get("/flexible")
def flexible_endpoint(
    current_user: User = Depends(require_any_permission("canView", "canEdit")),
):
    ...
```

### Adding Permission Protection to Frontend UI

1. **For buttons/actions:**

```tsx
import { CanCreate, CanEdit, CanDelete } from '../components/AccessGate';

// Hide button if no permission
<CanCreate module="clients">
    <button>Add Client</button>
</CanCreate>

<CanEdit module="projects">
    <button>Edit</button>
</CanEdit>

<CanDelete module="invoices">
    <button>Delete</button>
</CanDelete>
```

2. **For conditional logic:**

```tsx
import { useAccessControl } from '../contexts/AccessControlContext';

function MyComponent() {
    const { hasPermission } = useAccessControl();
    
    return (
        <div>
            {hasPermission('canEditClients') && (
                <EditPanel />
            )}
        </div>
    );
}
```

3. **For navigation:**

```tsx
const navItems = [
    {
        name: 'My Feature',
        path: '/studio/my-feature',
        permission: 'canAccessMyFeature',  // Add permission requirement
    },
];
```

### Adding a New Permission

1. **Backend - permission_service.py:**

```python
ALL_PERMISSIONS = [
    ...
    "canNewPermission",  # Add here
]

ROLE_DEFAULTS = {
    "studio_owner": { ..., "canNewPermission": True },
    "studio_admin": { ..., "canNewPermission": True },
    "studio_photographer": { ..., "canNewPermission": False },
    "client": { ..., "canNewPermission": False },
}
```

2. **Backend - permissions.py:**

```python
require_new_permission = require_permission("canNewPermission")
```

3. **Frontend - AccessControlContext.tsx:**

```typescript
const ROLE_DEFAULT_PERMISSIONS = {
    studio_owner: { ..., canNewPermission: true },
    studio_admin: { ..., canNewPermission: true },
    studio_photographer: { ..., canNewPermission: false },
    client: { ..., canNewPermission: false },
};
```

4. **Frontend - AccessGate.tsx (if needed):**

```tsx
// Add to CanManage or create new convenience component
export const CanNewAction: React.FC<Props> = ({ children }) => (
    <AccessGate permission="canNewPermission">
        {children}
    </AccessGate>
);
```

---

## For Studio Owners/Admins

### Managing Team Permissions

1. Go to **Settings → Studio Users**
2. Click **Edit** on a team member
3. Toggle individual permissions on/off
4. Click **Save**

### Understanding Permission Badges

In the user list, badges show key permissions:

| Badge | Permission |
|-------|------------|
| Users | Can manage team members |
| Settings | Can access studio settings |
| Clients | Can view clients |
| Projects | Can view projects |
| Upload | Can upload photos |
| Edit | Can edit photos |
| Invoices | Can view invoices |
| Analytics | Can view analytics |

### Common Permission Configurations

**Second Shooter / Assistant:**
- ✓ View Projects
- ✓ Upload Photos
- ✓ Edit Photos
- ✗ Everything else

**Office Manager:**
- ✓ View/Create/Edit Clients
- ✓ View/Create/Edit Invoices
- ✓ View Analytics
- ✗ Photo editing
- ✗ Settings

**Lead Photographer:**
- ✓ All project permissions
- ✓ All photo permissions
- ✓ View clients (no edit)
- ✗ Financial access
- ✗ Settings

---

## Troubleshooting

### User Can't See a Page

1. Check if the user has the required **view** permission
2. Check if the **feature** is enabled for the studio
3. Verify the user's role and custom permissions in Settings

### Permission Changes Not Taking Effect

1. Have the user **log out and log back in**
2. Clear browser cache/sessionStorage
3. Check that the save was successful (no API errors)

### Studio Owner Can't Edit Permissions

- Only `studio_owner` and users with `canManageUsers` can edit permissions
- Check if the logged-in user has this permission

### API Returns 403 Forbidden

The endpoint requires a permission the user doesn't have:

```json
{
    "detail": "Missing required permissions: canEditClients"
}
```

Solution: Grant the required permission or use a different user.

### Debug Permission Flow

**Backend logging (auth.py):**
```
[AUTH DEBUG] User permissions from DB: {...}
[AUTH DEBUG] Effective permissions: {...}
[AUTH DEBUG] canViewClients: true
```

**Frontend logging (AccessControlContext.tsx):**
```
[AccessControl] getUserPermissions called for: {...}
[AccessControl] Using custom permissions (with false base): {...}
[AccessControl] hasPermission(canViewClients): true
```

---

## Security Best Practices

1. **Always protect both frontend AND backend**
   - Frontend: Hide UI elements
   - Backend: Enforce with dependencies

2. **Use pre-built dependencies when available**
   ```python
   # Good
   current_user = Depends(require_view_clients)
   
   # Avoid custom checks when not needed
   ```

3. **Test with different roles**
   - Create test users for each role
   - Verify UI and API access

4. **Audit permission changes**
   - Log when permissions are modified
   - Track who made changes

5. **Don't trust frontend-only checks**
   - Attackers can bypass frontend
   - Backend enforcement is mandatory

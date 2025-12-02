# RBAC Architecture

## Two-Layer Permission System

```
┌─────────────────────────────────────────────────────────────┐
│                      ACCESS DECISION                         │
│                                                              │
│   User Action → Feature Enabled? → Has Permission? → Allow  │
│                         ↓                  ↓                 │
│                      Layer 1           Layer 2               │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: Studio Features (Global)

Studio features are controlled at the subscription/admin level:

```typescript
const DEFAULT_FEATURES = {
    clients_module: true,
    projects_module: true,
    invoices_module: true,
    analytics_module: true,
    settings_module: true,
    services_module: true,
    contracts_module: true,
    notifications_module: true,
    upload_module: true,
};
```

Features can be:
- Disabled by super admin
- Tied to subscription plans
- Used for A/B testing

### Layer 2: User Permissions (RBAC)

Individual user permissions stored in the database:

```json
{
    "canViewClients": true,
    "canCreateClients": false,
    "canEditClients": true,
    "canDeleteClients": false,
    "canViewProjects": true,
    // ... more permissions
}
```

## Data Flow

### Login Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────►│  /login  │────►│ DB Query │────►│ Response │
│  Login   │     │   API    │     │  + Perms │     │ + Perms  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │
                      ▼
              ┌──────────────┐
              │ JWT Token    │
              │ includes:    │
              │ - user_id    │
              │ - role       │
              │ - studio_id  │
              │ - permissions│
              └──────────────┘
```

### Permission Check Flow (Backend)

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│ Incoming │────►│ JWT Auth │────►│ Permission   │────►│ Endpoint │
│ Request  │     │ Decode   │     │ Checker      │     │ Handler  │
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │ Is Owner?    │──Yes──► Allow
                                 │              │
                                 │ Has Custom   │
                                 │ Permissions? │──Yes──► Check Custom
                                 │              │
                                 │ Use Role     │──No───► Check Defaults
                                 │ Defaults     │
                                 └──────────────┘
```

### Permission Check Flow (Frontend)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ AccessControl│────►│ useAccess    │────►│ Render       │
│ Provider     │     │ Control      │     │ Decision     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │
       │                    ▼
       │             ┌──────────────┐
       │             │ AccessGate   │
       │             │ Component    │
       │             └──────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ State:                               │
│ - features: { clients_module: true } │
│ - permissions: { canViewClients: T } │
│ - isLoading: false                   │
└──────────────────────────────────────┘
```

## Permission Resolution Algorithm

```python
def get_user_permissions(user):
    # 1. Studio owner always has all permissions
    if user.role == "studio_owner":
        return ALL_PERMISSIONS_TRUE
    
    # 2. Check for custom permissions in database
    if user.permissions and len(user.permissions) > 0:
        # Use stored permissions directly
        # Missing permissions = FALSE (not merged with defaults)
        return user.permissions
    
    # 3. Fall back to role defaults
    return ROLE_DEFAULTS[user.role]
```

### Why No Merge?

When an admin sets custom permissions, we use them **exactly as stored**:

```
WRONG (merge approach):
  Role defaults: { canViewClients: true, canEditClients: true }
  Custom perms:  { canEditClients: false }
  Result:        { canViewClients: true, canEditClients: false }  ← Unexpected!

RIGHT (no merge):
  Role defaults: { canViewClients: true, canEditClients: true }
  Custom perms:  { canEditClients: false }
  Result:        { canViewClients: false, canEditClients: false } ← Missing = false
```

This ensures:
- Admin has full control over user permissions
- No unexpected permission inheritance
- Clear, predictable behavior

## Component Responsibilities

### Backend

| Component | File | Responsibility |
|-----------|------|----------------|
| PermissionService | `services/permission_service.py` | Core permission logic |
| PermissionChecker | `core/permissions.py` | FastAPI dependency |
| Pre-built Checkers | `core/permissions.py` | `require_view_clients`, etc. |
| Auth Router | `routers/auth.py` | Include permissions in response |

### Frontend

| Component | File | Responsibility |
|-----------|------|----------------|
| AccessControlProvider | `contexts/AccessControlContext.tsx` | Global state |
| useAccessControl | `contexts/AccessControlContext.tsx` | Hook for components |
| AccessGate | `components/AccessGate.tsx` | Conditional rendering |
| CanView/Create/Edit/Delete | `components/AccessGate.tsx` | Convenience wrappers |

### Database

| Table | Column | Type | Description |
|-------|--------|------|-------------|
| users | permissions | JSONB | Custom permissions object |
| users | role | VARCHAR | Role for default permissions |

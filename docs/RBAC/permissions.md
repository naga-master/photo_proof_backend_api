# Permissions Reference

## Complete Permission List

### Project Management

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canViewProjects` | View project list and details | ✓ | ✓ | ✓ | ✓ |
| `canCreateProjects` | Create new projects | ✓ | ✓ | ✗ | ✗ |
| `canEditProjects` | Edit project details | ✓ | ✓ | ✓ | ✗ |
| `canDeleteProjects` | Delete projects | ✓ | ✓ | ✗ | ✗ |

### Client Management

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canViewClients` | View client list and details | ✓ | ✓ | ✓ | ✗ |
| `canCreateClients` | Add new clients | ✓ | ✓ | ✗ | ✗ |
| `canEditClients` | Edit client information | ✓ | ✓ | ✗ | ✗ |
| `canDeleteClients` | Delete clients | ✓ | ✓ | ✗ | ✗ |

### Photo Management

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canUploadPhotos` | Upload photos to projects | ✓ | ✓ | ✓ | ✗ |
| `canEditPhotos` | Edit photo metadata, crop, etc. | ✓ | ✓ | ✓ | ✗ |
| `canDeletePhotos` | Delete photos | ✓ | ✓ | ✗ | ✗ |

### Financial

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canViewInvoices` | View invoice list and details | ✓ | ✓ | ✗ | ✓ |
| `canCreateInvoices` | Create new invoices | ✓ | ✓ | ✗ | ✗ |
| `canEditInvoices` | Edit invoice details | ✓ | ✓ | ✗ | ✗ |
| `canDeleteInvoices` | Delete invoices | ✓ | ✓ | ✗ | ✗ |
| `canViewAnalytics` | View analytics dashboard | ✓ | ✓ | ✓ | ✗ |

### Contracts

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canViewContracts` | View contract list and details | ✓ | ✓ | ✗ | ✓ |
| `canCreateContracts` | Create new contracts and templates | ✓ | ✓ | ✗ | ✗ |
| `canEditContracts` | Edit contracts and templates | ✓ | ✓ | ✗ | ✗ |
| `canDeleteContracts` | Delete contracts | ✓ | ✓ | ✗ | ✗ |

### Studio Settings

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canManageSettings` | Access studio settings | ✓ | ✓ | ✗ | ✗ |
| `canManageUsers` | Invite/edit/remove team members | ✓ | ✓ | ✗ | ✗ |
| `canManageBranding` | Edit logo, colors, templates | ✓ | ✓ | ✗ | ✗ |

### Services & Packages

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canManageServices` | Create/edit service offerings | ✓ | ✓ | ✗ | ✗ |
| `canManagePackages` | Manage package types | ✓ | ✓ | ✗ | ✗ |

### Communication

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canSendNotifications` | Send notifications to clients | ✓ | ✓ | ✗ | ✗ |
| `canManageCommunication` | Manage email templates, settings | ✓ | ✓ | ✗ | ✗ |

### Advanced / Fine-Grained

| Permission | Description | Owner | Admin | Photographer | Client |
|------------|-------------|:-----:|:-----:|:------------:|:------:|
| `canDownloadOriginals` | Download full-resolution photos | ✓ | ✓ | ✓ | ✗ |
| `canManageComments` | Delete/moderate any comment | ✓ | ✓ | ✗ | ✗ |
| `canApplyDiscounts` | Apply discounts to invoices | ✓ | ✓ | ✗ | ✗ |
| `canViewRevenue` | See revenue/financial metrics | ✓ | ✓ | ✗ | ✗ |
| `canShareExternally` | Generate public share links | ✓ | ✓ | ✓ | ✗ |

## Role Defaults

### Studio Owner (`studio_owner`)

Full access to everything. This role has a hardcoded bypass - all permission checks return `true`.

```python
# In PermissionChecker
if current_user.role == "studio_owner":
    return current_user  # Always allowed
```

### Studio Admin (`studio_admin`)

Near-full access, designed for trusted team members - all permissions enabled by default.

### Studio Photographer (`studio_photographer`)

Content-focused with limited administrative access:

| Category | Allowed | Denied |
|----------|---------|--------|
| Projects | View, Edit | Create, Delete |
| Clients | View | Create, Edit, Delete |
| Photos | Upload, Edit | Delete |
| Financial | Analytics | Invoices |
| Settings | None | All |

### Client (`client`)

External clients with view-only access:

| Category | Allowed | Denied |
|----------|---------|--------|
| Projects | View | All others |
| Invoices | View | All others |
| Everything else | None | All |

## Custom Permissions

When a studio owner/admin assigns custom permissions:

1. Custom permissions stored in `users.permissions` (JSONB)
2. Role defaults are **completely ignored**
3. Missing permissions = `false`

### Example

```json
// User role: studio_photographer
// Stored in DB:
{
    "canViewProjects": true,
    "canEditProjects": true,
    "canViewClients": false
}

// Effective permissions:
// canViewProjects → true (from custom)
// canEditProjects → true (from custom)
// canViewClients → false (from custom)
// canUploadPhotos → false (NOT in custom = false)
// All others → false
```

## Feature Flags (Layer 1)

Features can be disabled at studio level:

| Feature | Controls |
|---------|----------|
| `clients_module` | Client management section |
| `projects_module` | Project management section |
| `invoices_module` | Invoice/billing section |
| `analytics_module` | Analytics dashboard |
| `settings_module` | Studio settings |
| `services_module` | Service offerings |
| `contracts_module` | Contract management |
| `notifications_module` | Notification system |
| `upload_module` | Photo upload capability |

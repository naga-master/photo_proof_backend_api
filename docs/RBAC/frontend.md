# Frontend Implementation

## File Structure

```
src/
├── contexts/
│   └── AccessControlContext.tsx   # Global permission state
├── components/
│   ├── AccessGate.tsx             # Conditional rendering component
│   └── studio/
│       ├── StudioSidebar.tsx      # Filtered navigation
│       ├── ClientsPage.tsx        # Permission-gated buttons
│       └── ...
└── index.tsx                      # Provider wrapper
```

## AccessControlContext

**Location:** `contexts/AccessControlContext.tsx`

Provides global permission state and checking functions.

### Context Type

```typescript
interface AccessControlContextType {
    // Layer 1: Studio Features
    features: Record<string, boolean>;
    isFeatureEnabled: (feature: string) => boolean;
    
    // Layer 2: User Permissions
    permissions: Record<string, boolean>;
    hasPermission: (permission: string) => boolean;
    
    // Combined check
    canAccess: (feature: string, permission?: string) => boolean;
    
    // Loading state
    isLoading: boolean;
    
    // Refresh permissions from API
    refreshPermissions: () => Promise<void>;
}
```

### Provider Setup

```tsx
// index.tsx
import { AccessControlProvider } from './contexts/AccessControlContext';

ReactDOM.render(
    <AuthProvider>
        <AccessControlProvider>
            <App />
        </AccessControlProvider>
    </AuthProvider>,
    document.getElementById('root')
);
```

### Permission Resolution

```typescript
const getUserPermissions = useCallback(() => {
    if (!user) return {};

    const roleDefaults = ROLE_DEFAULT_PERMISSIONS[user.role];

    // Custom permissions override everything
    if (user.permissions && Object.keys(user.permissions).length > 0) {
        // Start with all false, overlay stored permissions
        const allFalseBase: Record<string, boolean> = {};
        Object.keys(roleDefaults).forEach(key => {
            allFalseBase[key] = false;
        });
        return { ...allFalseBase, ...user.permissions };
    }

    // Use role defaults only when no custom permissions
    return roleDefaults;
}, [user]);
```

### Usage Hook

```tsx
import { useAccessControl } from '../contexts/AccessControlContext';

function MyComponent() {
    const { 
        hasPermission, 
        isFeatureEnabled, 
        canAccess,
        isLoading 
    } = useAccessControl();

    if (isLoading) return <Spinner />;

    // Check single permission
    if (hasPermission('canEditClients')) {
        // Show edit button
    }

    // Check feature flag
    if (isFeatureEnabled('invoices_module')) {
        // Show invoices section
    }

    // Combined check
    if (canAccess('clients_module', 'canDeleteClients')) {
        // Feature enabled AND user has permission
    }
}
```

## AccessGate Component

**Location:** `components/AccessGate.tsx`

Conditionally renders children based on permissions.

### Props

```typescript
interface AccessGateProps {
    children: ReactNode;
    feature?: string;           // Feature flag to check
    permission?: string;        // Single permission to check
    anyPermission?: string[];   // User needs ANY of these
    allPermissions?: string[];  // User needs ALL of these
    fallback?: ReactNode;       // What to show if denied
    showFallback?: boolean;     // Show fallback vs hide completely
}
```

### Basic Usage

```tsx
import { AccessGate } from '../components/AccessGate';

// Hide if no permission
<AccessGate permission="canEditClients">
    <EditButton />
</AccessGate>

// Check feature + permission
<AccessGate feature="clients_module" permission="canCreateClients">
    <AddClientButton />
</AccessGate>

// Show fallback if denied
<AccessGate 
    permission="canDeleteProjects" 
    fallback={<DisabledButton />}
    showFallback
>
    <DeleteButton />
</AccessGate>

// ANY of multiple permissions
<AccessGate anyPermission={["canEditClients", "canManageUsers"]}>
    <ManageButton />
</AccessGate>

// ALL of multiple permissions
<AccessGate allPermissions={["canCreateInvoices", "canViewClients"]}>
    <CreateInvoiceButton />
</AccessGate>
```

## Convenience Components

Pre-built components for common patterns:

### CanView

```tsx
<CanView module="clients">
    <ClientDetails />
</CanView>

// Supports: clients, projects, invoices, analytics
```

### CanCreate

```tsx
<CanCreate module="projects">
    <button>New Project</button>
</CanCreate>

// Supports: clients, projects, invoices
```

### CanEdit

```tsx
<CanEdit module="clients">
    <button>Edit Client</button>
</CanEdit>

// Supports: clients, projects, invoices, photos
```

### CanDelete

```tsx
<CanDelete module="invoices">
    <button>Delete Invoice</button>
</CanDelete>

// Supports: clients, projects, invoices, photos
```

### CanManage

```tsx
<CanManage module="users">
    <TeamSettings />
</CanManage>

// Supports: users, settings, branding, services, packages
```

## Navigation Filtering

**Location:** `components/studio/StudioSidebar.tsx`

Filter navigation items based on permissions:

```tsx
const { hasPermission, isFeatureEnabled } = useAccessControl();

const filteredNavItems = useMemo(() => {
    return navItems.filter(item => {
        // Check feature flag
        if (item.feature && !isFeatureEnabled(item.feature)) {
            return false;
        }
        
        // Check permission
        if (item.permission && !hasPermission(item.permission)) {
            return false;
        }
        
        return true;
    });
}, [navItems, hasPermission, isFeatureEnabled]);
```

### Navigation Item Definition

```tsx
const navItems = [
    { 
        name: 'Dashboard', 
        path: '/studio', 
        icon: HomeIcon,
        // No permission required
    },
    { 
        name: 'Clients', 
        path: '/studio/clients', 
        icon: UsersIcon,
        feature: 'clients_module',
        permission: 'canViewClients',
    },
    { 
        name: 'Projects', 
        path: '/studio/projects', 
        icon: FolderIcon,
        feature: 'projects_module',
        permission: 'canViewProjects',
    },
    { 
        name: 'Invoices', 
        path: '/studio/invoices', 
        icon: DocumentIcon,
        feature: 'invoices_module',
        permission: 'canViewInvoices',
    },
    { 
        name: 'Settings', 
        path: '/studio/settings', 
        icon: CogIcon,
        permission: 'canManageSettings',
    },
];
```

## Real-World Examples

### ClientsPage.tsx

```tsx
function ClientsPage() {
    return (
        <div>
            <header>
                <h1>Clients</h1>
                <CanCreate module="clients">
                    <button onClick={openCreateModal}>
                        Add Client
                    </button>
                </CanCreate>
            </header>

            <table>
                {clients.map(client => (
                    <tr key={client.id}>
                        <td>{client.name}</td>
                        <td>
                            <CanEdit module="clients">
                                <button onClick={() => edit(client)}>
                                    Edit
                                </button>
                            </CanEdit>
                            <CanDelete module="clients">
                                <button onClick={() => remove(client)}>
                                    Delete
                                </button>
                            </CanDelete>
                        </td>
                    </tr>
                ))}
            </table>
        </div>
    );
}
```

### InvoicesPage.tsx

```tsx
function InvoicesPage() {
    const { hasPermission } = useAccessControl();

    return (
        <div>
            <CanCreate module="invoices">
                <button>Create Invoice</button>
            </CanCreate>

            {invoices.map(invoice => (
                <InvoiceCard 
                    key={invoice.id}
                    invoice={invoice}
                    canEdit={hasPermission('canEditInvoices')}
                    canDelete={hasPermission('canDeleteInvoices')}
                />
            ))}
        </div>
    );
}
```

## Caching

SettingsPage implements sessionStorage caching for studio users:

```typescript
const USERS_CACHE_KEY = 'studio_users_cache';
const USERS_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Check cache before API call
const cached = sessionStorage.getItem(USERS_CACHE_KEY);
if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < USERS_CACHE_TTL) {
        setStudioUsers(data);
        return;
    }
}

// Cache after successful fetch
sessionStorage.setItem(USERS_CACHE_KEY, JSON.stringify({
    data: mappedUsers,
    timestamp: Date.now()
}));

// Clear cache on mutations
sessionStorage.removeItem(USERS_CACHE_KEY);
```

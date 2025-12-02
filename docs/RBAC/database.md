# Database Schema

## Users Table

### Schema

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    studio_id VARCHAR(36) REFERENCES studios(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'client',
    permissions JSONB DEFAULT '{}',  -- RBAC permissions
    avatar_url VARCHAR(500),
    phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Invitation fields
    invitation_token VARCHAR(255),
    invitation_sent_at TIMESTAMP,
    invitation_accepted_at TIMESTAMP,
    invited_by_id VARCHAR(36) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_users_studio_id ON users(studio_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

### SQLAlchemy Model

**Location:** `app/db/models/user.py`

```python
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=True)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    
    role = Column(String(50), nullable=False, default='client', index=True)
    permissions = Column(JSON, nullable=True, default={})  # RBAC permissions
    
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    studio = relationship("Studio", back_populates="users")
```

## Permissions Column

### Data Type

- **PostgreSQL:** `JSONB` (binary JSON with indexing support)
- **SQLAlchemy:** `JSON` type (maps to JSONB in PostgreSQL)

### Structure

```json
{
    "canViewProjects": true,
    "canCreateProjects": false,
    "canEditProjects": true,
    "canDeleteProjects": false,
    "canViewClients": true,
    "canCreateClients": false,
    "canEditClients": false,
    "canDeleteClients": false,
    "canViewInvoices": false,
    "canCreateInvoices": false,
    "canEditInvoices": false,
    "canDeleteInvoices": false,
    "canViewAnalytics": true,
    "canUploadPhotos": true,
    "canEditPhotos": true,
    "canDeletePhotos": false,
    "canManageServices": false,
    "canManagePackages": false,
    "canManageSettings": false,
    "canManageUsers": false,
    "canManageBranding": false,
    "canSendNotifications": false,
    "canManageCommunication": false
}
```

### Default Value

- Default: `{}` (empty object)
- When empty, role defaults are used
- When populated, used directly (no merge)

## Role Column

### Values

| Role | Description |
|------|-------------|
| `studio_owner` | Studio owner, full access |
| `studio_admin` | Administrative user |
| `studio_photographer` | Content editor |
| `client` | External client |

### Constraints

```sql
-- No explicit enum constraint, validated at application level
ALTER TABLE users ADD CONSTRAINT check_valid_role 
    CHECK (role IN ('studio_owner', 'studio_admin', 'studio_photographer', 'client'));
```

## Querying Permissions

### Get User with Permissions

```python
from app.db.models import User
from sqlalchemy.orm import Session

def get_user_with_permissions(db: Session, user_id: str) -> User:
    return db.query(User).filter(User.id == user_id).first()

# Access permissions
user = get_user_with_permissions(db, "user-123")
if user.permissions:
    can_edit = user.permissions.get("canEditProjects", False)
```

### Update Permissions

```python
def update_user_permissions(db: Session, user_id: str, permissions: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.permissions = permissions
        db.commit()
        db.refresh(user)
    return user
```

### Query by Permission (PostgreSQL JSONB)

```python
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import JSONB

# Find users who can manage users
users_with_manage = db.query(User).filter(
    User.permissions['canManageUsers'].astext.cast(Boolean) == True
).all()

# Find users who can view clients
users_with_clients = db.query(User).filter(
    User.permissions.op('->>')('canViewClients') == 'true'
).all()
```

## Migration

### Adding Permissions Column

```python
# Alembic migration
def upgrade():
    op.add_column('users', 
        sa.Column('permissions', sa.JSON(), nullable=True, server_default='{}')
    )

def downgrade():
    op.drop_column('users', 'permissions')
```

### Backfilling Existing Users

```python
def backfill_permissions():
    """Set default permissions for existing users based on role."""
    from app.services.permission_service import PermissionService
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.permissions == None).all()
        for user in users:
            # Only set defaults if no custom permissions
            # Leave as {} to use role defaults dynamically
            user.permissions = {}
        db.commit()
    finally:
        db.close()
```

## Data Integrity

### Validation

Permissions are validated before storage:

```python
from app.services.permission_service import PermissionService

def update_user(user_id: str, permissions: dict):
    # Validate permissions
    is_valid, error = PermissionService.validate_permissions(permissions)
    if not is_valid:
        raise ValueError(error)
    
    # Proceed with update
    ...
```

### No Foreign Keys

Permissions are stored as denormalized JSON:
- **Pro:** Fast reads, no joins needed
- **Con:** No referential integrity for permission names
- **Mitigation:** Application-level validation

## Performance Considerations

### JSONB Indexing (Optional)

For large-scale deployments:

```sql
-- GIN index for JSONB containment queries
CREATE INDEX idx_users_permissions_gin ON users USING GIN (permissions);

-- Example query using index
SELECT * FROM users WHERE permissions @> '{"canManageUsers": true}';
```

### Caching

- Permissions are included in JWT tokens
- Frontend caches user list in sessionStorage (5 min TTL)
- Consider Redis caching for high-traffic scenarios

# Multi-Tenant Scripts

This directory contains scripts for setting up and testing the multi-tenant functionality.

## Quick Start

Run everything in one command:

```bash
# Initialize multi-tenant database and run tests
python scripts/init_multi_tenant_db.py && python scripts/test_multi_tenant.py
```

## Available Scripts

### 1. `init_multi_tenant_db.py`
**Purpose:** Initialize the multi-tenant database with tables, subscription plans, and a demo studio.

**Usage:**
```bash
python scripts/init_multi_tenant_db.py
```

**What it does:**
- Creates all multi-tenant database tables
- Seeds 3 subscription plans (Starter, Professional, Enterprise)
- Creates a demo studio with subdomain "demo"
- Configures domain mapping

**Output:**
```
🚀 Initializing Multi-Tenant Database
🔨 Creating database tables...
✅ All tables created successfully
📦 Seeding subscription plans...
   ✓ Added plan: Starter Plan ($29.0/mo)
   ✓ Added plan: Professional Plan ($99.0/mo)
   ✓ Added plan: Enterprise Plan ($299.0/mo)
✅ Seeded 3 subscription plans
🏢 Creating sample studio...
✅ Created sample studio:
   Name: Demo Photography Studio
   Subdomain: demo
   Domain: demo.photoapp.local
   Studio ID: xxx-xxx-xxx
🎉 Multi-tenant database initialized successfully!
```

### 2. `test_multi_tenant.py`
**Purpose:** Run automated tests to verify multi-tenant functionality.

**Usage:**
```bash
python scripts/test_multi_tenant.py
```

**Tests Performed:**
- ✅ Test 1: Creating test studios (alpha, beta, gamma)
- ✅ Test 2: Tenant detection from different hosts
- ✅ Test 3: Data isolation between studios
- ✅ Test 4: Storage path isolation
- ✅ Test 5: Subscription plans configuration

**Output:**
```
🚀 Multi-Tenant Testing Suite

🧪 Test 1: Creating test studios...
   ✓ Created studio: Studio Alpha (alpha)
   ✓ Created studio: Studio Beta (beta)
   ✓ Created studio: Studio Gamma (gamma)
✅ Test 1 passed: 3 studios ready

🧪 Test 2: Testing tenant detection...
   ✓ alpha.photoapp.local → Studio Alpha
   ✓ beta.photoapp.local → Studio Beta
   ✓ gamma.photoapp.local → Studio Gamma
✅ Test 2 passed: 5/5 cases successful

... more tests ...

🎉 All automated tests passed!
```

### 3. `migrate_sqlite_to_postgres.py`
**Purpose:** Migrate data from SQLite to PostgreSQL.

**Usage:**
```bash
# Set PostgreSQL connection
export DATABASE_URL="postgresql://user:password@localhost/photo_proof_production"

# Run migration
python scripts/migrate_sqlite_to_postgres.py
```

**What it does:**
- Backs up SQLite database
- Connects to both SQLite and PostgreSQL
- Migrates all tables in dependency order
- Converts data types (datetime, etc.)
- Verifies migration

**Prerequisites:**
- PostgreSQL installed and running
- Database and user created
- DATABASE_URL environment variable set
- Tables already created in PostgreSQL

## Step-by-Step Setup Guide

### Step 1: Install PostgreSQL (Optional)

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Create database
createdb photo_proof_production

# Create user
psql photo_proof_production
CREATE USER photo_proof_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE photo_proof_production TO photo_proof_user;
\q
```

### Step 2: Update Environment Variables

```bash
# For PostgreSQL (optional)
export DATABASE_URL="postgresql://photo_proof_user:your_password@localhost/photo_proof_production"

# Or keep SQLite (works fine for testing)
export DATABASE_URL="sqlite:///./photo_proof.db"
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Initialize Multi-Tenant Database

```bash
python scripts/init_multi_tenant_db.py
```

### Step 5: Run Tests

```bash
python scripts/test_multi_tenant.py
```

### Step 6: Configure Local Domains

```bash
# Add test domains to /etc/hosts
sudo tee -a /etc/hosts << 'EOF'
127.0.0.1 demo.photoapp.local
127.0.0.1 alpha.photoapp.local
127.0.0.1 beta.photoapp.local
127.0.0.1 gamma.photoapp.local
EOF
```

### Step 7: Start the Server

```bash
python main.py
```

### Step 8: Test Tenant Detection

```bash
# Test demo studio
curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/health

# Check response headers for X-Studio-ID
curl -v -H 'Host: alpha.photoapp.local' http://localhost:8000/api/health
```

## Troubleshooting

### Issue: "No module named 'app'"
**Solution:** Run scripts from the project root directory:
```bash
cd /path/to/photo_proof_api
python scripts/init_multi_tenant_db.py
```

### Issue: "Table already exists"
**Solution:** This is normal - the script skips existing tables. If you want to start fresh:
```bash
# Backup first!
cp photo_proof.db photo_proof.db.backup

# Delete database (caution!)
rm photo_proof.db

# Re-initialize
python scripts/init_multi_tenant_db.py
```

### Issue: "Studio not found for this domain"
**Solution:**
1. Check /etc/hosts has the domain entry
2. Verify studio has `subdomain` field set
3. Check StudioDomain table has verified entry
4. Restart the server

### Issue: PostgreSQL connection error
**Solution:**
1. Check PostgreSQL is running: `brew services list`
2. Verify DATABASE_URL is correct
3. Test connection: `psql $DATABASE_URL`
4. Check firewall/permissions

## Advanced Usage

### Create Studio Programmatically

```python
from app.db.session import SessionLocal
from app.db.models import Studio, StudioDomain
import uuid
from datetime import datetime

db = SessionLocal()

studio = Studio(
    id=str(uuid.uuid4()),
    name="My Studio",
    email="my@studio.com",
    subdomain="mystudio",
    brand_color="#FF5733",
    onboarding_completed=True,
    is_active=True
)
db.add(studio)
db.flush()

domain = StudioDomain(
    id=str(uuid.uuid4()),
    studio_id=studio.id,
    domain="mystudio.photoapp.local",
    subdomain="mystudio",
    is_primary=True,
    is_verified=True,
    verified_at=datetime.utcnow()
)
db.add(domain)

db.commit()
print(f"Created studio: {studio.id}")
db.close()
```

### Check Storage Usage

```python
from app.services.storage_service import tenant_storage

# Get storage stats for a studio
stats = tenant_storage.get_storage_stats("studio-id-here")
print(f"Total: {stats['total_gb']:.2f} GB")
print(f"Photos: {stats['photo_count']}")
```

### Invalidate Cache

```python
from app.services.cache_service import cache

# Invalidate all cache for a studio
cache.delete_pattern("studio:theme:studio-id-here")

# Or clear entire cache
cache.clear()
```

## Maintenance

### Clean Up Expired Cache Entries

```python
from app.services.cache_service import cache

# Manually trigger cleanup
cleaned = cache.cleanup_expired()
print(f"Cleaned up {cleaned} expired entries")
```

### Monitor Storage Usage

```python
from app.db.session import SessionLocal
from app.db.models import Studio
from app.services.storage_service import tenant_storage

db = SessionLocal()
studios = db.query(Studio).all()

for studio in studios:
    used_bytes = tenant_storage.get_studio_storage_usage(studio.id)
    used_gb = used_bytes / (1024 ** 3)
    print(f"{studio.name}: {used_gb:.2f} GB / {studio.max_storage_gb} GB")

db.close()
```

## Migration Between Databases

### SQLite → PostgreSQL

```bash
# 1. Backup SQLite
cp photo_proof.db photo_proof.db.backup

# 2. Set up PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/photo_proof_db"

# 3. Create tables in PostgreSQL
python scripts/init_multi_tenant_db.py

# 4. Migrate data
python scripts/migrate_sqlite_to_postgres.py

# 5. Verify
psql $DATABASE_URL -c "SELECT COUNT(*) FROM studios;"
```

## Performance Tips

1. **Use PostgreSQL for production** - Much better concurrency
2. **Enable caching** - Cache studio themes for 30+ minutes
3. **Add database indexes** - Already configured in migration
4. **Use connection pooling** - Already configured (20 base + 10 overflow)
5. **Monitor storage** - Track usage per studio

## Security Checklist

- ✅ Tenant isolation enforced in middleware
- ✅ Storage paths validated (prevent directory traversal)
- ✅ Database queries filtered by studio_id
- ✅ API dependencies check studio ownership
- ✅ File access restricted to studio directory
- ✅ No cross-tenant data leakage

## Support

For issues or questions:
1. Check MULTI_TENANT_IMPLEMENTATION.md for detailed docs
2. Review logs in `logs/photo_proof_api.log`
3. Verify database schema matches models
4. Test with curl commands provided above

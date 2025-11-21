#!/usr/bin/env python3
"""Initialize PostgreSQL database with all tables."""

import sys
import os

# Set PostgreSQL URL
os.environ['DATABASE_URL'] = 'postgresql://photo_proof_user:PhotoProof2024!@localhost/photo_proof_production'

# Import after setting env
from app.db.session import engine
from app.db.models import Base

# Import all models to register them with Base
import app.db.models.user
import app.db.models.project
import app.db.models.photo
import app.db.models.service
import app.db.models.store
import app.db.models.upload
import app.db.models.notification
import app.db.models.settings
import app.db.models.multi_tenant

print("🚀 Initializing PostgreSQL database...")
print(f"📍 Database: {os.environ['DATABASE_URL'].split('@')[1]}")
print()

try:
    # Create all tables
    print("📋 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    print()
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"📊 Created {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  ✓ {table}")
    
    print()
    print("🎉 PostgreSQL initialization complete!")
    print()
    print("Next steps:")
    print("  1. Run migration script to copy data from SQLite")
    print("  2. Restart your backend server")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

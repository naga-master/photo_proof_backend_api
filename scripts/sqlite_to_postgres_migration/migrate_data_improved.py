#!/usr/bin/env python3
"""
Improved SQLite to PostgreSQL migration with proper type handling.
"""

import sqlite3
import sys
import os
from datetime import datetime

# Set PostgreSQL URL
os.environ['DATABASE_URL'] = 'postgresql://photo_proof_user:PhotoProof2024!@localhost/photo_proof_production'

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

print("🚀 Starting Improved SQLite → PostgreSQL Migration\n")

# Connect to SQLite
sqlite_db = 'photo_proof.db'
sqlite_conn = sqlite3.connect(sqlite_db)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_url = os.environ['DATABASE_URL']
pg_engine = create_engine(pg_url)
Session = sessionmaker(bind=pg_engine)
pg_session = Session()

# Get list of tables from PostgreSQL
inspector = inspect(pg_engine)
pg_tables = inspector.get_table_names()

print(f"📊 Found {len(pg_tables)} tables in PostgreSQL\n")

# Define column types for proper conversion (ALL boolean columns)
BOOLEAN_COLUMNS = {
    'studios': ['is_active', 'onboarding_completed'],
    'users': ['is_active', 'email_verified'],
    'clients': ['is_active', 'whatsapp_opt_in', 'email_opt_in'],
    'service_packages': ['is_predefined'],
    'projects': ['is_locked', 'has_folders'],
    'photos': ['is_favorite', 'is_selected', 'is_cover'],
    'photo_versions': ['is_primary', 'is_original'],
    'comments': ['is_edited'],
    'invoices': ['is_paid'],
    'products': ['is_active'],
    'product_options': ['is_active'],
    'orders': ['is_paid'],
    'upload_sessions': ['is_completed'],
    'upload_tokens': ['is_version_upload'],
    'layout_templates': ['is_predefined'],
    'ai_tools': ['is_active'],
    'studio_domains': ['is_primary', 'is_verified'],
    'subscription_plans': ['is_active', 'is_popular', 'is_visible'],
    'studio_subscriptions': ['auto_renew', 'cancel_at_period_end'],
    'studio_features': ['is_enabled'],
}

def convert_value(column_name, value, table_name):
    """Convert SQLite values to PostgreSQL-compatible format."""
    if value is None:
        return None
    
    # Handle boolean columns
    if table_name in BOOLEAN_COLUMNS and column_name in BOOLEAN_COLUMNS[table_name]:
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'yes', 't')
        return bool(value)
    
    # Handle datetime strings
    if isinstance(value, str) and len(value) > 10 and ('-' in value or 'T' in value):
        try:
            # Try parsing ISO datetime
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            pass
    
    return value

# Tables to migrate in dependency order
TABLES_TO_MIGRATE = [
    'studios',
    'users',
    'clients',
    'service_packages',
    'projects',
    'folders',
    'photos',
    'photo_versions',
    'comments',
    'invoices',
    'products',
    'product_options',
    'cart_items',
    'orders',
    'notifications',
    'user_photo_favorites',
    'user_photo_selections',
    'upload_sessions',
    'upload_tokens',
    'layout_templates',
    'communication_settings',
    'ai_tools',
    'studio_domains',
    'subscription_plans',
    'studio_subscriptions',
    'studio_features',
    'studio_usage_stats',
]

total_migrated = 0

for table_name in TABLES_TO_MIGRATE:
    # Skip if table doesn't exist in PostgreSQL
    if table_name not in pg_tables:
        print(f"⏭️  Skipping {table_name} (doesn't exist in PostgreSQL)")
        continue
    
    # Get data from SQLite
    try:
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
    except sqlite3.OperationalError:
        print(f"⏭️  Skipping {table_name} (doesn't exist in SQLite)")
        continue
    
    if not rows:
        print(f"⏭️  Skipping {table_name} (no data)")
        continue
    
    print(f"📦 Migrating {table_name} ({len(rows)} rows)...")
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    
    migrated_count = 0
    failed_count = 0
    
    for row in rows:
        try:
            # Convert values with proper type handling
            values = {col: convert_value(col, row[col], table_name) for col in columns}
            
            # Build INSERT statement
            cols = ', '.join(f'"{col}"' for col in columns)
            placeholders = ', '.join(f':{col}' for col in columns)
            sql = f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})'
            
            # Execute
            pg_session.execute(text(sql), values)
            migrated_count += 1
            
        except Exception as e:
            failed_count += 1
            if failed_count <= 3:  # Only print first few errors
                print(f"  ⚠️  Error inserting row: {str(e)[:100]}")
    
    # Commit after each table
    try:
        pg_session.commit()
        print(f"  ✅ Migrated {migrated_count} rows (failed: {failed_count})\n")
        total_migrated += migrated_count
    except Exception as e:
        pg_session.rollback()
        print(f"  ❌ Failed to commit {table_name}: {e}\n")

# Close connections
sqlite_conn.close()
pg_session.close()

print(f"\n🎉 Migration complete! Total rows migrated: {total_migrated}")
print("\n📝 Next steps:")
print("  1. Restart your backend server")
print("  2. Test the application")
print(f"  3. Backend should now log: '[INFO] Using PostgreSQL with connection pooling'")

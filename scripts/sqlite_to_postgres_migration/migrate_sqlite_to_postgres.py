#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL.
Handles all data types, foreign keys, and constraints.
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json
from datetime import datetime
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
SQLITE_DB = 'photo_proof.db'
POSTGRES_DSN = os.getenv('DATABASE_URL', 'postgresql://photo_proof_user:secure_password_here@localhost/photo_proof_production')

# Tables in dependency order (respects foreign keys)
TABLE_ORDER = [
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
]

def convert_value(value):
    """Convert SQLite values to PostgreSQL-compatible format."""
    if value is None:
        return None
    if isinstance(value, str):
        # Try parsing ISO datetime strings
        if len(value) > 10 and ('T' in value or '-' in value[:10]):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                pass
    return value

def migrate_table(sqlite_cursor, pg_cursor, table_name):
    """Migrate a single table from SQLite to PostgreSQL."""
    print(f"📦 Migrating table: {table_name}")
    
    # Get all rows from SQLite
    try:
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  Table {table_name} doesn't exist in SQLite, skipping ({e})")
        return
    
    rows = sqlite_cursor.fetchall()
    if not rows:
        print(f"  ⏭️  No data in {table_name}")
        return
    
    # Get column names
    columns = [desc[0] for desc in sqlite_cursor.description]
    columns_str = ','.join(f'"{col}"' for col in columns)
    
    # Prepare data
    converted_rows = []
    for row in rows:
        converted_rows.append([convert_value(val) for val in row])
    
    # Insert into PostgreSQL
    placeholders = ','.join(['%s'] * len(columns))
    insert_query = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
    
    try:
        success_count = 0
        for row_data in converted_rows:
            try:
                pg_cursor.execute(insert_query, row_data)
                success_count += 1
            except Exception as row_error:
                print(f"  ⚠️  Error inserting row: {row_error}")
                continue
        
        print(f"  ✅ Migrated {success_count}/{len(converted_rows)} rows")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        raise

def main():
    print("🚀 Starting SQLite → PostgreSQL Migration\n")
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite database not found: {SQLITE_DB}")
        sys.exit(1)
    
    # Backup SQLite first
    import shutil
    backup_file = f"{SQLITE_DB}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(SQLITE_DB, backup_file)
    print(f"💾 Backup created: {backup_file}\n")
    
    # Connect to databases
    print(f"📂 Connecting to SQLite: {SQLITE_DB}")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    print(f"🐘 Connecting to PostgreSQL: {POSTGRES_DSN.split('@')[1] if '@' in POSTGRES_DSN else POSTGRES_DSN}")
    try:
        pg_conn = psycopg2.connect(POSTGRES_DSN)
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is installed and running")
        print("  2. Database and user are created")
        print("  3. DATABASE_URL environment variable is set correctly")
        sys.exit(1)
    
    # Create tables first (using Alembic or SQLAlchemy)
    print("\n📋 Note: Make sure you've created tables using: python -c 'from app.db.init_db import init_db; init_db()'\n")
    
    # Migrate each table
    print("🔄 Starting table migration...\n")
    for table in TABLE_ORDER:
        migrate_table(sqlite_cursor, pg_cursor, table)
    
    # Commit all changes
    pg_conn.commit()
    print("\n💾 Committed all changes to PostgreSQL")
    
    # Verify migration
    print("\n🔍 Verification:")
    for table in TABLE_ORDER:
        try:
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = pg_cursor.fetchone()[0]
            if count > 0:
                print(f"  ✅ {table}: {count} rows")
        except Exception as e:
            print(f"  ⚠️  {table}: {e}")
    
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n🎉 Migration complete!")
    print(f"\n📝 Next steps:")
    print(f"  1. Update your .env file with:")
    print(f"     DATABASE_URL={POSTGRES_DSN}")
    print(f"  2. Restart your application")
    print(f"  3. Test thoroughly")

if __name__ == "__main__":
    main()

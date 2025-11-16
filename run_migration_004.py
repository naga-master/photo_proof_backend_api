#!/usr/bin/env python3
"""
Run Migration 004: Add Image Optimization Fields
Adds variants_json and thumbhash columns to photos table
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "photo_proof.db"
MIGRATION_FILE = Path(__file__).parent / "migrations" / "004_add_image_optimization_fields.sql"

def run_migration():
    """Apply migration 004 to add image optimization fields"""
    
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)
    
    if not MIGRATION_FILE.exists():
        print(f"Error: Migration file not found at {MIGRATION_FILE}")
        sys.exit(1)
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(photos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'variants_json' in columns and 'thumbhash' in columns:
            print("✓ Migration already applied. Columns exist.")
            return
        
        print("Reading migration file...")
        with open(MIGRATION_FILE, 'r') as f:
            migration_sql = f.read()
        
        print("Applying migration...")
        
        # Execute migration (split by semicolon for multiple statements)
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                print(f"  Executing: {statement[:50]}...")
                cursor.execute(statement)
        
        conn.commit()
        print("✓ Migration 004 applied successfully!")
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(photos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'variants_json' in columns and 'thumbhash' in columns:
            print("✓ Verified: variants_json and thumbhash columns added")
        else:
            print("⚠ Warning: Columns may not have been added correctly")
        
        # Show table info
        print("\nUpdated photos table schema:")
        cursor.execute("PRAGMA table_info(photos)")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error applying migration: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Migration 004: Add Image Optimization Fields")
    print("=" * 60)
    run_migration()
    print("=" * 60)

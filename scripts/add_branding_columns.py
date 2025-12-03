#!/usr/bin/env python3
"""
Add branding columns to studios table for PostgreSQL.
Includes: studio_photo, studio_description, typography, custom_css, subdomain, onboarding fields
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

def main():
    print("🔧 Adding branding columns to studios table...")
    
    # Columns to add (compatible with PostgreSQL)
    columns_to_add = [
        ("subdomain", "VARCHAR(63)"),
        ("typography", "VARCHAR(255) DEFAULT 'System Default (Inter & Cormorant)'"),
        ("custom_css", "TEXT"),
        ("studio_photo", "TEXT"),
        ("studio_description", "TEXT"),
        ("onboarding_step", "VARCHAR(50) DEFAULT 'studio'"),
        ("onboarding_completed", "BOOLEAN DEFAULT FALSE"),
    ]
    
    with engine.connect() as connection:
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists (PostgreSQL syntax)
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'studios' AND column_name = :col_name
                """), {"col_name": column_name})
                
                exists = result.fetchone() is not None
                
                if not exists:
                    print(f"  Adding column: {column_name}")
                    connection.execute(text(f"ALTER TABLE studios ADD COLUMN {column_name} {column_type}"))
                    connection.commit()
                    print(f"  ✅ Added {column_name}")
                else:
                    print(f"  ⏭️  Column {column_name} already exists")
            except Exception as e:
                print(f"  ❌ Error adding {column_name}: {e}")
                # Try to rollback if there was an error
                try:
                    connection.rollback()
                except:
                    pass
    
    print("\n✅ Schema update complete")
    print("\n📋 Current studios table schema:")
    
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'studios'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"   {row[0]}: {row[1]} (nullable: {row[2]})")

if __name__ == "__main__":
    main()

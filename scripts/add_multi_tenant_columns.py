#!/usr/bin/env python3
"""
Quick script to add multi-tenant columns to the existing studios table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

def main():
    print("🔧 Adding multi-tenant columns to studios table...")
    
    # Add columns that might be missing
    columns_to_add = [
        ("subdomain", "VARCHAR(255)"),
        ("custom_css", "TEXT"),
        ("onboarding_completed", "BOOLEAN DEFAULT 0"),
        ("onboarding_step", "INTEGER DEFAULT 0"),
    ]
    
    with engine.connect() as connection:
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                result = connection.execute(text(f"PRAGMA table_info(studios)"))
                existing_columns = [row[1] for row in result]
                
                if column_name not in existing_columns:
                    print(f"  Adding column: {column_name}")
                    connection.execute(text(f"ALTER TABLE studios ADD COLUMN {column_name} {column_type}"))
                    connection.commit()
                    print(f"  ✅ Added {column_name}")
                else:
                    print(f"  ⏭️  Column {column_name} already exists")
            except Exception as e:
                print(f"  ❌ Error adding {column_name}: {e}")
    
    print("✅ Schema update complete")

if __name__ == "__main__":
    main()

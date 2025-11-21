#!/usr/bin/env python3
"""
Script to create missing image_versions records for images that exist in the images table
but don't have corresponding version records.
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
import sqlite3

def create_missing_versions():
    """Create missing image_versions records for images without versions."""
    
    db_path = Path(__file__).parent / "photo_proof.db"
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Find images that don't have any versions
        cursor.execute("""
            SELECT i.id, i.original_filename, i.s3_key_original, i.file_size_bytes,
                   i.width, i.height, i.mime_type, i.uploaded_at
            FROM images i
            LEFT JOIN image_versions iv ON i.id = iv.image_id
            WHERE iv.image_id IS NULL
        """)
        
        images_without_versions = cursor.fetchall()
        
        print(f"Found {len(images_without_versions)} images without versions")
        
        created_count = 0
        
        for image_data in images_without_versions:
            image_id, original_filename, s3_key, file_size, width, height, mime_type, uploaded_at = image_data
            
            try:
                # Generate version ID
                version_id = str(uuid.uuid4())
                
                # Create the image_versions record
                cursor.execute("""
                    INSERT INTO image_versions (
                        id, image_id, version_name, s3_key, file_size_bytes,
                        width, height, created_by, created_at, original_filename,
                        mime_type, is_current
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    version_id,
                    image_id,
                    'original',  # version_name
                    s3_key,     # s3_key - same as the image s3_key_original  
                    file_size,
                    width,
                    height,
                    'system-restore',  # created_by
                    uploaded_at,       # created_at - use same as image uploaded_at
                    original_filename,
                    mime_type,
                    True    # is_current - this is the current/latest version
                ))
                
                created_count += 1
                print(f"Created version for image: {original_filename} -> {version_id}")
                
            except Exception as e:
                print(f"Error creating version for image {image_id}: {e}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print(f"\nSuccessfully created {created_count} image version records.")
        
    except Exception as e:
        print(f"Error processing database: {e}")

if __name__ == "__main__":
    create_missing_versions()
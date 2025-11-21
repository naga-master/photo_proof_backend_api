#!/usr/bin/env python3
"""
Script to restore missing image database records for files that exist on disk.
This script scans the uploads directory and creates database records for any
images that were uploaded but don't have corresponding database entries.
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from PIL import Image
import sqlite3
from typing import Dict, List, Tuple

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    """Get image dimensions from file."""
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        print(f"Warning: Could not get dimensions for {image_path}: {e}")
        return (0, 0)

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def scan_uploads_directory(uploads_dir: Path) -> List[Dict]:
    """Scan uploads directory and return list of found images."""
    found_images = []
    
    if not uploads_dir.exists():
        print(f"Uploads directory not found: {uploads_dir}")
        return found_images
    
    # Scan each project directory
    for project_dir in uploads_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        project_id = project_dir.name
        print(f"Scanning project: {project_id}")
        
        # Scan each category directory within the project
        for category_dir in project_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_id = category_dir.name
            print(f"  Category: {category_id}")
            
            # Scan each image file in the category
            for image_file in category_dir.iterdir():
                if not image_file.is_file():
                    continue
                    
                # Skip non-image files
                if not image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    continue
                
                # Get image info
                width, height = get_image_dimensions(image_file)
                file_size = get_file_size(image_file)
                
                found_images.append({
                    'project_id': project_id,
                    'category_id': category_id,
                    'filename': image_file.name,
                    'file_path': str(image_file),
                    'file_size': file_size,
                    'width': width,
                    'height': height,
                    'uploaded_at': datetime.fromtimestamp(image_file.stat().st_mtime)
                })
                
                print(f"    Found: {image_file.name} ({width}x{height}, {file_size} bytes)")
    
    return found_images

def check_existing_images(db_path: Path, found_images: List[Dict]) -> List[Dict]:
    """Check which images already exist in database and return missing ones."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return found_images
    
    missing_images = []
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        for image_info in found_images:
            # Check if image already exists in database
            cursor.execute("""
                SELECT id FROM images 
                WHERE project_id = ? AND category_id = ? AND original_filename = ?
            """, (
                image_info['project_id'],
                image_info['category_id'], 
                image_info['filename']
            ))
            
            result = cursor.fetchone()
            if not result:
                missing_images.append(image_info)
                print(f"Missing from DB: {image_info['project_id']}/{image_info['category_id']}/{image_info['filename']}")
            else:
                print(f"Already in DB: {image_info['filename']}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return found_images
    
    return missing_images

def create_database_records(db_path: Path, missing_images: List[Dict]) -> int:
    """Create database records for missing images."""
    if not missing_images:
        print("No missing images to restore.")
        return 0
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        created_count = 0
        
        for image_info in missing_images:
            try:
                # Generate a new UUID for the image
                image_id = str(uuid.uuid4())
                
                # Get MIME type from filename
                file_ext = image_info['filename'].lower().split('.')[-1]
                mime_type = f"image/{file_ext}" if file_ext in ['jpg', 'jpeg'] else f"image/{file_ext}"
                if file_ext == 'jpg':
                    mime_type = "image/jpeg"
                
                # Create S3 key path (this is the relative path to the file)
                s3_key = f"{image_info['project_id']}/{image_info['category_id']}/{image_info['filename']}"
                
                # Insert the image record
                cursor.execute("""
                    INSERT INTO images (
                        id, project_id, category_id, uploaded_by, original_filename,
                        s3_key_original, file_size_bytes, mime_type, width, height,
                        rating, is_favorite, is_selected, comment_count, status,
                        uploaded_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    image_id,
                    image_info['project_id'],
                    image_info['category_id'],
                    'system-restore',  # uploaded_by - we'll use a special system user ID
                    image_info['filename'],
                    s3_key,
                    image_info['file_size'],
                    mime_type,
                    image_info['width'],
                    image_info['height'],
                    0,      # rating
                    False,  # is_favorite
                    False,  # is_selected
                    0,      # comment_count
                    'ready',  # status - use 'ready' to match backend expectations
                    image_info['uploaded_at'],
                    datetime.now()
                ))
                
                # Generate version ID for the image version
                version_id = str(uuid.uuid4())
                
                # Also create the corresponding image_versions record
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
                    image_info['file_size'],
                    image_info['width'],
                    image_info['height'],
                    'system-restore',  # created_by
                    image_info['uploaded_at'],
                    image_info['filename'],
                    mime_type,
                    True    # is_current - this is the current/latest version
                ))
                
                created_count += 1
                print(f"Created DB record: {image_info['filename']} -> {image_id}")
                
            except Exception as e:
                print(f"Error creating record for {image_info['filename']}: {e}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print(f"\nSuccessfully created {created_count} database records.")
        return created_count
        
    except Exception as e:
        print(f"Error creating database records: {e}")
        return 0

def main():
    """Main function to restore missing image records."""
    print("Starting image database restoration...")
    
    # Set up paths
    script_dir = Path(__file__).parent
    uploads_dir = script_dir / "uploads"
    db_path = script_dir / "photo_proof.db"
    
    print(f"Uploads directory: {uploads_dir}")
    print(f"Database path: {db_path}")
    
    # Step 1: Scan uploads directory
    print("\n1. Scanning uploads directory...")
    found_images = scan_uploads_directory(uploads_dir)
    print(f"Found {len(found_images)} image files on disk.")
    
    if not found_images:
        print("No images found. Exiting.")
        return
    
    # Step 2: Check which images are missing from database
    print("\n2. Checking database for missing records...")
    missing_images = check_existing_images(db_path, found_images)
    print(f"Found {len(missing_images)} images missing from database.")
    
    if not missing_images:
        print("All images are already in the database. Nothing to restore.")
        return
    
    # Step 3: Create database records for missing images
    print("\n3. Creating missing database records...")
    created_count = create_database_records(db_path, missing_images)
    
    print(f"\nRestoration complete. Created {created_count} new database records.")

if __name__ == "__main__":
    main()
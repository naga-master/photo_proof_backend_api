#!/usr/bin/env python3
"""
Migration 005: Migrate Variants to Nested Directory Structure

Moves variants from flat structure to nested project-based structure:
  OLD: uploads/variants/808_thumbnail.webp
  NEW: uploads/projects/10/variants/808/thumbnail.webp

Also moves originals from:
  OLD: uploads/projects/10/filename.jpg
  NEW: uploads/projects/10/originals/filename.jpg
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime


def migrate_variants():
    """Migrate existing variants to nested structure"""
    
    db_path = "photo_proof.db"
    uploads_base = Path("uploads")
    
    print("=" * 60)
    print("Migration 005: Nested Directory Structure")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all photos with variants
    cursor.execute("""
        SELECT id, project_id, storage_path, variants_json
        FROM photos
        WHERE variants_json IS NOT NULL
    """)
    
    photos = cursor.fetchall()
    total = len(photos)
    
    print(f"\n📊 Found {total} photos with variants to migrate")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for photo_id, project_id, storage_path, variants_json_str in photos:
        try:
            print(f"[{migrated_count + skipped_count + error_count + 1}/{total}] Photo {photo_id} (Project {project_id})")
            
            # Parse variants JSON
            variants = json.loads(variants_json_str)
            
            # Create new variants directory
            new_variants_dir = uploads_base / "projects" / str(project_id) / "variants" / str(photo_id)
            new_variants_dir.mkdir(parents=True, exist_ok=True)
            
            new_variants = {}
            all_moved = True
            
            # Move each variant file
            for quality, old_path in variants.items():
                # Handle paths with or without "uploads/" prefix
                clean_old_path = old_path.removeprefix("uploads/")
                old_file_path = uploads_base / clean_old_path
                
                # NEW: uploads/projects/10/variants/808/thumbnail.webp
                new_filename = f"{quality}.webp"
                new_file_path = new_variants_dir / new_filename
                new_relative_path = f"projects/{project_id}/variants/{photo_id}/{new_filename}"
                
                if old_file_path.exists():
                    # Move file
                    shutil.move(str(old_file_path), str(new_file_path))
                    new_variants[quality] = new_relative_path
                    print(f"  ✓ Moved {quality}: {old_path} → {new_relative_path}")
                else:
                    print(f"  ⚠ Missing {quality}: {old_path} (file not found at {old_file_path})")
                    all_moved = False
            
            # Update database only if all variants moved successfully
            if all_moved and new_variants:
                new_variants_json = json.dumps(new_variants)
                cursor.execute("""
                    UPDATE photos
                    SET variants_json = ?
                    WHERE id = ?
                """, (new_variants_json, photo_id))
                migrated_count += 1
                print(f"  ✓ Database updated")
            else:
                skipped_count += 1
                print(f"  ⚠ Skipped (missing files)")
            
            print()
            
        except Exception as e:
            error_count += 1
            print(f"  ✗ Error: {e}")
            print()
    
    # Commit all database updates
    conn.commit()
    
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"✓ Migrated: {migrated_count}")
    print(f"⚠ Skipped:  {skipped_count}")
    print(f"✗ Errors:   {error_count}")
    print(f"📊 Total:    {total}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check for empty old variants directory
    old_variants_dir = uploads_base / "variants"
    if old_variants_dir.exists():
        remaining_files = list(old_variants_dir.iterdir())
        if remaining_files:
            print(f"⚠ Warning: {len(remaining_files)} files remain in uploads/variants/")
            print(f"   Review these files before deleting the directory")
        else:
            print(f"✓ Old variants/ directory is empty and can be safely deleted")
    
    conn.close()
    
    print()
    print("✅ Migration Complete!")
    print()


def migrate_originals():
    """Migrate original files to originals/ subdirectory"""
    
    db_path = "photo_proof.db"
    uploads_base = Path("uploads")
    
    print("=" * 60)
    print("Migrating Original Files to originals/ Subdirectory")
    print("=" * 60)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all photos
    cursor.execute("""
        SELECT id, project_id, storage_path
        FROM photos
        WHERE storage_path NOT LIKE '%/originals/%'
    """)
    
    photos = cursor.fetchall()
    total = len(photos)
    
    print(f"📊 Found {total} photos to migrate")
    print()
    
    migrated = 0
    skipped = 0
    
    for photo_id, project_id, storage_path in photos:
        try:
            # OLD: projects/10/20251116_152207_abc123_photo.jpg
            old_file_path = uploads_base / storage_path
            
            # NEW: projects/10/originals/20251116_152207_abc123_photo.jpg
            filename = Path(storage_path).name
            new_storage_path = f"projects/{project_id}/originals/{filename}"
            new_file_path = uploads_base / new_storage_path
            
            if old_file_path.exists():
                # Create originals directory
                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(old_file_path), str(new_file_path))
                
                # Update database
                cursor.execute("""
                    UPDATE photos
                    SET storage_path = ?
                    WHERE id = ?
                """, (new_storage_path, photo_id))
                
                migrated += 1
                print(f"[{migrated + skipped}/{total}] ✓ Photo {photo_id}: {storage_path} → {new_storage_path}")
            else:
                skipped += 1
                print(f"[{migrated + skipped}/{total}] ⚠ Photo {photo_id}: File not found at {storage_path}")
        
        except Exception as e:
            print(f"✗ Error migrating photo {photo_id}: {e}")
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print(f"✓ Migrated: {migrated}")
    print(f"⚠ Skipped:  {skipped}")
    print(f"📊 Total:    {total}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    print()
    print("🚀 Starting Migration 005: Nested Directory Structure")
    print()
    
    # Step 1: Migrate variants
    migrate_variants()
    
    # Step 2: Migrate originals
    migrate_originals()
    
    print()
    print("✅ All migrations complete!")
    print()
    print("Next steps:")
    print("1. Verify all files migrated correctly")
    print("2. Test variant endpoints work")
    print("3. Test new uploads use new structure")
    print("4. After verification, delete old uploads/variants/ directory")
    print()

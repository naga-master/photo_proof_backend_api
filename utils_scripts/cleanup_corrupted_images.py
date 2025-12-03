#!/usr/bin/env python3
"""
Image Cleanup Script
Identifies and removes corrupted image files from both filesystem and database.
"""

import os
import sqlite3
import mimetypes
from pathlib import Path

def is_valid_image_file(filepath):
    """Check if a file is a valid image based on size and content."""
    try:
        # Check file size - images should be reasonably sized
        size = os.path.getsize(filepath)
        
        # First check: Is the file suspiciously small?
        if size < 100:  # Less than 100 bytes is likely corrupted
            return False, f"File too small ({size} bytes)"
        
        # Second check: Try to read the file as text to detect ASCII text files
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(min(size, 200))  # Read first 200 chars or entire file
            
            # If we can read it as text and it contains common test phrases, it's corrupted
            test_phrases = ['test', 'hello', 'image does not exist', 'test data', 'hello world']
            if any(phrase in content.lower() for phrase in test_phrases):
                return False, f"Contains test text: '{content.strip()}'"
            
            # If the entire file is readable as text and short, it's probably not an image
            if size < 1000 and content.isprintable():
                return False, f"File is ASCII text: '{content.strip()}'"
                
        except UnicodeDecodeError:
            # Good! Can't decode as text - likely a real binary image file
            pass
        
        # Third check: Try to read first few bytes to check for image headers
        with open(filepath, 'rb') as f:
            header = f.read(20)
        
        # Check for common image file signatures
        # JPEG: FF D8 FF
        # PNG: 89 50 4E 47
        if filepath.lower().endswith('.jpg') or filepath.lower().endswith('.jpeg'):
            if not (len(header) >= 3 and header[:3] == b'\xff\xd8\xff'):
                return False, "Invalid JPEG header"
        elif filepath.lower().endswith('.png'):
            if not (len(header) >= 8 and header[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'):
                return False, "Invalid PNG header"
        
        return True, "Valid image file"
    
    except Exception as e:
        return False, f"Error checking file: {str(e)}"

def scan_all_images(uploads_dir):
    """Scan all image files in the uploads directory."""
    print("🔍 Scanning all image files for corruption...")
    
    valid_files = []
    corrupted_files = []
    
    for root, dirs, files in os.walk(uploads_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                filepath = os.path.join(root, file)
                is_valid, reason = is_valid_image_file(filepath)
                
                if is_valid:
                    valid_files.append(filepath)
                else:
                    corrupted_files.append((filepath, reason))
                    print(f"  ❌ CORRUPTED: {filepath}")
                    print(f"     Reason: {reason}")
    
    print(f"\n📊 Scan Results:")
    print(f"  ✅ Valid images: {len(valid_files)}")
    print(f"  ❌ Corrupted images: {len(corrupted_files)}")
    
    return valid_files, corrupted_files

def get_database_entries_for_files(db_path, corrupted_files):
    """Find database entries for corrupted files."""
    print("\n🔍 Checking database entries for corrupted files...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Extract just filenames from corrupted file paths
    corrupted_filenames = []
    for filepath, reason in corrupted_files:
        filename = os.path.basename(filepath)
        corrupted_filenames.append(filename)
    
    # Find database entries
    db_entries = []
    for filename in corrupted_filenames:
        cursor.execute("""
            SELECT id, s3_key_original, original_filename, project_id 
            FROM images 
            WHERE original_filename = ?
        """, (filename,))
        
        results = cursor.fetchall()
        for row in results:
            db_entries.append({
                'id': row[0],
                'url': row[1],
                'filename': row[2],
                'project_id': row[3]
            })
    
    conn.close()
    
    print(f"  📋 Found {len(db_entries)} database entries for corrupted files")
    for entry in db_entries:
        print(f"    - {entry['filename']} (ID: {entry['id'][:8]}...)")
    
    return db_entries

def cleanup_corrupted_files(corrupted_files, db_entries, db_path, dry_run=True):
    """Remove corrupted files from filesystem and database."""
    if dry_run:
        print("\n🧪 DRY RUN - No files will be deleted")
    else:
        print("\n🧹 CLEANING UP corrupted files...")
    
    # Remove files from filesystem
    removed_files = 0
    for filepath, reason in corrupted_files:
        if dry_run:
            print(f"  Would delete: {filepath}")
        else:
            try:
                os.remove(filepath)
                print(f"  ✅ Deleted file: {filepath}")
                removed_files += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {filepath}: {e}")
    
    # Remove database entries
    removed_db_entries = 0
    if not dry_run and db_entries:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for entry in db_entries:
            try:
                cursor.execute("DELETE FROM images WHERE id = ?", (entry['id'],))
                print(f"  ✅ Removed DB entry: {entry['filename']} (ID: {entry['id'][:8]}...)")
                removed_db_entries += 1
            except Exception as e:
                print(f"  ❌ Failed to remove DB entry {entry['id']}: {e}")
        
        conn.commit()
        conn.close()
    
    if dry_run:
        print(f"\n📊 Would remove:")
        print(f"  📁 Files: {len(corrupted_files)}")
        print(f"  📋 DB entries: {len(db_entries)}")
    else:
        print(f"\n📊 Cleanup completed:")
        print(f"  📁 Files removed: {removed_files}/{len(corrupted_files)}")
        print(f"  📋 DB entries removed: {removed_db_entries}/{len(db_entries)}")

def main():
    """Main cleanup process."""
    print("🧹 Image Cleanup Script")
    print("=" * 50)
    
    # Configuration
    uploads_dir = "./uploads"
    db_path = "./photo_proof.db"
    
    # Check if directories exist
    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads directory not found: {uploads_dir}")
        return
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    # Step 1: Scan all images
    valid_files, corrupted_files = scan_all_images(uploads_dir)
    
    if not corrupted_files:
        print("\n🎉 No corrupted files found! All images are valid.")
        return
    
    # Step 2: Find database entries
    db_entries = get_database_entries_for_files(db_path, corrupted_files)
    
    # Step 3: Show what will be cleaned up
    print("\n📋 Files to be cleaned up:")
    for i, (filepath, reason) in enumerate(corrupted_files, 1):
        print(f"  {i}. {filepath}")
        print(f"     Reason: {reason}")
    
    # Step 4: Ask for confirmation
    print(f"\n⚠️  WARNING: This will permanently delete {len(corrupted_files)} files and {len(db_entries)} database entries!")
    
    # First run as dry run
    cleanup_corrupted_files(corrupted_files, db_entries, db_path, dry_run=True)
    
    # Ask for confirmation
    response = input("\nDo you want to proceed with the cleanup? (yes/no): ").lower().strip()
    
    if response == 'yes':
        cleanup_corrupted_files(corrupted_files, db_entries, db_path, dry_run=False)
        print("\n🎉 Cleanup completed successfully!")
        print("   Your image loading errors should now be resolved.")
    else:
        print("\n🚫 Cleanup cancelled. No files were deleted.")

if __name__ == "__main__":
    main()
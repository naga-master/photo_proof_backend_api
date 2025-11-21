#!/usr/bin/env python3
"""Fix storage paths to include /originals/ subdirectory"""

import sqlite3
from pathlib import Path

db_path = "photo_proof.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all photos without /originals/ in path
cursor.execute("""
    SELECT id, storage_path 
    FROM photos 
    WHERE storage_path LIKE 'projects/%' 
    AND storage_path NOT LIKE '%/originals/%'
    AND storage_path NOT LIKE '%/versions/%'
""")

photos = cursor.fetchall()
print(f"Found {len(photos)} photos to fix")

for photo_id, old_path in photos:
    # Parse path: projects/10/20251116_file.jpg -> projects/10/originals/20251116_file.jpg
    parts = old_path.split('/')
    if len(parts) >= 3:
        project_folder = parts[1]  # "10"
        filename = '/'.join(parts[2:])  # "20251116_file.jpg"
        new_path = f"projects/{project_folder}/originals/{filename}"
        
        cursor.execute("UPDATE photos SET storage_path = ? WHERE id = ?", (new_path, photo_id))
        print(f"✓ Photo {photo_id}: {old_path} → {new_path}")

conn.commit()
print(f"\n✅ Updated {len(photos)} photos")

# Verify
cursor.execute("SELECT id, storage_path FROM photos WHERE id IN (797, 798, 808, 809, 810, 811)")
print("\nSample results:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()

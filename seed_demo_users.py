"""Simple script to seed demo users for testing login."""

import sqlite3
import bcrypt
from uuid import uuid4

# Database path
DB_PATH = "photo_proof.db"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Seeding Demo Users for Photo Proof")
    print("=" * 60)
    
    # Check if studio@admin.com user exists
    cursor.execute("SELECT id, studio_id FROM users WHERE email = 'studio@admin.com'")
    result = cursor.fetchone()
    
    if result:
        print(f"✓ Studio admin user already exists (studio@admin.com)")
        user_id, studio_id = result
    else:
        # Get the demo studio
        cursor.execute("SELECT id FROM studios WHERE email = 'studio@photoproof.com' LIMIT 1")
        studio_result = cursor.fetchone()
        
        if not studio_result:
            print("✗ No studio found - please create a studio first")
            return
        
        studio_id = studio_result[0]
        user_id = str(uuid4())
        
        # Create studio admin user
        password_hash = hash_password("password123")
        cursor.execute("""
            INSERT INTO users (id, studio_id, name, email, username, password_hash, role, is_active, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (user_id, studio_id, "Studio Admin", "studio@admin.com", "studio@admin.com", password_hash, "studio_owner", 1, 0))
        
        conn.commit()
        print(f"✓ Created studio admin user: studio@admin.com / password123")
    
    # Create client users
    clients_data = [
        ("Emily & James", "emily.james@email.com", "wedding2024", "+1234567891"),
        ("Sarah Thompson", "sarah.t@email.com", "portraits", "+1234567892"),
        ("Mike & Jessica", "mike.jess@email.com", "engagement", "+1234567893"),
    ]
    
    print("\nCreating client users...")
    for name, email, password, phone in clients_data:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"  ✓ {email} already exists")
            continue
        
        user_id = str(uuid4())
        client_id = cursor.lastrowid + 1  # AUTO INCREMENT for INTEGER PRIMARY KEY
        password_hash = hash_password(password)
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (id, studio_id, name, email, username, password_hash, role, is_active, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (user_id, studio_id, name, email, email, password_hash, "client", 1, 0))
        
        # Insert client
        cursor.execute("""
            INSERT INTO clients (studio_id, user_id, name, email, phone, whatsapp_opt_in, email_opt_in, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (studio_id, user_id, name, email, phone, 0, 1, "active"))
        
        conn.commit()
        print(f"  ✓ Created {email} / {password}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("Demo users created successfully!")
    print("=" * 60)
    print("\nYou can now login with:")
    print("  Studio: studio@admin.com / password123")
    print("  Client 1: emily.james@email.com / wedding2024")
    print("  Client 2: sarah.t@email.com / portraits")
    print("  Client 3: mike.jess@email.com / engagement")

if __name__ == "__main__":
    main()

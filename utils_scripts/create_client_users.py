"""
Create user accounts for all clients who don't have one yet.
Sets password to 'OldClient' for all clients.
"""
from datetime import datetime
import uuid
import bcrypt
from sqlalchemy import text

from app.db import models
from app.db.session import session_scope

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_client_users():
    """Create user accounts for clients without user_id."""
    
    with session_scope() as session:
        # Get all clients without user_id
        clients = session.query(models.Client).filter(
            models.Client.user_id.is_(None)
        ).all()
        
        if not clients:
            print("✓ All clients already have user accounts!")
            return
        
        print(f"Found {len(clients)} clients without user accounts")
        print("-" * 80)
        
        password = "OldClient"
        password_hash = hash_password(password)
        
        created_count = 0
        
        for client in clients:
            try:
                # Skip clients without email
                if not client.email:
                    print(f"⚠ Skipping client ID {client.id}: No email")
                    continue
                
                # Check if user already exists with this email
                existing_user = session.query(models.User).filter(
                    models.User.email == client.email
                ).first()
                
                if existing_user:
                    # Link existing user to client
                    client.user_id = existing_user.id
                    print(f"✓ Linked client '{client.name}' to existing user {existing_user.email}")
                else:
                    # Create new user
                    user_id = str(uuid.uuid4())
                    user = models.User(
                        id=user_id,
                        studio_id=client.studio_id,
                        name=client.name,
                        email=client.email,
                        username=client.email,  # Use email as username
                        password_hash=password_hash,
                        role="client",
                        is_active=True,
                        email_verified=False,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(user)
                    
                    # Link user to client
                    client.user_id = user_id
                    
                    print(f"✓ Created user account for '{client.name}' ({client.email})")
                    created_count += 1
                
            except Exception as e:
                print(f"✗ Error processing client '{client.name}': {e}")
                session.rollback()
                continue
        
        # Commit all changes
        session.commit()
        
        print("-" * 80)
        print(f"\n✅ Successfully created {created_count} new user accounts")
        print(f"   Password for all clients: {password}")
        
        # Show all clients with their user accounts
        print("\n" + "=" * 80)
        print("ALL CLIENTS:")
        print("=" * 80)
        
        all_clients = session.query(models.Client).all()
        for client in all_clients:
            if client.user_id:
                user = session.query(models.User).filter(
                    models.User.id == client.user_id
                ).first()
                status = "✓" if user else "✗"
                email = user.email if user else "N/A"
                print(f"{status} ID: {client.id:3} | {client.name:30} | {email:30}")
            else:
                print(f"✗ ID: {client.id:3} | {client.name:30} | NO USER ACCOUNT")

def update_demo_passwords():
    """Update existing demo client passwords to 'OldClient'."""
    
    with session_scope() as session:
        password = "OldClient"
        password_hash = hash_password(password)
        
        # Get demo clients (IDs 1-3)
        demo_emails = [
            "emily.james@email.com",
            "sarah.t@email.com", 
            "mike.jess@email.com"
        ]
        
        print("\n" + "=" * 80)
        print("UPDATING DEMO CLIENT PASSWORDS:")
        print("=" * 80)
        
        updated_count = 0
        
        for email in demo_emails:
            user = session.query(models.User).filter(
                models.User.email == email
            ).first()
            
            if user:
                user.password_hash = password_hash
                user.updated_at = datetime.utcnow()
                print(f"✓ Updated password for {email}")
                updated_count += 1
            else:
                print(f"✗ User not found: {email}")
        
        session.commit()
        
        print("-" * 80)
        print(f"✅ Updated {updated_count} demo client passwords")
        print(f"   New password: {password}")

if __name__ == "__main__":
    print("=" * 80)
    print("CLIENT USER ACCOUNT SETUP")
    print("=" * 80)
    print()
    
    # Step 1: Create user accounts for clients without them
    create_client_users()
    
    # Step 2: Update demo client passwords
    update_demo_passwords()
    
    print("\n" + "=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    print("\n📝 CREDENTIALS:")
    print("   - All clients can login with their email")
    print("   - Password: OldClient")
    print("\n🔐 Example logins:")
    print("   • emily.james@email.com / OldClient")
    print("   • sarah.t@email.com / OldClient")
    print("   • vicky@gmail.com / OldClient")
    print("=" * 80)

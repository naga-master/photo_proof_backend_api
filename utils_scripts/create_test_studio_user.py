"""
Create a test studio user for mobile app testing
Email: studio@example.com
Password: password123
"""
from datetime import datetime
import uuid
import bcrypt

from app.db import models
from app.db.session import session_scope

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_test_studio_user():
    """Create test studio user: studio@example.com / password123"""
    
    email = "studio@example.com"
    password = "password123"
    name = "Test Studio"
    studio_id = "test-studio-001"
    
    with session_scope() as session:
        # Check if user already exists
        existing_user = session.query(models.User).filter(
            models.User.email == email
        ).first()
        
        if existing_user:
            print(f"✓ Studio user already exists!")
            print(f"  Email: {existing_user.email}")
            print(f"  ID: {existing_user.id}")
            print(f"  Role: {existing_user.role}")
            print(f"\n  Updating password to 'password123'...")
            
            # Update password
            existing_user.password_hash = hash_password(password)
            existing_user.updated_at = datetime.utcnow()
            session.commit()
            
            print(f"  ✓ Password updated!")
            return existing_user.id
        
        # Create new studio user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        
        user = models.User(
            id=user_id,
            studio_id=studio_id,
            name=name,
            email=email,
            username=email,
            password_hash=password_hash,
            role="studio_owner",
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(user)
        session.commit()
        
        print(f"✓ Created test studio user!")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  ID: {user_id}")
        print(f"  Studio ID: {studio_id}")
        
        return user_id

def list_all_studio_users():
    """List all studio users in the database."""
    with session_scope() as session:
        studio_users = session.query(models.User).filter(
            models.User.role.in_(['studio_owner', 'studio', 'admin'])
        ).all()
        
        if not studio_users:
            print("\n⚠ No studio users found in database!")
            return
        
        print(f"\n{'='*80}")
        print("ALL STUDIO USERS:")
        print(f"{'='*80}")
        
        for user in studio_users:
            print(f"  • {user.email:40} | Role: {user.role:15} | ID: {user.id}")
        
        print(f"{'='*80}\n")

if __name__ == "__main__":
    print("=" * 80)
    print("CREATE TEST STUDIO USER")
    print("=" * 80)
    print()
    
    # Create the test studio user
    create_test_studio_user()
    
    # List all studio users
    list_all_studio_users()
    
    print("\n" + "=" * 80)
    print("✅ SETUP COMPLETE!")
    print("=" * 80)
    print("\n📝 STUDIO LOGIN CREDENTIALS:")
    print("   Email:    studio@example.com")
    print("   Password: password123")
    print("\n📝 CLIENT LOGIN CREDENTIALS:")
    print("   Email:    emily.james@email.com")
    print("   Password: OldClient")
    print("=" * 80)

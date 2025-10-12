from datetime import datetime
import uuid
import bcrypt

from app.db import models
from app.db.session import session_scope

"""

   •  Username (Email): olivia@freshlightstudio.com
   •  Password: password
   •  User ID: 878152f6-bd5b-41c1-b3e7-cc2d1d4ae966

"""
email = "john@elegantmoments.com"
password = "password"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
user_id = str(uuid.uuid4())

with session_scope() as session:
    existing = session.query(models.User).filter(models.User.email == email).first()
    if existing:
        print({"existing_user_id": existing.id})
    else:
        user = models.User(
            id=user_id,
            studio_id="studio-002",
            name="John Carter",
            email=email,
            password_hash=password_hash,
            role="studio_owner",
            avatar_url=None,
            phone=None,
            last_login_at=None,
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(user)
        print({"created_user_id": user_id})
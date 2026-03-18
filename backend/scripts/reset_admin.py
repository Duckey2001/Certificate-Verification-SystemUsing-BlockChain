#!/usr/bin/env python3
"""
Reset admin password and ensure admin user exists
"""

import os
import sys
from datetime import datetime
from passlib.context import CryptContext

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    db = SessionLocal()
    try:
        # Default admin credentials
        email = os.getenv("ADMIN_EMAIL", "letsapobokang.certivert@gmail.com")
        username = os.getenv("ADMIN_USERNAME", email)
        password = os.getenv("ADMIN_PASSWORD", "mpho10//")

        # Check if admin exists
        existing = db.query(User).filter(User.email == email).first()
        
        if existing:
            # Update password
            existing.password_hash = pwd_context.hash(password)
            existing.username = username
            existing.role = "admin"
            existing.updated_at = datetime.now()
            db.commit()
            print(f"✅ Updated admin user: {email}")
        else:
            # Create new admin
            user = User(
                username=username,
                email=email,
                password_hash=pwd_context.hash(password),
                role="admin",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created admin user: {email}")
        
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print("🎯 Login at /login with these credentials.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

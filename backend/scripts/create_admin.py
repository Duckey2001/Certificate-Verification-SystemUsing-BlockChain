#!/usr/bin/env python3
"""Create an initial admin user. Run from project root: python -m scripts.create_admin"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import User
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    db = SessionLocal()
    try:
        # Default admin credentials (can be overridden via env vars)
        email = os.getenv("ADMIN_EMAIL", "letsapobokang.certivert@gmail.com")
        username = os.getenv("ADMIN_USERNAME", email)
        password = os.getenv("ADMIN_PASSWORD", "mpho10//")

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Admin user '{username}' already exists (id={existing.id})")
            return

        user = User(
            username=username,
            email=email,
            password_hash=pwd_context.hash(password),
            role="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created admin user: {username} (id={user.id})")
        print("Login at /login with these credentials.")
    finally:
        db.close()

if __name__ == "__main__":
    main()

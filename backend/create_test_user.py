#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/duckey/lgcse-project/backend')

from database import SessionLocal, engine
from models import Base, User
from auth import get_password_hash
import traceback

def main():
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print('Tables created successfully')
        
        print("Creating test user...")
        db = SessionLocal()
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == 'mpholekunye6@gmail.com').first()
        if not existing_user:
            user = User(
                username='mpholekunye6',
                email='mpholekunye6@gmail.com',
                password_hash=get_password_hash('test123'),
                role='issuer'
            )
            db.add(user)
            db.commit()
            print('✅ Test user created: mpholekunye6@gmail.com')
        else:
            print('ℹ️ Test user already exists:', existing_user.email)
        
        # Check all users
        users = db.query(User).all()
        print(f'📊 Total users: {len(users)}')
        for u in users:
            print(f'  - {u.username} ({u.email}) - {u.role}')
        
        db.close()
        print("✅ Script completed successfully")
        
    except Exception as e:
        print(f'❌ Error: {e}')
        traceback.print_exc()

if __name__ == "__main__":
    main()

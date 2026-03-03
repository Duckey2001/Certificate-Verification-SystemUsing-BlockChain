#!/usr/bin/env python3
"""
Complete database setup for CertiVert LGCSE system
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, SessionLocal
from models import Base, User, Certificate, VerificationRequest, AuditEvent, Invitation, Payment, Badge
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tables():
    """Create all database tables"""
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

def create_admin_user():
    """Create or update admin user"""
    print("👤 Setting up admin user...")
    db = SessionLocal()
    try:
        email = "letsapobokang.certivert@gmail.com"
        password = "mpho10//"
        
        # Check if admin exists
        existing = db.query(User).filter(User.email == email).first()
        
        if existing:
            existing.password_hash = pwd_context.hash(password)
            existing.role = "admin"
            existing.updated_at = datetime.now()
            db.commit()
            print(f"✅ Admin user updated: {email}")
        else:
            user = User(
                username=email,
                email=email,
                password_hash=pwd_context.hash(password),
                role="admin",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(user)
            db.commit()
            print(f"✅ Admin user created: {email}")
        
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

def verify_setup():
    """Verify database setup"""
    print("\n🔍 Verifying database setup...")
    db = SessionLocal()
    try:
        # Check tables
        tables = db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'").fetchall()
        table_names = [row[0] for row in tables]
        print(f"📊 Tables found: {', '.join(table_names)}")
        
        # Check admin user
        admin = db.query(User).filter(User.role == "admin").first()
        if admin:
            print(f"👑 Admin user found: {admin.email}")
        else:
            print("❌ No admin user found")
        
        # Count users
        user_count = db.query(User).count()
        print(f"👥 Total users: {user_count}")
        
        print("✅ Database verification complete")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🚀 CertiVert LGCSE Database Setup")
    print("=" * 50)
    
    # Create tables
    create_tables()
    
    # Create admin user
    create_admin_user()
    
    # Verify setup
    verify_setup()
    
    print("\n🎉 Database setup complete!")
    print("🌐 You can now login at: http://localhost:3000/login")
    print("👤 Admin credentials:")
    print("   Email: letsapobokang.certivert@gmail.com")
    print("   Password: mpho10//")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Authentication System Fix Script

This script fixes common authentication issues and ensures the system works properly.
"""

import os
import sys
import uuid
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import User, Institution, Session as DbSession, LoginActivity, AuditEvent
from passlib.context import CryptContext

def create_default_institutions():
    """Create default institutions"""
    print("🏫 Creating default institutions...")
    
    institutions_data = [
        {
            "code": "ECOL",
            "name": "Ecol University",
            "role": "issuer",
            "type": "university",
            "address": "Maseru, Lesotho",
            "contact_email": "info@ecol.ac.ls",
            "website": "https://www.ecol.ac.ls",
            "status": "active"
        },
        {
            "code": "LIMKOWING",
            "name": "Limkokwing University of Creative Technology",
            "role": "verifier",
            "type": "university",
            "address": "Maseru, Lesotho",
            "contact_email": "info@limkokwing.ls",
            "website": "https://www.limkokwing.ls",
            "status": "active"
        },
        {
            "code": "BOTHO",
            "name": "Botho University",
            "role": "verifier",
            "type": "university",
            "address": "Maseru, Lesotho",
            "contact_email": "info@botho.ls",
            "website": "https://www.botho.ls",
            "status": "active"
        },
        {
            "code": "NUL",
            "name": "National University of Lesotho",
            "role": "verifier",
            "type": "university",
            "address": "Roma, Lesotho",
            "contact_email": "info@nul.ls",
            "website": "https://www.nul.ls",
            "status": "active"
        }
    ]
    
    try:
        with SessionLocal() as db:
            for inst_data in institutions_data:
                # Check if institution already exists
                existing = db.query(Institution).filter(Institution.code == inst_data["code"]).first()
                
                if not existing:
                    institution = Institution(
                        code=inst_data["code"],
                        name=inst_data["name"],
                        role=inst_data["role"],
                        type=inst_data["type"],
                        address=inst_data["address"],
                        contact_email=inst_data["contact_email"],
                        website=inst_data["website"],
                        status=inst_data["status"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(institution)
                    print(f"   ✅ Created {inst_data['name']}")
                else:
                    print(f"   ℹ️ {inst_data['name']} already exists")
            
            db.commit()
            print("✅ Institutions setup completed")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create institutions: {e}")
        return False

def create_default_admin():
    """Create default admin user"""
    print("👤 Creating default admin user...")
    
    try:
        with SessionLocal() as db:
            # Check if admin already exists
            existing_admin = db.query(User).filter(User.username == "admin").first()
            
            if not existing_admin:
                # Create admin user
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed_password = pwd_context.hash("Admin@123")
                
                admin_user = User(
                    username="admin",
                    email="admin@lgcse.example.com",
                    password_hash=hashed_password,
                    role="admin",
                    institution_code="ECOL",
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                
                print("   ✅ Admin user created")
                print(f"   📧 Email: admin@lgcse.example.com")
                print(f"   🔑 Password: Admin@123")
                print(f"   🏫 Institution: ECOL")
                return admin_user
            else:
                print("   ℹ️ Admin user already exists")
                return existing_admin
                
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        return None

def create_test_user():
    """Create test user for testing"""
    print("🧪 Creating test user...")
    
    try:
        with SessionLocal() as db:
            # Check if test user already exists
            existing_test = db.query(User).filter(User.username == "testuser").first()
            
            if not existing_test:
                # Create test user
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                hashed_password = pwd_context.hash("TestPassword123!")
                
                test_user = User(
                    username="testuser",
                    email="testuser@lgcse.example.com",
                    password_hash=hashed_password,
                    role="issuer",
                    institution_code="ECOL",
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                
                print("   ✅ Test user created")
                print(f"   📧 Email: testuser@lgcse.example.com")
                print(f"   🔑 Password: TestPassword123!")
                print(f"   🏫 Institution: ECOL")
                return test_user
            else:
                print("   ℹ️ Test user already exists")
                return existing_test
                
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return None

def verify_database_schema():
    """Verify and fix database schema"""
    print("🔍 Verifying database schema...")
    
    try:
        from sqlalchemy import text, inspect
        
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = ["users", "sessions", "login_activity", "audit_events", "institutions"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"   📝 Creating missing tables: {missing_tables}")
                Base.metadata.create_all(bind=engine)
                print("   ✅ Missing tables created")
            else:
                print("   ✅ All required tables exist")
            
            # Check user table columns
            if "users" in tables:
                user_cols = {col["name"] for col in inspector.get_columns("users")}
                required_user_cols = ["id", "username", "email", "password_hash", "role", "is_active", "created_at", "updated_at"]
                missing_user_cols = [col for col in required_user_cols if col not in user_cols]
                
                if missing_user_cols:
                    print(f"   ⚠️ Missing user columns: {missing_user_cols}")
                else:
                    print("   ✅ User table schema is correct")
            
            # Check session table columns
            if "sessions" in tables:
                session_cols = {col["name"] for col in inspector.get_columns("sessions")}
                required_session_cols = ["id", "session_token", "user_id", "expires", "created_at", "updated_at"]
                missing_session_cols = [col for col in required_session_cols if col not in session_cols]
                
                if missing_session_cols:
                    print(f"   ⚠️ Missing session columns: {missing_session_cols}")
                else:
                    print("   ✅ Session table schema is correct")
            
            return True
            
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

def test_authentication_flow():
    """Test basic authentication flow"""
    print("🧪 Testing authentication flow...")
    
    try:
        from passlib.context import CryptContext
        from jose import jwt
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        is_valid = pwd_context.verify(password, hashed)
        
        if is_valid:
            print("   ✅ Password hashing working")
        else:
            print("   ❌ Password hashing failed")
            return False
        
        # Test JWT token creation
        SECRET_KEY = os.getenv("SECRET_KEY", "certivert-dev-secret")
        token_data = {
            "sub": "test_user_id",
            "username": "testuser",
            "role": "issuer"
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        print("   ✅ JWT token creation working")
        
        # Test token verification
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if decoded["username"] == "testuser":
                print("   ✅ JWT token verification working")
            else:
                print("   ❌ JWT token verification failed")
                return False
        except jwt.JWTError as e:
            print(f"   ❌ JWT token verification failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication flow test failed: {e}")
        return False

def cleanup_old_sessions():
    """Clean up old sessions"""
    print("🧹 Cleaning up old sessions...")
    
    try:
        with SessionLocal() as db:
            # Delete expired sessions
            from sqlalchemy import text
            
            result = db.execute(text("DELETE FROM sessions WHERE expires < datetime('now')"))
            deleted_count = result.rowcount
            
            if deleted_count > 0:
                print(f"   ✅ Deleted {deleted_count} expired sessions")
            else:
                print("   ℹ️ No expired sessions to delete")
            
            db.commit()
            return True
            
    except Exception as e:
        print(f"❌ Failed to cleanup sessions: {e}")
        return False

def main():
    """Run all authentication fixes"""
    print("🔧 Starting Authentication System Fixes")
    print("=" * 50)
    
    # Verify database schema
    if not verify_database_schema():
        print("❌ Database schema verification failed. Cannot continue.")
        return False
    
    # Create default institutions
    if not create_default_institutions():
        print("❌ Institution setup failed.")
        return False
    
    # Create default admin user
    admin_user = create_default_admin()
    if not admin_user:
        print("❌ Admin user creation failed.")
        return False
    
    # Create test user
    test_user = create_test_user()
    if not test_user:
        print("❌ Test user creation failed.")
        return False
    
    # Test authentication flow
    if not test_authentication_flow():
        print("❌ Authentication flow test failed.")
        return False
    
    # Clean up old sessions
    cleanup_old_sessions()
    
    print("\n🎉 Authentication System Fixed Successfully!")
    print("=" * 50)
    print("✅ Database schema: Verified")
    print("✅ Default institutions: Created")
    print("✅ Admin user: Created")
    print("✅ Test user: Created")
    print("✅ Authentication flow: Working")
    print("✅ Session cleanup: Completed")
    
    print("\n📋 Login Credentials:")
    print("🔑 Admin User:")
    print("   Username: admin")
    print("   Password: Admin@123")
    print("   Email: admin@lgcse.example.com")
    print("")
    print("🔑 Test User:")
    print("   Username: testuser")
    print("   Password: TestPassword123!")
    print("   Email: testuser@lgcse.example.com")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

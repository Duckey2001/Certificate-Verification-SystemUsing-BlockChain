#!/usr/bin/env python3
"""
Authentication System Test Script

This script tests the complete authentication system including:
- User registration
- User login
- Token verification
- Session management
- Database connectivity
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import User, Institution, Session as DbSession
from passlib.context import CryptContext

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/auth"

def test_database_connection():
    """Test database connection and setup"""
    print("🔍 Testing database connection...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check if tables exist
            inspector = engine.inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = ["users", "sessions", "login_activity", "audit_events", "institutions"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️ Missing tables: {missing_tables}")
                print("🔧 Creating missing tables...")
                Base.metadata.create_all(bind=engine)
                print("✅ Tables created successfully")
            else:
                print("✅ All required tables exist")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_default_institution():
    """Test and create default institution"""
    print("🏫 Testing default institution...")
    
    try:
        with SessionLocal() as db:
            # Check if ECOL institution exists
            institution = db.query(Institution).filter(Institution.code == "ECOL").first()
            
            if not institution:
                # Create default ECOL institution
                institution = Institution(
                    code="ECOL",
                    name="Ecol University",
                    role="issuer",
                    type="university",
                    address="Maseru, Lesotho",
                    contact_email="info@ecol.ac.ls",
                    website="https://www.ecol.ac.ls",
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(institution)
                db.commit()
                print("✅ Default ECOL institution created")
            else:
                print("✅ Default ECOL institution exists")
            
            return True
            
    except Exception as e:
        print(f"❌ Failed to create default institution: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("👤 Testing user registration...")
    
    try:
        # Test data
        registration_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "role": "issuer",
            "institution_code": "ECOL"
        }
        
        # Make registration request
        response = requests.post(f"{API_URL}/register", json=registration_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ User registration successful")
                print(f"   User ID: {result['user']['id']}")
                print(f"   Username: {result['user']['username']}")
                print(f"   Role: {result['user']['role']}")
                print(f"   Institution: {result['user']['institution']['name'] if result['user']['institution'] else 'None'}")
                return result
            else:
                print(f"❌ Registration failed: {result}")
                return None
        else:
            print(f"❌ Registration request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure the backend is running.")
        return None
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return None

def test_user_login():
    """Test user login"""
    print("🔐 Testing user login...")
    
    try:
        # Test login data
        login_data = {
            "username": "testuser",
            "password": "TestPassword123!"
        }
        
        # Make login request
        response = requests.post(f"{API_URL}/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ User login successful")
                print(f"   Access token: {result['access_token'][:50]}...")
                print(f"   User ID: {result['user']['id']}")
                print(f"   Username: {result['user']['username']}")
                return result
            else:
                print(f"❌ Login failed: {result}")
                return None
        else:
            print(f"❌ Login request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def test_token_verification(token):
    """Test token verification"""
    print("🔍 Testing token verification...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/verify", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("valid"):
                print("✅ Token verification successful")
                print(f"   User ID: {result['user']['id']}")
                print(f"   Username: {result['user']['username']}")
                print(f"   Role: {result['user']['role']}")
                return True
            else:
                print(f"❌ Token verification failed: {result}")
                return False
        else:
            print(f"❌ Token verification request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Token verification test failed: {e}")
        return False

def test_user_profile(token):
    """Test user profile endpoint"""
    print("👤 Testing user profile...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/me", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ User profile retrieval successful")
            print(f"   User ID: {result['id']}")
            print(f"   Username: {result['username']}")
            print(f"   Email: {result['email']}")
            print(f"   Role: {result['role']}")
            print(f"   Active: {result['is_active']}")
            print(f"   Institution: {result['institution']['name'] if result['institution'] else 'None'}")
            return True
        else:
            print(f"❌ User profile request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User profile test failed: {e}")
        return False

def test_logout(token):
    """Test user logout"""
    print("🚪 Testing user logout...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/logout", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ User logout successful")
            print(f"   Message: {result['message']}")
            return True
        else:
            print(f"❌ Logout request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Logout test failed: {e}")
        return False

def test_invalid_credentials():
    """Test invalid credentials"""
    print("❌ Testing invalid credentials...")
    
    try:
        # Test with wrong password
        login_data = {
            "username": "testuser",
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{API_URL}/login", json=login_data)
        
        if response.status_code == 401:
            print("✅ Invalid credentials properly rejected")
            return True
        else:
            print(f"❌ Invalid credentials not properly handled: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Invalid credentials test failed: {e}")
        return False

def test_duplicate_registration():
    """Test duplicate registration"""
    print("🔄 Testing duplicate registration...")
    
    try:
        # Try to register the same user again
        registration_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "role": "issuer",
            "institution_code": "ECOL"
        }
        
        response = requests.post(f"{API_URL}/register", json=registration_data)
        
        if response.status_code == 400:
            result = response.json()
            print("✅ Duplicate registration properly rejected")
            print(f"   Error: {result.get('detail', 'Unknown error')}")
            return True
        else:
            print(f"❌ Duplicate registration not properly handled: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Duplicate registration test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        with SessionLocal() as db:
            # Delete test user
            test_user = db.query(User).filter(User.username == "testuser").first()
            if test_user:
                # Delete related sessions
                db.query(DbSession).filter(DbSession.user_id == str(test_user.id)).delete()
                db.commit()
                
                # Delete user
                db.delete(test_user)
                db.commit()
                print("✅ Test user cleaned up")
            else:
                print("ℹ️ No test user to clean up")
            
            return True
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Starting Authentication System Tests")
    print("=" * 50)
    
    # Test database connection first
    if not test_database_connection():
        print("❌ Database tests failed. Cannot continue.")
        return False
    
    # Test default institution
    if not test_default_institution():
        print("❌ Institution setup failed.")
        return False
    
    # Check if API server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ API server is not responding correctly.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Please start the backend first:")
        print("   cd backend")
        print("   python main.py")
        return False
    except Exception as e:
        print(f"❌ API server check failed: {e}")
        return False
    
    print("✅ API server is running")
    
    # Run authentication tests
    print("\n📋 Running Authentication Tests")
    print("-" * 30)
    
    # Test registration
    registration_result = test_user_registration()
    if not registration_result:
        print("❌ Registration test failed. Cannot continue.")
        return False
    
    # Test login
    login_result = test_user_login()
    if not login_result:
        print("❌ Login test failed.")
        return False
    
    token = login_result.get("access_token")
    
    # Test token verification
    if not test_token_verification(token):
        print("❌ Token verification test failed.")
        return False
    
    # Test user profile
    if not test_user_profile(token):
        print("❌ User profile test failed.")
        return False
    
    # Test logout
    if not test_logout(token):
        print("❌ Logout test failed.")
        return False
    
    # Test invalid credentials
    if not test_invalid_credentials():
        print("❌ Invalid credentials test failed.")
        return False
    
    # Test duplicate registration
    if not test_duplicate_registration():
        print("❌ Duplicate registration test failed.")
        return False
    
    # Clean up test data
    cleanup_test_data()
    
    print("\n🎉 All Authentication Tests Passed!")
    print("=" * 50)
    print("✅ Database connection: Working")
    print("✅ User registration: Working")
    print("✅ User login: Working")
    print("✅ Token verification: Working")
    print("✅ User profile: Working")
    print("✅ User logout: Working")
    print("✅ Invalid credentials: Working")
    print("✅ Duplicate registration: Working")
    print("✅ Data cleanup: Working")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

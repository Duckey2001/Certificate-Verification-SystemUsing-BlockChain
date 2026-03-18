#!/usr/bin/env python3
"""
Test script for enhanced authentication system
Tests all authentication methods and features
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_enhanced_registration():
    """Test enhanced user registration"""
    print("🧪 Testing Enhanced Registration...")
    
    test_user = {
        "username": "testuser_enhanced",
        "email": "testenhanced@example.com",
        "password": "TestPassword123!",
        "role": "issuer",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+26612345678"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            print(f"User ID: {data['user']['id']}")
            print(f"Profile completion: {data['user']['profile_completion_score']}")
            return data['access_token']
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_enhanced_login():
    """Test enhanced login with device tracking"""
    print("\n🧪 Testing Enhanced Login...")
    
    login_data = {
        "username": "testuser_enhanced",
        "password": "TestPassword123!",
        "remember_me": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Expires in: {data['expires_in']} seconds")
            print(f"OAuth provider: {data['user']['oauth_provider']}")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_profile_update(token):
    """Test profile update with audit logging"""
    print("\n🧪 Testing Profile Update...")
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "bio": "Updated bio for testing",
        "department": "Computer Science",
        "language_preference": "fr",
        "timezone": "Africa/Maseru"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/auth/profile", json=update_data, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile update successful!")
            print(f"New profile completion: {data['profile_completion_score']}")
        else:
            print(f"❌ Profile update failed: {response.text}")
    except Exception as e:
        print(f"❌ Profile update error: {e}")

def test_get_profile(token):
    """Test getting user profile"""
    print("\n🧪 Testing Get Profile...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Get profile successful!")
            print(f"Username: {data['username']}")
            print(f"Email: {data['email']}")
            print(f"Role: {data['role']}")
            print(f"Profile completion: {data['profile_completion_score']}")
        else:
            print(f"❌ Get profile failed: {response.text}")
    except Exception as e:
        print(f"❌ Get profile error: {e}")

def test_logout(token):
    """Test enhanced logout"""
    print("\n🧪 Testing Enhanced Logout...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Logout successful!")
        else:
            print(f"❌ Logout failed: {response.text}")
    except Exception as e:
        print(f"❌ Logout error: {e}")

def test_google_oauth():
    """Test Google OAuth (simulated)"""
    print("\n🧪 Testing Google OAuth...")
    
    oauth_data = {
        "access_token": "simulated_google_token",
        "refresh_token": "simulated_refresh_token",
        "id_token": "simulated_id_token"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/google-auth", json=oauth_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Google OAuth successful!")
            print(f"OAuth provider: {data['user']['oauth_provider']}")
            return data['access_token']
        else:
            print(f"❌ Google OAuth failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Google OAuth error: {e}")
        return None

def test_database_connection():
    """Test database connection and schema"""
    print("\n🧪 Testing Database Connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Database connection successful!")
        else:
            print(f"❌ Database connection failed: {response.text}")
    except Exception as e:
        print(f"❌ Database connection error: {e}")

def main():
    """Run all authentication tests"""
    print("🚀 Starting Enhanced Authentication Tests")
    print("=" * 50)
    
    # Test database connection first
    test_database_connection()
    
    # Test registration
    token = test_enhanced_registration()
    
    if token:
        # Test profile operations
        test_get_profile(token)
        test_profile_update(token)
        test_get_profile(token)  # Check updated profile
        
        # Test logout
        test_logout(token)
    
    # Test login
    login_token = test_enhanced_login()
    
    if login_token:
        test_get_profile(login_token)
        test_logout(login_token)
    
    # Test Google OAuth
    google_token = test_google_oauth()
    
    if google_token:
        test_get_profile(google_token)
        test_logout(google_token)
    
    print("\n" + "=" * 50)
    print("🏁 Authentication Tests Complete!")

if __name__ == "__main__":
    main()

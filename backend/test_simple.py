#!/usr/bin/env python3
"""Simple test to verify backend is working"""

import requests
import json

def test_backend():
    base_url = "http://localhost:8000"
    
    print("Testing Backend Connection...")
    print("=" * 40)
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test login with JSON data (enhanced_auth endpoint)
    try:
        login_data = {
            "username": "admin",
            "password": "Admin@123"
        }
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,  # Use json= for JSON data
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Login endpoint (JSON): {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Login endpoint (JSON) failed: {e}")
    
    # Test login with form data (main.py endpoint)
    try:
        login_data = {
            "username": "admin",
            "password": "Admin@123"
        }
        response = requests.post(
            f"{base_url}/api/auth/login",
            data=login_data,  # Use data= for form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"✅ Login endpoint (form): {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Login endpoint (form) failed: {e}")
    
    # Test CORS
    try:
        response = requests.options(
            f"{base_url}/api/auth/me",
            headers={"Origin": "http://localhost:3000"}
        )
        cors_headers = {
            key: value for key, value in response.headers.items()
            if 'access-control' in key.lower() or 'cors' in key.lower()
        }
        print(f"✅ CORS headers: {cors_headers}")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")

if __name__ == "__main__":
    test_backend()

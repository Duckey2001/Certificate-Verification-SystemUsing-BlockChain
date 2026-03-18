#!/usr/bin/env python3
"""
Test script for OCR functionality with authentication
"""

import requests
import json

def get_auth_token():
    """Get authentication token"""
    
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "username": "issuer_ecol",
        "password": "password123"  # This might need to be adjusted
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            result = response.json()
            return result.get("access_token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return None

def test_ocr_endpoint():
    """Test the OCR extraction endpoint with authentication"""
    
    # Get auth token first
    print("🔐 Getting authentication token...")
    token = get_auth_token()
    
    if not token:
        print("❌ Failed to get authentication token")
        return
    
    print("✅ Authentication successful!")
    
    # Test file path
    test_file_path = "/home/duckey/lgcse-project/backend/uploads/certificates/dc942112-b126-4f19-a49f-a36bc26a0b8f.jpeg"
    
    # API endpoint
    url = "http://localhost:8000/api/certificates/extract-data"
    
    # Headers with auth token
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Read the test file
        with open(test_file_path, "rb") as f:
            files = {"file": f}
            
            print(f"\n🔍 Testing OCR endpoint with: {test_file_path}")
            print(f"📡 Sending request to: {url}")
            
            # Make the request
            response = requests.post(url, files=files, headers=headers)
            
            print(f"📊 Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OCR Success!")
                print(f"📋 Response JSON: {json.dumps(result, indent=2)}")
                
                # Check if we have extracted data
                if "data" in result:
                    data = result["data"]
                    if "extracted_fields" in data:
                        print("\n🎯 Extracted Fields:")
                        for key, value in data["extracted_fields"].items():
                            print(f"  {key}: {value}")
                    
                    if "validation" in data:
                        print(f"\n📈 Validation Confidence: {data['validation'].get('confidence', 'N/A')}")
                
            else:
                print("❌ OCR Failed!")
                print(f"🚫 Error Response: {response.text}")
                
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file_path}")
    except Exception as e:
        print(f"❌ Error during OCR test: {str(e)}")

if __name__ == "__main__":
    test_ocr_endpoint()

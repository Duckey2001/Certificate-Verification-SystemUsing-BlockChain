#!/usr/bin/env python3
"""
Test full OCR API with proper authentication
"""

import requests
import json

def get_auth_token():
    """Get authentication token for test user"""
    
    login_url = "http://localhost:8000/api/auth/login"
    
    # Try different test credentials
    test_credentials = [
        {"username": "issuer_ecol", "password": "password123"},
        {"username": "testuser", "password": "password123"},
        {"username": "letsapobokang.certivert@gmail.com", "password": "password123"}
    ]
    
    for creds in test_credentials:
        try:
            print(f"🔐 Trying login with: {creds['username']}")
            response = requests.post(login_url, json=creds)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Login successful!")
                return result.get("access_token")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
    
    return None

def test_ocr_api():
    """Test the complete OCR API flow"""
    
    # Get auth token
    token = get_auth_token()
    
    if not token:
        print("❌ Could not authenticate with any test user")
        print("💡 You may need to check the database for correct credentials")
        return
    
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
            
            print(f"\n🔍 Testing OCR API with: {test_file_path}")
            print(f"📡 Sending request to: {url}")
            
            # Make the request
            response = requests.post(url, files=files, headers=headers)
            
            print(f"📊 Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OCR API Success!")
                
                # Show key results
                if "data" in result:
                    data = result["data"]
                    
                    print("\n🎯 Key Extracted Fields:")
                    extracted = data.get("extracted_fields", {})
                    for key in ["student_name", "date_of_birth", "institution", "examination_session", "lgcse_number"]:
                        value = extracted.get(key, "Not found")
                        print(f"  {key}: {value}")
                    
                    # Show subjects
                    subjects = extracted.get("subjects", [])
                    if subjects:
                        print(f"\n📚 Subjects Found ({len(subjects)}):")
                        for subject in subjects:
                            print(f"  {subject.get('subject_name', 'Unknown')}: {subject.get('grade', 'N/A')}")
                    
                    # Show validation
                    validation = data.get("validation", {})
                    confidence = validation.get("confidence", 0)
                    print(f"\n📈 Validation Confidence: {confidence}%")
                    
                    if confidence > 80:
                        print("🎉 High confidence extraction - ready for form auto-fill!")
                    elif confidence > 60:
                        print("⚠️ Medium confidence - manual review recommended")
                    else:
                        print("❌ Low confidence - manual entry required")
                
            else:
                print("❌ OCR API Failed!")
                print(f"🚫 Error Response: {response.text}")
                
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file_path}")
    except Exception as e:
        print(f"❌ Error during OCR API test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_api()

#!/usr/bin/env python3
"""
Test script for OCR functionality
"""

import requests
import json

def test_ocr_endpoint():
    """Test the OCR extraction endpoint"""
    
    # Test file path
    test_file_path = "/home/duckey/lgcse-project/backend/uploads/certificates/dc942112-b126-4f19-a49f-a36bc26a0b8f.jpeg"
    
    # API endpoint
    url = "http://localhost:8000/api/certificates/extract-data"
    
    # Headers (you'll need to add auth token in a real scenario)
    headers = {
        "Accept": "application/json"
    }
    
    try:
        # Read the test file
        with open(test_file_path, "rb") as f:
            files = {"file": f}
            
            print(f"Testing OCR endpoint with: {test_file_path}")
            print(f"Sending request to: {url}")
            
            # Make the request
            response = requests.post(url, files=files, headers=headers)
            
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OCR Success!")
                print(f"Response JSON: {json.dumps(result, indent=2)}")
            else:
                print("❌ OCR Failed!")
                print(f"Error Response: {response.text}")
                
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file_path}")
    except Exception as e:
        print(f"❌ Error during OCR test: {str(e)}")

if __name__ == "__main__":
    test_ocr_endpoint()

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_complete_ussd_flow():
    """Test complete USSD flow"""
    
    print("\n" + "="*60)
    print("🧪 Testing Complete USSD Payment Flow")
    print("="*60)
    
    # Step 1: Initiate USSD
    print("\n📱 Step 1: Initiate USSD Push")
    response = requests.post(f"{BASE_URL}/api/ussd/initiate", json={
        "certificate_ref": "CERT-2024-001",
        "university_name": "National University of Lesotho",
        "amount": 5000  # 50.00 LSL
    })
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    ussd_session_id = result['ussd_session_id']
    
    # Step 2: Enter Phone Number
    print("\n📱 Step 2: Enter Phone Number")
    time.sleep(1)
    response = requests.post(f"{BASE_URL}/api/ussd/enter-phone", json={
        "ussd_session_id": ussd_session_id,
        "phone_number": "26657620256"  # Full Lesotho format
    })
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    # Step 3: Send PIN (SMS)
    print("\n📱 Step 3: Send PIN via SMS")
    time.sleep(1)
    response = requests.post(f"{BASE_URL}/api/ussd/send-pin", json={
        "ussd_session_id": ussd_session_id
    })
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    pin_session_id = result['pin_session_id']
    
    # Step 4: Verify PIN
    print("\n📱 Step 4: Verify PIN")
    print("   ⚠️  Check console for the generated PIN (it appears in logs)")
    pin = input("   Enter the PIN shown in server logs: ")
    
    response = requests.post(f"{BASE_URL}/api/ussd/verify-pin", json={
        "ussd_session_id": ussd_session_id,
        "pin": pin
    })
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    payment_id = result.get('payment_id')
    
    # Step 5: Process Payment
    if payment_id:
        print("\n💳 Step 5: Process Payment")
        time.sleep(1)
        response = requests.post(f"{BASE_URL}/api/ussd/process-payment", json={
            "payment_id": payment_id
        })
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
    
    # Check final status
    print("\n📊 Step 6: Check Session Status")
    response = requests.get(f"{BASE_URL}/api/ussd/status/{ussd_session_id}")
    result = response.json()
    print(f"   Status: {json.dumps(result, indent=2)}")
    
    print("\n" + "="*60)
    print("✅ Test Complete")
    print("="*60)

if __name__ == '__main__':
    test_complete_ussd_flow()

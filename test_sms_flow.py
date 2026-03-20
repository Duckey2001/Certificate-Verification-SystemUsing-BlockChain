import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_sms_payment_flow():
    """Test complete SMS-based payment flow"""
    
    print("\n" + "="*60)
    print("🧪 Testing SMS-Based Payment Flow")
    print("="*60)
    
    # Step 1: Initiate payment from your app
    print("\n📱 Step 1: User enters phone number in app")
    print("   Your app calls POST /api/payment/initiate")
    
    response = requests.post(f"{BASE_URL}/api/payment/initiate", json={
        "phone_number": "26657620256",  # Your preferred number
        "certificate_ref": "CERT-2024-001",
        "university_name": "National University of Lesotho",
        "amount": 5000,  # 50.00 LSL
        "university_code": "UNI001"
    })
    
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    transaction_id = result.get('transaction_id')
    print(f"\n   ✅ Transaction ID: {transaction_id}")
    
    # Get PIN from pending transaction for testing
    print("\n📱 Step 2: Get PIN from server (simulating user receiving SMS)")
    
    pending_response = requests.get(f"{BASE_URL}/api/transactions")
    pending_data = pending_response.json()
    
    pin = None
    for tx in pending_data.get('pending', []):
        if tx.get('transaction_id') == transaction_id:
            pin = tx.get('pin')
            break
    
    if pin:
        print(f"   📱 User receives SMS with PIN: {pin}")
        
        # Step 3: Simulate user replying to SMS with PIN
        print("\n📱 Step 3: User replies to SMS with PIN")
        print(f"   User sends SMS: {pin}")
        
        response = requests.post(f"{BASE_URL}/api/payment/simulate-sms", json={
            "from_phone": "26657620256",
            "message": pin
        })
        
        print(f"   SMS reply simulated")
        
        # Wait for processing
        time.sleep(2)
        
        # Step 4: Check final status
        print("\n📱 Step 4: Check payment status")
        response = requests.get(f"{BASE_URL}/api/payment/status/{transaction_id}")
        final_status = response.json()
        
        print(f"   Final Status: {json.dumps(final_status, indent=2)}")
        
        if final_status.get('status') == 'completed':
            print("\n✅ Payment completed successfully!")
            print(f"   M-Pesa Transaction ID: {final_status.get('mpesa_transaction_id')}")
        else:
            print("\n❌ Payment failed")
    
    print("\n" + "="*60)
    print("✅ Test Complete")
    print("="*60)

if __name__ == '__main__':
    test_sms_payment_flow()

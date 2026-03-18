#!/usr/bin/env python3
"""
Direct M-Pesa Test - No authentication required for callback testing
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_mpesa_direct():
    """Test M-Pesa system directly"""
    
    print("🧪 Direct M-Pesa System Test")
    print("=" * 40)
    
    # Step 1: Check configuration
    print("🔧 Step 1: Checking M-Pesa configuration...")
    try:
        response = requests.get(f"{API_BASE}/api/mpesa/config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Server is running")
            print(f"📊 M-Pesa Configured: {'Yes' if config.get('configured') else 'No'}")
            print(f"🌍 Environment: {config.get('environment')}")
            print(f"💰 Currency: {config.get('currency')}")
            print(f"📱 Shortcode: {config.get('shortcode')}")
            print(f"📡 Callback URL: {config.get('callback_url')}")
        else:
            print(f"❌ Server not responding: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Step 2: Test callback simulation
    print("\n🔄 Step 2: Testing callback handling...")
    
    # Simulate successful payment callback
    success_callback = {
        "MerchantRequestID": "test_merchant_123456",
        "CheckoutRequestID": "test_checkout_123456", 
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "CallbackMetadata": {
            "Item": [
                {"Name": "Amount", "Value": 100},  # 1.00 LSL in cents
                {"Name": "MpesaReceiptNumber", "Value": "LHR987654321"},
                {"Name": "TransactionDate", "Value": "20260311152700"},
                {"Name": "PhoneNumber", "Value": "26656720256"}
            ]
        }
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/mpesa/callback", 
            json=success_callback)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success callback processed")
            print(f"📊 Status: {result.get('status')}")
            print(f"🆔 Payment ID: {result.get('payment_id')}")
        else:
            print(f"⚠️ Callback response: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Callback test error: {e}")
    
    # Step 3: Test failed payment callback
    print("\n❌ Step 3: Testing failed payment callback...")
    
    fail_callback = {
        "MerchantRequestID": "test_merchant_789012",
        "CheckoutRequestID": "test_checkout_789012",
        "ResultCode": 1,  # Failure code
        "ResultDesc": "Request cancelled by user",
        "CallbackMetadata": {
            "Item": [
                {"Name": "Amount", "Value": 100},
                {"Name": "PhoneNumber", "Value": "26656720256"}
            ]
        }
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/mpesa/callback", 
            json=fail_callback)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Failure callback processed")
            print(f"📊 Status: {result.get('status')}")
            print(f"🚫 Result Code: {result.get('result_code')}")
            print(f"📝 Description: {result.get('result_desc')}")
        else:
            print(f"⚠️ Callback response: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed callback test error: {e}")
    
    # Step 4: Instructions for real testing
    print("\n" + "=" * 40)
    print("📋 REAL TESTING INSTRUCTIONS:")
    print("=" * 40)
    print()
    print("🎯 TO TEST WITH YOUR REAL M-PESA:")
    print("1. Open the payment monitor:")
    print("   file:///home/duckey/lgcse-project/mpesa_monitor.html")
    print()
    print("2. Enter your details:")
    print("   📱 Phone: +26656720256")
    print("   💰 Amount: 1.00 LSL")
    print("   📝 Reference: REAL-TEST")
    print()
    print("3. Click 'Send STK Push'")
    print()
    print("4. On your phone:")
    print("   ✅ Enter CORRECT PIN → Money deducted")
    print("   ❌ Enter INCORRECT PIN → Payment fails")
    print()
    print("5. Watch the monitor for real-time updates!")
    print()
    print("🔍 What to expect:")
    print("• STK Push prompt on your M-Pesa")
    print("• PIN request dialog")
    print("• Success/failure notification")
    print("• Real-time status updates in monitor")
    print()
    print("⚠️  IMPORTANT:")
    print("• Use PRODUCTION environment for real money")
    print("• Use SANDBOX environment for testing")
    print("• Small amounts only (1.00 LSL)")
    print("• Check your M-Pesa balance")

if __name__ == "__main__":
    test_mpesa_direct()

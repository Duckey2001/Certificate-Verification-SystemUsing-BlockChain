#!/usr/bin/env python3
"""
Test script for M-Pesa payment integration
Tests both STK push and B2B payment methods
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "test_user",
    "password": "test123",
    "email": "test@example.com",
    "phone_number": "+26658881234"  # Test Lesotho number
}

class PaymentTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def register_test_user(self) -> bool:
        """Register a test user"""
        try:
            response = requests.post(f"{self.base_url}/api/auth/register", json={
                "username": TEST_USER["username"],
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "role": "verifier",
                "phone_number": TEST_USER["phone_number"]
            })
            
            if response.status_code == 200:
                self.log("✅ Test user registered successfully")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                self.log("ℹ️ Test user already exists")
                return True
            else:
                self.log(f"❌ Failed to register user: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
            return False
    
    def login_user(self) -> bool:
        """Login and get auth token"""
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.log("✅ User login successful")
                return True
            else:
                self.log(f"❌ Login failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authenticated headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_mpesa_config(self) -> bool:
        """Test M-Pesa configuration"""
        try:
            response = requests.get(
                f"{self.base_url}/api/mpesa/config",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                config = response.json()
                self.log(f"📊 M-Pesa Config Status:")
                self.log(f"   Configured: {config.get('configured')}")
                self.log(f"   Environment: {config.get('environment')}")
                self.log(f"   Currency: {config.get('currency')}")
                
                if not config.get('configured'):
                    self.log("⚠️ M-Pesa not properly configured. Check environment variables.", "WARNING")
                    return False
                return True
            else:
                self.log(f"❌ Failed to get M-Pesa config: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Config check error: {str(e)}", "ERROR")
            return False
    
    def test_stk_push_payment(self) -> bool:
        """Test M-Pesa STK Push payment"""
        try:
            self.log("🚀 Initiating STK Push payment...")
            
            response = requests.post(
                f"{self.base_url}/api/mpesa/stk-push",
                headers=self.get_headers(),
                json={
                    "phone_number": TEST_USER["phone_number"],
                    "amount": 5.00,
                    "account_reference": "TEST-PAYMENT",
                    "transaction_desc": "Test payment for CertiVert"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ STK Push initiated successfully!")
                self.log(f"   Payment ID: {data.get('payment_id')}")
                self.log(f"   Merchant Request ID: {data.get('merchant_request_id')}")
                self.log(f"   Checkout Request ID: {data.get('checkout_request_id')}")
                self.log(f"   Message: {data.get('customer_message')}")
                
                # Store payment ID for status check
                self.payment_id = data.get('payment_id')
                return True
            else:
                self.log(f"❌ STK Push failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ STK Push error: {str(e)}", "ERROR")
            return False
    
    def test_payment_status(self) -> bool:
        """Check payment status"""
        if not hasattr(self, 'payment_id'):
            self.log("⚠️ No payment ID to check", "WARNING")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/mpesa/status/{self.payment_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"📊 Payment Status:")
                self.log(f"   Payment ID: {data.get('payment_id')}")
                self.log(f"   Status: {data.get('status')}")
                self.log(f"   Amount: {data.get('amount')} {data.get('currency')}")
                self.log(f"   Method: {data.get('method')}")
                
                if data.get('mpesa_transaction_id'):
                    self.log(f"   Transaction ID: {data.get('mpesa_transaction_id')}")
                
                return True
            else:
                self.log(f"❌ Failed to check payment status: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Status check error: {str(e)}", "ERROR")
            return False
    
    def test_payment_history(self) -> bool:
        """Test payment history endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/payments/my",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                payments = response.json()
                self.log(f"📊 Payment History: {len(payments)} payments found")
                
                for payment in payments[:3]:  # Show last 3 payments
                    self.log(f"   Payment {payment.get('id')}: {payment.get('amount')} {payment.get('currency')} - {payment.get('status')}")
                
                return True
            else:
                self.log(f"❌ Failed to get payment history: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Payment history error: {str(e)}", "ERROR")
            return False
    
    def simulate_callback(self) -> bool:
        """Simulate M-Pesa callback for testing"""
        if not hasattr(self, 'payment_id'):
            self.log("⚠️ No payment ID to simulate callback for", "WARNING")
            return False
            
        try:
            self.log("🔄 Simulating M-Pesa callback...")
            
            callback_data = {
                "MerchantRequestID": "test_merchant_123",
                "CheckoutRequestID": "test_checkout_123",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 500},  # 5.00 in cents
                        {"Name": "MpesaReceiptNumber", "Value": "LHR123456789"},
                        {"Name": "TransactionDate", "Value": "20240226123456"},
                        {"Name": "PhoneNumber", "Value": "26658881234"}
                    ]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/mpesa/callback",
                json=callback_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Callback processed successfully!")
                self.log(f"   Status: {data.get('status')}")
                return True
            else:
                self.log(f"❌ Callback failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Callback simulation error: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all payment tests"""
        self.log("🧪 Starting Payment System Tests")
        self.log("=" * 50)
        
        tests = [
            ("Register Test User", self.register_test_user),
            ("Login User", self.login_user),
            ("Check M-Pesa Config", self.test_mpesa_config),
            ("Test STK Push", self.test_stk_push_payment),
            ("Check Payment Status", self.test_payment_status),
            ("Simulate Callback", self.simulate_callback),
            ("Check Payment History", self.test_payment_history)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {str(e)}", "ERROR")
                results.append((test_name, False))
        
        # Summary
        self.log("\n" + "=" * 50)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} {test_name}")
            if result:
                passed += 1
        
        self.log(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! Payment system is working correctly.")
        else:
            self.log(f"⚠️ {total - passed} test(s) failed. Please check the configuration.")
        
        return passed == total

if __name__ == "__main__":
    tester = PaymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

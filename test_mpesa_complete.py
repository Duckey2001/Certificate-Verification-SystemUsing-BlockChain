#!/usr/bin/env python3
"""
Comprehensive M-Pesa System Test Script
Tests all payment flows: USSD popup, SMS flow, and real M-Pesa integration
"""

import requests
import time
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5000"

class MpesaSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.phone_number = "26657620256"  # Test phone number
        
    def log_test(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if details:
            print(f"    Details: {json.dumps(details, indent=6)}")
    
    def test_health_check(self):
        """Test API health check"""
        try:
            response = self.session.get(f"{BASE_URL}/api/health")
            data = response.json()
            
            success = response.status_code == 200 and data.get('status') == 'healthy'
            self.log_test(
                "Health Check",
                success,
                "API is healthy" if success else "API health check failed",
                data if success else None
            )
            return success
            
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_mpesa_config(self):
        """Test M-Pesa configuration"""
        try:
            response = self.session.get(f"{BASE_URL}/api/mpesa/config")
            data = response.json()
            
            success = response.status_code == 200
            self.log_test(
                "M-Pesa Configuration",
                success,
                "Configuration retrieved" if success else "Config check failed",
                data
            )
            return success
            
        except Exception as e:
            self.log_test("M-Pesa Configuration", False, f"Exception: {str(e)}")
            return False
    
    def test_ussd_popup_flow(self):
        """Test complete USSD popup flow"""
        print(f"\n🧪 Testing USSD Popup Flow...")
        
        try:
            # Step 1: Initiate USSD session
            response = self.session.post(f"{BASE_URL}/api/ussd/initiate", json={
                "certificate_ref": "CERT-2024-TEST-001",
                "university_name": "National University of Lesotho",
                "amount": 5000  # M50.00
            })
            
            if response.status_code != 200:
                self.log_test("USSD Initiate", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            ussd_session_id = data.get('ussd_session_id')
            
            if not ussd_session_id:
                self.log_test("USSD Initiate", False, "No session ID returned")
                return False
            
            self.log_test("USSD Initiate", True, "Session created", {'ussd_session_id': ussd_session_id})
            
            # Step 2: Enter phone number
            response = self.session.post(f"{BASE_URL}/api/ussd/enter-phone", json={
                "ussd_session_id": ussd_session_id,
                "phone_number": self.phone_number
            })
            
            if response.status_code != 200:
                self.log_test("USSD Phone Entry", False, f"Status: {response.status_code}")
                return False
            
            self.log_test("USSD Phone Entry", True, "Phone number accepted")
            
            # Step 3: Send PIN
            response = self.session.post(f"{BASE_URL}/api/ussd/send-pin", json={
                "ussd_session_id": ussd_session_id
            })
            
            if response.status_code != 200:
                self.log_test("USSD Send PIN", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            pin_session_id = data.get('pin_session_id')
            
            self.log_test("USSD Send PIN", True, "PIN sent via SMS", {'pin_session_id': pin_session_id})
            
            # Step 4: Get PIN for testing (from transactions endpoint)
            response = self.session.get(f"{BASE_URL}/api/transactions")
            data = response.json()
            
            pin = None
            for pin_data in data.get('pending', []):
                if pin_data.get('ussd_session_id') == ussd_session_id:
                    pin = pin_data.get('pin')
                    break
            
            if not pin:
                self.log_test("USSD Get PIN", False, "Could not retrieve PIN for testing")
                return False
            
            self.log_test("USSD Get PIN", True, f"PIN retrieved: {pin}")
            
            # Step 5: Verify PIN
            response = self.session.post(f"{BASE_URL}/api/ussd/verify-pin", json={
                "ussd_session_id": ussd_session_id,
                "pin": pin
            })
            
            if response.status_code != 200:
                self.log_test("USSD Verify PIN", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            payment_id = data.get('payment_id')
            
            self.log_test("USSD Verify PIN", True, "PIN verified", {'payment_id': payment_id})
            
            # Step 6: Process payment
            response = self.session.post(f"{BASE_URL}/api/ussd/process-payment", json={
                "payment_id": payment_id
            })
            
            if response.status_code != 200:
                self.log_test("USSD Process Payment", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            transaction_id = data.get('transaction_id')
            
            self.log_test(
                "USSD Process Payment", 
                True, 
                "Payment completed",
                {
                    'transaction_id': transaction_id,
                    'amount': data.get('amount'),
                    'demo_mode': data.get('demo_mode', False)
                }
            )
            
            return True
            
        except Exception as e:
            self.log_test("USSD Popup Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_legacy_sms_flow(self):
        """Test legacy SMS flow for compatibility"""
        print(f"\n🧪 Testing Legacy SMS Flow...")
        
        try:
            # Step 1: Initiate payment
            response = self.session.post(f"{BASE_URL}/api/payment/initiate", json={
                "phone_number": self.phone_number,
                "certificate_ref": "CERT-2024-LEGACY-001",
                "university_name": "National University of Lesotho",
                "amount": 3000,  # M30.00
                "university_code": "UNI001"
            })
            
            if response.status_code != 200:
                self.log_test("Legacy Initiate", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            transaction_id = data.get('transaction_id')
            
            self.log_test("Legacy Initiate", True, "Payment initiated", {'transaction_id': transaction_id})
            
            # Step 2: Check status
            response = self.session.get(f"{BASE_URL}/api/payment/status/{transaction_id}")
            
            if response.status_code != 200:
                self.log_test("Legacy Status Check", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            status = data.get('status')
            
            self.log_test("Legacy Status Check", True, f"Status: {status}")
            
            # Step 3: Get PIN for testing
            response = self.session.get(f"{BASE_URL}/api/transactions")
            data = response.json()
            
            pin = None
            for pin_data in data.get('pending', []):
                if pin_data.get('pin_session_id') == transaction_id:
                    pin = pin_data.get('pin')
                    break
            
            if pin:
                self.log_test("Legacy Get PIN", True, f"PIN: {pin}")
                
                # Step 4: Simulate SMS reply
                response = self.session.post(f"{BASE_URL}/api/payment/simulate-sms", json={
                    "from_phone": self.phone_number,
                    "message": pin
                })
                
                if response.status_code == 200:
                    self.log_test("Legacy SMS Reply", True, "SMS reply simulated")
                else:
                    self.log_test("Legacy SMS Reply", False, f"Status: {response.status_code}")
            else:
                self.log_test("Legacy Get PIN", False, "Could not retrieve PIN")
            
            return True
            
        except Exception as e:
            self.log_test("Legacy SMS Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_real_mpesa_flow(self):
        """Test real M-Pesa B2B flow"""
        print(f"\n🧪 Testing Real M-Pesa B2B Flow...")
        
        try:
            # Test B2B payment
            response = self.session.post(f"{BASE_URL}/api/mpesa/b2b-payment", json={
                "university_code": "UNI001",
                "amount": "1000",  # M10.00 in cents
                "certificate_reference": "CERT-2024-REAL-001",
                "description": "Test certificate verification"
            })
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                transaction_id = data.get('transaction_id')
                
                self.log_test(
                    "Real M-Pesa B2B",
                    success,
                    "B2B payment processed" if success else "B2B payment failed",
                    {
                        'transaction_id': transaction_id,
                        'response_code': data.get('response_code'),
                        'response_message': data.get('response_message')
                    }
                )
                
                if success and transaction_id:
                    # Check payment status
                    response = self.session.get(f"{BASE_URL}/api/mpesa/status/{transaction_id}")
                    if response.status_code == 200:
                        status_data = response.json()
                        self.log_test("Real M-Pesa Status", True, "Status retrieved", status_data)
                
                return success
            else:
                self.log_test("Real M-Pesa B2B", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Real M-Pesa Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_stk_push_flow(self):
        """Test STK Push flow"""
        print(f"\n🧪 Testing STK Push Flow...")
        
        try:
            response = self.session.post(f"{BASE_URL}/api/mpesa/stk-push", json={
                "phone_number": self.phone_number,
                "amount": 25.00,  # M25.00
                "verification_request_id": "VERIFY-TEST-001",
                "account_reference": "LGCSE_VERIFY"
            })
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                payment_id = data.get('payment_id')
                
                self.log_test(
                    "STK Push",
                    success,
                    "STK push initiated" if success else "STK push failed",
                    {
                        'payment_id': payment_id,
                        'merchant_request_id': data.get('merchant_request_id'),
                        'checkout_request_id': data.get('checkout_request_id')
                    }
                )
                
                return success
            else:
                self.log_test("STK Push", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("STK Push Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_monitoring_endpoints(self):
        """Test monitoring and logging endpoints"""
        print(f"\n🧪 Testing Monitoring Endpoints...")
        
        try:
            # Test transactions endpoint
            response = self.session.get(f"{BASE_URL}/api/transactions")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Transactions Log",
                    True,
                    f"Retrieved {len(data.get('pending', []))} pending, {len(data.get('completed', []))} completed"
                )
            else:
                self.log_test("Transactions Log", False, f"HTTP {response.status_code}")
            
            # Test SMS logs
            response = self.session.get(f"{BASE_URL}/api/sms/sent")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "SMS Logs",
                    True,
                    f"Retrieved {data.get('total', 0)} SMS logs"
                )
            else:
                self.log_test("SMS Logs", False, f"HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Monitoring Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"\n{'='*80}")
        print(f"🧪 Comprehensive M-Pesa System Test")
        print(f"{'='*80}")
        print(f"🌐 Testing against: {BASE_URL}")
        print(f"📱 Test phone: {self.phone_number}")
        print(f"{'='*80}\n")
        
        # Run all test suites
        tests = [
            self.test_health_check,
            self.test_mpesa_config,
            self.test_ussd_popup_flow,
            self.test_legacy_sms_flow,
            self.test_real_mpesa_flow,
            self.test_stk_push_flow,
            self.test_monitoring_endpoints
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! M-Pesa system is fully functional.")
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
        
        # Print detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print(f"{'='*80}\n")
        
        return passed == total

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    except requests.exceptions.RequestException:
        print(f"❌ M-Pesa server not running at {BASE_URL}")
        print(f"Please start the server first: python mpesa-real-backend.py")
        sys.exit(1)
    
    # Run tests
    tester = MpesaSystemTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

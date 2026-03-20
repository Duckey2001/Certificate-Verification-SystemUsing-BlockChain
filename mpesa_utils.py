import base64
import time
import json
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import hashlib

class MpesaClient:
    def __init__(self, api_key, public_key, environment="sandbox"):
        self.api_key = api_key
        self.public_key = public_key
        self.environment = environment
        self.base_url = "https://openapi.m-pesa.com"
        self.market = "vodacomLES"  # Lesotho market
        self.shortcode = "110799"  # Your business shortcode
        
    def encrypt_api_key(self):
        """Encrypt API Key using RSA Public Key"""
        try:
            # Import RSA public key
            key = RSA.import_key(self.public_key)
            cipher = PKCS1_v1_5.new(key)
            
            # Encrypt API key
            encrypted = cipher.encrypt(self.api_key.encode('utf-8'))
            
            # Encode to base64
            encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
            return encrypted_b64
        except Exception as e:
            print(f"Encryption error: {e}")
            return None
    
    def generate_session(self):
        """Generate Session Key"""
        encrypted_key = self.encrypt_api_key()
        if not encrypted_key:
            return None
            
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {encrypted_key}',
            'Origin': '*'
        }
        
        # Build URL - SANDBOX MODE (NO REAL MONEY)
        url = f"{self.base_url}/sandbox/ipg/v2/{self.market}/getSession/"
        
        print(f"🔑 Calling SANDBOX Session API: {url}")
        print(f"🔴 WARNING: No real money, no USSD prompts, no SMS")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                session_id = response.json().get('output_SessionID')
                print(f"✅ Session generated: {session_id}")
                return session_id
            else:
                print(f"❌ Session generation failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Session request error: {e}")
            return None
    
    def direct_debit_payment(self, session_id, customer_msisdn, amount, 
                            third_party_ref, mandate_id, 
                            third_party_conversation_id=None):
        """Make Direct Debit Payment - REAL PRODUCTION"""
        
        # Generate conversation ID if not provided
        if not third_party_conversation_id:
            third_party_conversation_id = f"conv_{int(time.time())}"
        
        # Prepare headers with session ID
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {session_id}',
            'Origin': '*'
        }
        
        # Prepare request body
        payload = {
            "input_Amount": str(amount),
            "input_Country": "LES",
            "input_Currency": "LSL",
            "input_CustomerMSISDN": customer_msisdn,
            "input_ServiceProviderCode": self.shortcode,  # Your 110799
            "input_ThirdPartyConversationID": third_party_conversation_id,
            "input_ThirdPartyReference": third_party_ref,
            "input_MandateID": mandate_id
        }
        
        # Build URL - SANDBOX MODE (NO REAL MONEY)
        url = f"{self.base_url}/sandbox/ipg/v2/{self.market}/directDebitPayment/"
        
        print(f"💳 Calling SANDBOX Payment API: {url}")
        print(f"🔴 WARNING: No real money, no USSD prompts, no SMS")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            result = {
                'status_code': response.status_code,
                'success': response.status_code in [200, 201],
                'data': response.json() if response.text else {}
            }
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Data: {json.dumps(result['data'], indent=2)}")
            
            return result
        except Exception as e:
            print(f"❌ Payment error: {e}")
            return {
                'status_code': 500,
                'success': False,
                'error': str(e)
            }
    
    def query_transaction(self, session_id, query_reference):
        """Query Transaction Status"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {session_id}',
            'Origin': '*'
        }
        
        payload = {
            "input_QueryReference": query_reference,
            "input_ServiceProviderCode": self.shortcode
        }
        
        if self.environment == "sandbox":
            url = f"{self.base_url}/sandbox/ipg/v2/{self.market}/queryTransactionStatus/"
        else:
            url = f"{self.base_url}/openapi/ipg/v2/{self.market}/queryTransactionStatus/"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            return response.json() if response.status_code == 200 else None
        except:
            return None

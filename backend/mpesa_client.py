import base64
import uuid
import time
import json
import requests
from datetime import datetime, timedelta
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import os
from dotenv import load_dotenv

load_dotenv()

class MpesaB2BClient:
    def __init__(self):
        # Load credentials from environment
        self.api_key = os.getenv('MPESA_API_KEY')
        self.public_key = os.getenv('MPESA_PUBLIC_KEY')
        self.service_provider_code = os.getenv('SERVICE_PROVIDER_CODE')
        self.ecol_code = os.getenv('ECOL_CODE')
        self.country = os.getenv('COUNTRY')
        self.currency = os.getenv('CURRENCY')
        
        # API endpoints
        self.base_url = "https://openapi.m-pesa.com"
        self.session_url = f"{self.base_url}/openapi/session/generate"
        self.b2b_url = f"{self.base_url}/openapi/b2b/v1/ctrlsinglerequest"
        self.status_url = f"{self.base_url}/openapi/tx/v1/querytransactionstatus"
        
        # Session management
        self.session_key = None
        self.session_expiry = None
        self.session_lifetime = int(os.getenv('SESSION_LIFETIME', 3600))
        
        # Validate required credentials
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Ensure all required credentials are present"""
        required = {
            'MPESA_API_KEY': self.api_key,
            'MPESA_PUBLIC_KEY': self.public_key,
            'SERVICE_PROVIDER_CODE': self.service_provider_code,
            'ECOL_CODE': self.ecol_code
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required credentials: {missing}")
    
    def _encrypt_api_key(self):
        """Encrypt API key with public key"""
        try:
            key = RSA.importKey(self.public_key)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(self.api_key.encode())
            encrypted_base64 = base64.b64encode(encrypted).decode()
            return encrypted_base64
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")
    
    def generate_session(self):
        """Generate new session key"""
        encrypted_key = self._encrypt_api_key()
        
        payload = {
            "input_EncryptedKey": encrypted_key
        }
        
        try:
            response = requests.post(
                self.session_url, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_key = result.get('output_SessionID')
                self.session_expiry = datetime.now() + timedelta(seconds=self.session_lifetime)
                return self.session_key
            else:
                error_msg = f"Session generation failed: {response.status_code} - {response.text}"
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
    
    def get_session(self):
        """Get valid session (generate if expired)"""
        if not self.session_key or datetime.now() >= self.session_expiry:
            return self.generate_session()
        return self.session_key
    
    def b2b_payment(self, university_code, amount, certificate_reference, description=None):
        """
        Process B2B payment from University to ECOL
        
        Args:
            university_code (str): University's business code
            amount (str/int): Amount in cents (e.g., 5000 = 50.00)
            certificate_reference (str): Certificate ID being verified
            description (str, optional): Payment description
        
        Returns:
            dict: M-Pesa API response
        """
        # Get valid session
        session_key = self.get_session()
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {session_key}"
        }
        
        # Generate unique IDs
        conversation_id = str(uuid.uuid4()).replace('-', '')[:20]
        transaction_ref = f"VERIFY-{certificate_reference}"
        
        # Prepare payload
        payload = {
            "input_Amount": str(amount),
            "input_Country": self.country,
            "input_Currency": self.currency,
            "input_PrimaryPartyCode": university_code,  # University (payer)
            "input_SecondaryPartyCode": self.ecol_code,  # ECOL (payee)
            "input_ThirdPartyConversationID": conversation_id,
            "input_TransactionReference": transaction_ref,
            "input_ServiceProviderCode": self.service_provider_code
        }
        
        # Add description if provided
        if description:
            payload["input_PurchasedItemsDesc"] = description[:50]
        else:
            payload["input_PurchasedItemsDesc"] = f"Cert Verify: {certificate_reference}"
        
        try:
            response = requests.post(
                self.b2b_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            result = response.json()
            
            # Add metadata to response
            result['_metadata'] = {
                'conversation_id': conversation_id,
                'transaction_reference': transaction_ref,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": str(e),
                "output_ResponseCode": "FAILED",
                "output_ResponseDesc": f"Network error: {e}"
            }
    
    def query_transaction(self, transaction_reference):
        """
        Query transaction status
        
        Args:
            transaction_reference (str): Transaction reference to query
        
        Returns:
            dict: Transaction status
        """
        session_key = self.get_session()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {session_key}"
        }
        
        payload = {
            "input_ThirdPartyReference": transaction_reference,
            "input_QueryReference": transaction_reference,
            "input_ServiceProviderCode": self.service_provider_code
        }
        
        try:
            response = requests.post(
                self.status_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": str(e),
                "output_ResponseCode": "FAILED",
                "output_ResponseDesc": f"Query failed: {e}"
            }
    
    def is_payment_successful(self, response):
        """Check if payment was successful"""
        return response.get('output_ResponseCode') == 'INS-0'
    
    def get_response_message(self, response):
        """Get human-readable response message"""
        return response.get('output_ResponseDesc', 'Unknown response')

"""
M-Pesa B2B Integration Client for Lesotho
Supports real payments with proper error handling and logging
"""

import requests
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MpesaB2BClient:
    """
    Production-ready M-Pesa B2B Client for Lesotho
    Handles real payments with proper security and error handling
    """
    
    def __init__(self):
        # Load configuration from environment
        self.api_key = os.getenv('MPESA_API_KEY')
        self.public_key = os.getenv('MPESA_PUBLIC_KEY')
        self.service_provider_code = os.getenv('SERVICE_PROVIDER_CODE', '110799')
        self.ecol_code = os.getenv('ECOL_CODE', '110799')
        self.country = os.getenv('COUNTRY', 'LES')
        self.currency = os.getenv('CURRENCY', 'LSL')
        
        # API endpoints (production)
        self.api_url = "https://openapi.m-pesa.com"
        self.session_url = f"{self.api_url}/openapi/session/generate"
        self.b2c_url = f"{self.api_url}/openapi/ipg/v2/vodacomLES/ussd/payments/"
        self.b2b_url = f"{self.api_url}/openapi/ipg/v2/vodacomLES/b2bPayments/"
        self.query_url = f"{self.api_url}/openapi/ipg/v2/vodacomLES/queryTransaction/"
        
        # Session management
        self.session_key = None
        self.session_expiry = None
        self.session_lifetime = 3600  # 1 hour in seconds
        
        logger.info(f"M-Pesa Client initialized for {self.country} - {self.currency}")

    def _encrypt_password(self) -> str:
        """
        Encrypt password using RSA public key
        Format: API Key + "@" + timestamp (yyyyMMddHHmmss)
        """
        try:
            # Get current timestamp in required format
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            password = f"{self.api_key}@{timestamp}"
            
            # Load public key
            public_key = RSA.import_key(self.public_key)
            cipher = PKCS1_v1_5.new(public_key)
            
            # Encrypt and encode
            encrypted = cipher.encrypt(password.encode())
            encoded = base64.b64encode(encrypted).decode('utf-8')
            
            logger.debug(f"Password encrypted successfully at {timestamp}")
            return encoded
            
        except Exception as e:
            logger.error(f"Password encryption failed: {str(e)}")
            raise

    def generate_session(self) -> Optional[str]:
        """
        Generate new session key with proper error handling
        """
        try:
            # Check if current session is still valid
            if self.session_key and self.session_expiry:
                if datetime.utcnow() < self.session_expiry:
                    logger.info("Using existing valid session")
                    return self.session_key
            
            # Encrypt password
            encrypted_password = self._encrypt_password()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {encrypted_password}'
            }
            
            # Make request
            logger.info("Generating new M-Pesa session...")
            response = requests.post(
                self.session_url,
                headers=headers,
                timeout=30
            )
            
            # Parse response
            if response.status_code == 200:
                data = response.json()
                self.session_key = data.get('output_SessionID')
                
                # Set session expiry
                self.session_expiry = datetime.utcnow() + timedelta(seconds=self.session_lifetime)
                
                logger.info(f"Session generated successfully: {self.session_key[:10]}...")
                return self.session_key
            else:
                logger.error(f"Session generation failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Session generation network error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Session generation failed: {str(e)}")
            raise

    def b2b_payment(
        self,
        university_code: str,
        amount: str,
        certificate_reference: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process REAL B2B payment from University to ECOL
        
        Args:
            university_code: University identifier
            amount: Amount in cents (e.g., "1000" for M10.00)
            certificate_reference: Certificate reference number
            description: Optional payment description
        
        Returns:
            Dict containing payment response
        """
        try:
            # Validate amount (minimum M5.00 = 500 cents)
            if int(amount) < 500:
                logger.warning(f"Amount {amount} cents is below minimum M5.00")
                return {
                    'output_ResponseCode': 'INS-26',
                    'output_ResponseDesc': 'Amount below minimum (M5.00)',
                    'output_TransactionID': None,
                    'output_ConversationID': None,
                    '_metadata': {
                        'error': 'Amount below minimum',
                        'minimum_amount': '500',
                        'provided_amount': amount
                    }
                }
            
            # Get valid session
            session = self.generate_session()
            if not session:
                logger.error("No valid session available")
                return {
                    'output_ResponseCode': 'INS-14',
                    'output_ResponseDesc': 'Invalid session',
                    'output_TransactionID': None,
                    'output_ConversationID': None
                }
            
            # Prepare payment data
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            transaction_id = f"VERIFY{certificate_reference[-8:]}{timestamp[-6:]}"
            
            payload = {
                "input_ServiceProviderCode": self.service_provider_code,
                "input_Country": self.country,
                "input_Currency": self.currency,
                "input_Amount": amount,
                "input_TransactionReference": transaction_id,
                "input_BillReferenceNumber": certificate_reference,
                "input_Description": description or f"Certificate verification fee for {certificate_reference}",
                "input_BuyerPhoneNumber": "",
                "input_BuyerEmail": "",
                "input_BuyerNames": university_code,
                "input_ThirdPartyConversationID": f"CONV{timestamp}",
                "input_ServiceProviderPaymentCode": self.ecol_code
            }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {session}',
                'Origin': '*'
            }
            
            # Make payment request
            logger.info(f"Processing B2B payment for certificate {certificate_reference}")
            logger.debug(f"Payment payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.b2b_url,
                json=payload,
                headers=headers,
                timeout=45
            )
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                
                # Add metadata
                result['_metadata'] = {
                    'timestamp': timestamp,
                    'amount_maloti': float(amount) / 100,
                    'currency': self.currency,
                    'certificate': certificate_reference,
                    'university': university_code
                }
                
                logger.info(f"Payment processed: {result.get('output_ResponseCode')} - {result.get('output_ResponseDesc')}")
                return result
            else:
                logger.error(f"Payment failed: {response.status_code} - {response.text}")
                return {
                    'output_ResponseCode': 'INS-9',
                    'output_ResponseDesc': f'HTTP {response.status_code}: {response.text[:100]}',
                    'output_TransactionID': None,
                    'output_ConversationID': None,
                    '_metadata': {'http_status': response.status_code}
                }
                
        except requests.exceptions.Timeout:
            logger.error("Payment request timed out")
            return {
                'output_ResponseCode': 'INS-998',
                'output_ResponseDesc': 'Request timeout',
                'output_TransactionID': None,
                'output_ConversationID': None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment network error: {str(e)}")
            return {
                'output_ResponseCode': 'INS-999',
                'output_ResponseDesc': f'Network error: {str(e)[:50]}',
                'output_TransactionID': None,
                'output_ConversationID': None
            }
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            return {
                'output_ResponseCode': 'INS-500',
                'output_ResponseDesc': f'Internal error: {str(e)[:50]}',
                'output_TransactionID': None,
                'output_ConversationID': None
            }

    def query_transaction(self, transaction_reference: str) -> Dict[str, Any]:
        """
        Query transaction status
        
        Args:
            transaction_reference: Transaction reference to query
        
        Returns:
            Dict containing transaction status
        """
        try:
            # Get valid session
            session = self.generate_session()
            if not session:
                return {
                    'output_ResponseCode': 'INS-14',
                    'output_ResponseDesc': 'Invalid session'
                }
            
            # Prepare query payload
            payload = {
                "input_QueryReference": transaction_reference,
                "input_ServiceProviderCode": self.service_provider_code,
                "input_Country": self.country,
                "input_ThirdPartyConversationID": f"QRY{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Make query request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {session}'
            }
            
            logger.info(f"Querying transaction: {transaction_reference}")
            response = requests.post(
                self.query_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'output_ResponseCode': 'INS-9',
                    'output_ResponseDesc': f'Query failed: HTTP {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Transaction query error: {str(e)}")
            return {
                'output_ResponseCode': 'INS-500',
                'output_ResponseDesc': f'Query error: {str(e)[:50]}'
            }

    def is_payment_successful(self, response: Dict[str, Any]) -> bool:
        """
        Check if payment was successful
        
        Args:
            response: M-Pesa API response
        
        Returns:
            True if payment successful, False otherwise
        """
        if not response:
            return False
        
        response_code = response.get('output_ResponseCode')
        
        # Successful codes
        success_codes = ['INS-0', '0', '200', 'INS-00']
        
        # Check if successful
        if response_code in success_codes:
            return True
        
        # Check if transaction ID exists (sometimes success without explicit code)
        if response.get('output_TransactionID') and response_code not in ['INS-14', 'INS-9']:
            return True
        
        return False

    def get_response_message(self, response: Dict[str, Any]) -> str:
        """
        Get user-friendly response message
        
        Args:
            response: M-Pesa API response
        
        Returns:
            User-friendly message
        """
        if not response:
            return "No response from M-Pesa"
        
        response_code = response.get('output_ResponseCode', 'UNKNOWN')
        response_desc = response.get('output_ResponseDesc', '')
        
        # Map response codes to user-friendly messages
        messages = {
            'INS-0': 'Payment successful',
            'INS-9': 'Payment failed',
            'INS-14': 'Invalid session - please try again',
            'INS-20': 'Insufficient balance',
            'INS-26': 'Amount below minimum (M5.00)',
            'INS-998': 'Request timeout - please check status',
            'INS-999': 'Network error - please try again',
            'INS-500': 'Internal server error'
        }
        
        # Return mapped message or original description
        return messages.get(response_code, response_desc or f'Unknown response: {response_code}')

# Singleton instance for reuse
mpesa_client = MpesaB2BClient()

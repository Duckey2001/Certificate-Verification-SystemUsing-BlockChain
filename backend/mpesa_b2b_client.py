"""
M-Pesa B2B Integration for CertiVert LGCSE (Lesotho)
Handles university-to-ECOL payments for certificate verification
"""

import os
import requests
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MpesaB2BClient:
    """
    M-Pesa B2B Client for Lesotho (Vodacom Lesotho)
    Handles university-to-ECOL payments for certificate verification
    """
    
    def __init__(self):
        # Load configuration from environment
        self.api_key = os.getenv('MPESA_API_KEY')
        self.public_key = os.getenv('MPESA_PUBLIC_KEY')
        self.service_provider_code = os.getenv('SERVICE_PROVIDER_CODE', '110799')
        self.ecol_code = os.getenv('ECOL_CODE', '110799')  # ECOL's receiving code
        self.country = os.getenv('COUNTRY', 'LES')
        self.currency = os.getenv('CURRENCY', 'LSL')  # Lesotho Loti
        
        # Validate and format merchant codes to 8 digits
        self.service_provider_code = self._format_merchant_code(self.service_provider_code)
        self.ecol_code = self._format_merchant_code(self.ecol_code)
        
        # API endpoints (production)
        self.api_url = "https://openapi.m-pesa.com"
        self.session_url = f"{self.api_url}/openapi/session/generate"
        self.b2b_url = f"{self.api_url}/openapi/ipg/v2/vodacomLES/b2bPayments/"
        self.query_url = f"{self.api_url}/openapi/ipg/v2/vodacomLES/queryTransaction/"
        
        # Session management
        self.session_key = None
        self.session_expiry = None
        self.session_lifetime = 3600  # 1 hour
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"M-Pesa B2B Client initialized for {self.country} - {self.currency}")
        logger.info(f"Service Provider Code: {self.service_provider_code}")
        logger.info(f"ECOL Code: {self.ecol_code}")
    
    def _validate_config(self):
        """Validate required configuration"""
        missing = []
        if not self.api_key:
            missing.append('MPESA_API_KEY')
        if not self.public_key:
            missing.append('MPESA_PUBLIC_KEY')
        if not self.service_provider_code:
            missing.append('SERVICE_PROVIDER_CODE')
        if not self.ecol_code:
            missing.append('ECOL_CODE')
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Validate merchant codes are 8 digits
        if not self._is_valid_merchant_code(self.service_provider_code):
            raise ValueError(f"Invalid service provider code: {self.service_provider_code}. Must be 8 digits")
        if not self._is_valid_merchant_code(self.ecol_code):
            raise ValueError(f"Invalid ECOL code: {self.ecol_code}. Must be 8 digits")
    
    def _format_merchant_code(self, code: str) -> str:
        """Format merchant code to 8 digits"""
        if not code:
            return code
        
        # Remove any non-digit characters
        clean_code = ''.join(filter(str.isdigit, code))
        
        # If already 8 digits, return as is
        if len(clean_code) == 8:
            return clean_code
        
        # If less than 8 digits, pad with leading zeros
        if len(clean_code) < 8:
            return clean_code.zfill(8)
        
        # If more than 8 digits, take last 8 digits
        return clean_code[-8:]
    
    def _is_valid_merchant_code(self, code: str) -> bool:
        """Check if merchant code is valid 8 digits"""
        return code and len(code) == 8 and code.isdigit()
    
    def _encrypt_password(self) -> Tuple[str, str]:
        """
        Encrypt password using RSA public key
        Returns: (encrypted_password, timestamp)
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
            return encoded, timestamp
            
        except Exception as e:
            logger.error(f"Password encryption failed: {str(e)}")
            raise
    
    def generate_session(self) -> Optional[str]:
        """
        Generate new session key
        Returns: Session ID or None if failed
        """
        try:
            # Check if current session is still valid
            if self.session_key and self.session_expiry:
                if datetime.utcnow() < self.session_expiry:
                    logger.info("Using existing valid session")
                    return self.session_key
            
            # Encrypt password
            encrypted_password, timestamp = self._encrypt_password()
            
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
        amount: str,  # Amount in cents (e.g., "1000" for M10.00)
        certificate_reference: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process B2B payment from University to ECOL
        
        Args:
            university_code: University identifier (e.g., "NUL001", "LEC001")
            amount: Amount in cents (minimum 500 = M5.00)
            certificate_reference: Certificate reference number
            description: Optional payment description
        
        Returns:
            Dict containing payment response
        """
        try:
            # Validate amount
            amount_int = int(amount)
            if amount_int < 500:
                logger.warning(f"Amount {amount} cents is below minimum M5.00")
                return {
                    'output_ResponseCode': 'INS-26',
                    'output_ResponseDesc': 'Amount below minimum (M5.00)',
                    'output_TransactionID': None,
                    'output_ConversationID': None,
                    '_metadata': {
                        'error': 'Amount below minimum',
                        'minimum_amount': '500',
                        'provided_amount': amount,
                        'amount_maloti': amount_int / 100
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
            
            # Generate transaction reference
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            # Use last 8 chars of certificate reference + timestamp
            cert_short = certificate_reference[-8:] if len(certificate_reference) >= 8 else certificate_reference
            transaction_id = f"VER{cert_short}{timestamp[-6:]}"
            
            # Prepare payment payload
            payload = {
                "input_ServiceProviderCode": self.service_provider_code,
                "input_Country": self.country,
                "input_Currency": self.currency,
                "input_Amount": amount,
                "input_TransactionReference": transaction_id,
                "input_BillReferenceNumber": certificate_reference,
                "input_Description": description or f"Certificate verification - {certificate_reference}",
                "input_BuyerPhoneNumber": "",
                "input_BuyerEmail": "",
                "input_BuyerNames": university_code,
                "input_ThirdPartyConversationID": f"CONV{timestamp}",
                "input_ServiceProviderPaymentCode": self.ecol_code  # ECOL's receiving code
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
                    'amount_maloti': amount_int / 100,
                    'currency': self.currency,
                    'certificate': certificate_reference,
                    'university': university_code,
                    'transaction_ref': transaction_id
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
        
        return messages.get(response_code, response_desc or f'Unknown response: {response_code}')

# Singleton instance
mpesa_b2b_client = MpesaB2BClient()

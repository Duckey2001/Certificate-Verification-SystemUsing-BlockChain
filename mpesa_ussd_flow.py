import uuid
import random
import requests
import base64
import json
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# ============================================
# In-Memory Storage (Replace with Database)
# ============================================
ussd_sessions = {}          # USSD session storage
pin_sessions = {}           # PIN verification sessions
transactions = []           # Transaction records
pending_payments = {}       # Pending payments waiting for PIN

# ============================================
# M-Pesa API Client
# ============================================
class MpesaB2BClient:
    def __init__(self):
        self.api_key = os.getenv('MPESA_API_KEY', '6bc4157dbowkdd409118e0978dc6991a')
        self.public_key = os.getenv('MPESA_PUBLIC_KEY', """MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAietPTdEyyoV/wvxRjS5pSn3ZBQH9hnVtQC9SFLgM9IkomEX9Vu9fBg2MzWSSqkQlaYIGFGH3d69Q5NOWkRo+Y8p5a61sc9hZ+ItAiEL9KIbZzhnMwi12jUYCTff0bVTsTGSNUePQ2V42sToOIKCeBpUtwWKhhW3CSpK7S1iJhS9H22/BT/pk21Jd8btwMLUHfVD95iXbHNM8u6vFaYuHczx966T7gpa9RGGXRtiOr3ScJq1515tzOSOsHTPHLTun59nxxJiEjKoI4Lb9h6IlauvcGAQHp5q6/2XmxuqZdGzh39uLac8tMSmY3vC3fiHYC3iMyTb7eXqATIhDUOf9mOSbgZMS19iiVZvz8igDl950IMcelJwcj0qCLoufLE5y8ud5WIw47OCVkD7tcAEPmVWlCQ744SIM5afw+Jg50T1SEtu3q3GiL0UQ6KTLDyDEt5BL9HWXAIXsjFdPDpX1jtxZavVQV+Jd7FXhuPQuDbh12liTROREdzatYWRnrhzeOJ5Se9xeXLvYSj8DmAI4iFf2cVtWCzj/02uK4+iIGXlX7lHP1W+tycLS7Pe2RdtC2+oz5RSSqb5jI4+3iEY/vZjSMBVk69pCDzZy4ZE8LBgyEvSabJ/cddwWmShcRS+21XvGQ1uXYLv0FCTEHHobCfmn2y8bJBb/Hct53BaojWUCAwEAAQ==""")
        self.service_provider_code = os.getenv('SERVICE_PROVIDER_CODE', '110799')
        self.ecol_code = os.getenv('ECOL_CODE', '110799')
        self.country = os.getenv('COUNTRY', 'LES')
        self.currency = os.getenv('CURRENCY', 'LSL')
        self.base_url = os.getenv('BASE_URL', 'https://openapi.m-pesa.com')
        
        self.session_key = None
        self.session_expiry = None
    
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
        
        payload = {"input_EncryptedKey": encrypted_key}
        
        try:
            response = requests.post(
                f"{self.base_url}/openapi/session/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_key = result.get('output_SessionID')
                self.session_expiry = datetime.now() + timedelta(hours=1)
                return self.session_key
            else:
                raise Exception(f"Session failed: {response.text}")
        except Exception as e:
            raise Exception(f"Session error: {e}")
    
    def get_session(self):
        """Get valid session"""
        if not self.session_key or datetime.now() >= self.session_expiry:
            return self.generate_session()
        return self.session_key
    
    def process_b2b_payment(self, university_code, amount, certificate_ref, description=None):
        """Process B2B payment"""
        session_key = self.get_session()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {session_key}"
        }
        
        conversation_id = str(uuid.uuid4()).replace('-', '')[:20]
        transaction_ref = f"VERIFY-{certificate_ref}"
        
        payload = {
            "input_Amount": str(amount),
            "input_Country": self.country,
            "input_Currency": self.currency,
            "input_PrimaryPartyCode": university_code,
            "input_SecondaryPartyCode": self.ecol_code,
            "input_ThirdPartyConversationID": conversation_id,
            "input_TransactionReference": transaction_ref,
            "input_ServiceProviderCode": self.service_provider_code
        }
        
        if description:
            payload["input_PurchasedItemsDesc"] = description[:50]
        else:
            payload["input_PurchasedItemsDesc"] = f"Cert Verify: {certificate_ref}"
        
        try:
            response = requests.post(
                f"{self.base_url}/openapi/b2b/v1/ctrlsinglerequest",
                json=payload,
                headers=headers,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": True, "message": str(e)}

mpesa_client = MpesaB2BClient()

# ============================================
# SMS Simulation (Replace with actual SMS API)
# ============================================
class SMSService:
    def __init__(self):
        self.sent_messages = []
    
    def send_sms(self, phone_number, message):
        """Send SMS to phone number"""
        # Simulate SMS sending
        sms_record = {
            "id": str(uuid.uuid4()),
            "phone": phone_number,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "sent"
        }
        self.sent_messages.append(sms_record)
        
        print(f"\n{'='*60}")
        print(f"📱 SMS SENT TO: {phone_number}")
        print(f"📝 MESSAGE:")
        print(f"{message}")
        print(f"{'='*60}\n")
        
        return True
    
    def send_pin_sms(self, phone_number, pin, transaction_details):
        """Send PIN verification SMS"""
        message = f"""🏫 ECOL Certificate Verification

Amount: {transaction_details['amount']} LSL
Certificate: {transaction_details['certificate_ref']}
University: {transaction_details['university_name']}

🔐 Your PIN: {pin}

Enter this PIN to confirm your payment.
This PIN expires in 5 minutes.

Reply to this SMS with the PIN to confirm.
If you didn't request this, ignore."""
        
        return self.send_sms(phone_number, message)
    
    def send_confirmation_sms(self, phone_number, transaction_details):
        """Send payment confirmation SMS"""
        message = f"""✅ PAYMENT CONFIRMED

Amount: {transaction_details['amount']} LSL
To: ECOL
Certificate: {transaction_details['certificate_ref']}
Transaction ID: {transaction_details['transaction_id']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Thank you for using ECOL Verification Service."""
        
        return self.send_sms(phone_number, message)
    
    def send_failure_sms(self, phone_number, reason):
        """Send payment failure SMS"""
        message = f"""❌ PAYMENT FAILED

Reason: {reason}

Please try again or contact support.

ECOL Verification Service"""
        
        return self.send_sms(phone_number, message)

sms_service = SMSService()

# ============================================
# USSD Flow Handlers
# ============================================
class USSDHandler:
    def __init__(self):
        self.steps = {
            'init': {
                'message': "Welcome to ECOL Certificate Verification\n\nEnter your M-Pesa number:",
                'next_step': 'get_phone'
            },
            'get_phone': {
                'validate': 'validate_phone',
                'next_step': 'send_pin'
            },
            'send_pin': {
                'message': "PIN has been sent to your phone.\nEnter PIN to confirm:",
                'next_step': 'verify_pin'
            },
            'verify_pin': {
                'validate': 'validate_pin',
                'next_step': 'process_payment'
            },
            'process_payment': {
                'message': "Processing payment...",
                'next_step': 'complete'
            },
            'complete': {
                'message': "✅ Payment successful!\nCertificate will be verified.",
                'next_step': None
            },
            'failed': {
                'message': "❌ Payment failed. Please try again.",
                'next_step': None
            }
        }
    
    def get_initial_message(self):
        return self.steps['init']['message']
    
    def validate_phone(self, phone_number):
        """Validate M-Pesa phone number"""
        # Remove any spaces or special characters
        phone_number = phone_number.strip()
        
        # Accept both formats: 266XXXXXXX or +266XXXXXXX
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Check if it's a valid Lesotho number
        if phone_number.startswith('266') and len(phone_number) == 11:
            return True, phone_number
        elif len(phone_number) == 9 and phone_number.isdigit():
            # If user entered just the local number (e.g., 57620256)
            phone_number = '266' + phone_number
            return True, phone_number
        else:
            return False, f"Invalid number: {phone_number} (len: {len(phone_number)}). Use format: 266XXXXXXX"
    
    def validate_pin(self, entered_pin, session_id):
        """Validate entered PIN"""
        if session_id in pin_sessions:
            stored_pin = pin_sessions[session_id]['pin']
            expiry = pin_sessions[session_id]['expiry']
            
            if datetime.now() > expiry:
                return False, "PIN expired. Please restart."
            
            if entered_pin == stored_pin:
                return True, "PIN verified"
            else:
                return False, "Invalid PIN"
        return False, "No PIN session found"

ussd_handler = USSDHandler()

# ============================================
# API Endpoints
# ============================================
@app.route('/api/ussd/initiate', methods=['POST'])
def initiate_ussd():
    """Step 1: Initiate USSD push"""
    data = request.json
    certificate_ref = data.get('certificate_ref')
    university_name = data.get('university_name', 'University')
    amount = data.get('amount', 5000)  # Default 50.00 LSL
    
    # Generate unique USSD session ID
    ussd_session_id = str(uuid.uuid4())
    
    # Store session data
    ussd_sessions[ussd_session_id] = {
        'step': 'init',
        'certificate_ref': certificate_ref,
        'university_name': university_name,
        'amount': amount,
        'created_at': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    print(f"\n{'='*60}")
    print(f"📱 USSD Push Initiated")
    print(f"🔗 Session ID: {ussd_session_id}")
    print(f"🎓 University: {university_name}")
    print(f"📄 Certificate: {certificate_ref}")
    print(f"💰 Amount: {amount/100:.2f} LSL")
    print(f"{'='*60}")
    
    # Simulate USSD push to phone
    message = ussd_handler.get_initial_message()
    
    return jsonify({
        "status": "success",
        "ussd_session_id": ussd_session_id,
        "message": message,
        "next_action": "enter_phone"
    })

@app.route('/api/ussd/enter-phone', methods=['POST'])
def enter_phone():
    """Step 2: User enters phone number"""
    data = request.json
    ussd_session_id = data.get('ussd_session_id')
    phone_input = data.get('phone_number')
    
    if ussd_session_id not in ussd_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    # Validate phone number
    is_valid, phone_result = ussd_handler.validate_phone(phone_input)
    
    if not is_valid:
        return jsonify({
            "status": "failed",
            "error": phone_result,
            "message": "Invalid phone number. Please try again."
        }), 400
    
    # Store phone number in session
    ussd_sessions[ussd_session_id]['phone_number'] = phone_result
    ussd_sessions[ussd_session_id]['step'] = 'get_phone'
    
    print(f"\n📱 User entered phone: {phone_result}")
    print(f"🔗 Session ID: {ussd_session_id}")
    
    # Move to next step - send PIN
    return jsonify({
        "status": "success",
        "ussd_session_id": ussd_session_id,
        "phone_number": phone_result,
        "next_action": "send_pin",
        "message": "PIN will be sent to your phone"
    })

@app.route('/api/ussd/send-pin', methods=['POST'])
def send_pin():
    """Step 3: Send SMS with PIN to user"""
    data = request.json
    ussd_session_id = data.get('ussd_session_id')
    
    if ussd_session_id not in ussd_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session_data = ussd_sessions[ussd_session_id]
    phone_number = session_data.get('phone_number')
    
    if not phone_number:
        return jsonify({"error": "Phone number not found"}), 400
    
    # Generate random PIN
    pin = str(random.randint(1000, 9999))
    
    # Create PIN session
    pin_session_id = str(uuid.uuid4())
    pin_sessions[pin_session_id] = {
        'ussd_session_id': ussd_session_id,
        'pin': pin,
        'phone': phone_number,
        'amount': session_data['amount'],
        'certificate_ref': session_data['certificate_ref'],
        'university_name': session_data['university_name'],
        'expiry': datetime.now() + timedelta(minutes=5),
        'created_at': datetime.now().isoformat()
    }
    
    # Store PIN session ID in USSD session
    session_data['pin_session_id'] = pin_session_id
    session_data['step'] = 'send_pin'
    
    # Prepare transaction details for SMS
    transaction_details = {
        'amount': session_data['amount'] / 100,
        'certificate_ref': session_data['certificate_ref'],
        'university_name': session_data['university_name']
    }
    
    # Send SMS with PIN
    sms_service.send_pin_sms(phone_number, pin, transaction_details)
    
    print(f"\n🔢 PIN Generated: {pin}")
    print(f"🆔 PIN Session ID: {pin_session_id}")
    print(f"⏰ PIN Expires: {(datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')}")
    
    return jsonify({
        "status": "success",
        "ussd_session_id": ussd_session_id,
        "pin_session_id": pin_session_id,
        "message": "PIN sent via SMS",
        "next_action": "verify_pin"
    })

@app.route('/api/ussd/verify-pin', methods=['POST'])
def verify_pin():
    """Step 4: User enters PIN to confirm"""
    data = request.json
    ussd_session_id = data.get('ussd_session_id')
    entered_pin = data.get('pin')
    
    if ussd_session_id not in ussd_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session_data = ussd_sessions[ussd_session_id]
    pin_session_id = session_data.get('pin_session_id')
    
    if not pin_session_id or pin_session_id not in pin_sessions:
        return jsonify({"error": "No PIN session found"}), 400
    
    # Validate PIN
    is_valid, message = ussd_handler.validate_pin(entered_pin, pin_session_id)
    
    if not is_valid:
        return jsonify({
            "status": "failed",
            "error": message,
            "message": "Invalid or expired PIN"
        }), 400
    
    # PIN verified - proceed to payment
    session_data['step'] = 'verify_pin'
    session_data['pin_verified'] = True
    
    print(f"\n✅ PIN Verified for {session_data['phone_number']}")
    
    # Store pending payment for processing
    payment_id = str(uuid.uuid4())
    pending_payments[payment_id] = {
        'ussd_session_id': ussd_session_id,
        'phone': session_data['phone_number'],
        'amount': session_data['amount'],
        'certificate_ref': session_data['certificate_ref'],
        'university_name': session_data['university_name']
    }
    
    return jsonify({
        "status": "success",
        "ussd_session_id": ussd_session_id,
        "payment_id": payment_id,
        "message": "PIN verified. Processing payment...",
        "next_action": "process_payment"
    })

@app.route('/api/ussd/process-payment', methods=['POST'])
def process_payment():
    """Step 5: Process B2B payment"""
    data = request.json
    payment_id = data.get('payment_id')
    
    if payment_id not in pending_payments:
        return jsonify({"error": "Invalid payment"}), 400
    
    payment = pending_payments[payment_id]
    ussd_session_id = payment['ussd_session_id']
    session_data = ussd_sessions[ussd_session_id]
    
    print(f"\n💳 Processing B2B Payment...")
    print(f"   Payer: University ({payment['university_name']})")
    print(f"   Payee: ECOL ({mpesa_client.ecol_code})")
    print(f"   Amount: {payment['amount']/100:.2f} LSL")
    print(f"   Reference: {payment['certificate_ref']}")
    
    try:
        # Process actual B2B payment
        response = mpesa_client.process_b2b_payment(
            university_code="UNI001",  # In production, get from database
            amount=payment['amount'],
            certificate_ref=payment['certificate_ref'],
            description=f"Certificate verification - {payment['certificate_ref']}"
        )
        
        # Check if payment was successful
        if response.get('output_ResponseCode') == 'INS-0':
            # Payment successful
            transaction_id = response.get('output_TransactionID')
            conversation_id = response.get('output_ConversationID')
            
            # Store transaction record
            transaction_record = {
                "id": transaction_id,
                "conversation_id": conversation_id,
                "ussd_session_id": ussd_session_id,
                "phone": payment['phone'],
                "amount": payment['amount'],
                "certificate_ref": payment['certificate_ref'],
                "university_name": payment['university_name'],
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "response": response
            }
            transactions.append(transaction_record)
            
            # Update session
            session_data['status'] = 'completed'
            session_data['transaction_id'] = transaction_id
            session_data['step'] = 'complete'
            
            # Send confirmation SMS
            transaction_details = {
                'amount': payment['amount'] / 100,
                'certificate_ref': payment['certificate_ref'],
                'transaction_id': transaction_id
            }
            sms_service.send_confirmation_sms(payment['phone'], transaction_details)
            
            print(f"✅ Payment Successful!")
            print(f"   Transaction ID: {transaction_id}")
            print(f"   Conversation ID: {conversation_id}")
            
            # Clean up
            del pending_payments[payment_id]
            
            return jsonify({
                "status": "success",
                "ussd_session_id": ussd_session_id,
                "transaction_id": transaction_id,
                "amount": payment['amount'] / 100,
                "certificate_ref": payment['certificate_ref'],
                "message": "Payment completed successfully"
            })
        else:
            # Payment failed
            error_msg = response.get('output_ResponseDesc', 'Payment processing failed')
            
            # Send failure SMS
            sms_service.send_failure_sms(payment['phone'], error_msg)
            
            session_data['status'] = 'failed'
            
            print(f"❌ Payment Failed: {error_msg}")
            
            return jsonify({
                "status": "failed",
                "error": error_msg,
                "message": "Payment failed. Please try again."
            }), 400
            
    except Exception as e:
        print(f"❌ Payment Error: {str(e)}")
        
        sms_service.send_failure_sms(payment['phone'], str(e))
        
        return jsonify({
            "status": "failed",
            "error": str(e),
            "message": "Payment processing error"
        }), 500

@app.route('/api/ussd/status/<ussd_session_id>', methods=['GET'])
def get_ussd_status(ussd_session_id):
    """Get USSD session status"""
    if ussd_session_id not in ussd_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session_data = ussd_sessions[ussd_session_id]
    
    return jsonify({
        "status": session_data.get('status'),
        "step": session_data.get('step'),
        "phone": session_data.get('phone_number'),
        "certificate_ref": session_data.get('certificate_ref'),
        "amount": session_data.get('amount', 0) / 100,
        "transaction_id": session_data.get('transaction_id')
    })

@app.route('/api/ussd/callback', methods=['POST'])
def ussd_callback():
    """Handle SMS reply with PIN (for real SMS integration)"""
    data = request.json
    phone = data.get('phone')
    message = data.get('message')  # Should contain PIN
    
    # Find active PIN session for this phone
    active_pin_session = None
    for pid, pin_data in pin_sessions.items():
        if pin_data['phone'] == phone and pin_data['expiry'] > datetime.now():
            active_pin_session = pid
            break
    
    if active_pin_session:
        # Auto-verify PIN and process payment
        pin = message.strip()
        pin_data = pin_sessions[active_pin_session]
        
        if pin == pin_data['pin']:
            # PIN matches - process payment
            return process_payment_from_callback(pin_data)
        else:
            return jsonify({"status": "failed", "message": "Invalid PIN"}), 400
    else:
        return jsonify({"status": "failed", "message": "No active session"}), 400

def process_payment_from_callback(pin_data):
    """Process payment from SMS callback"""
    ussd_session_id = pin_data['ussd_session_id']
    session_data = ussd_sessions[ussd_session_id]
    
    try:
        response = mpesa_client.process_b2b_payment(
            university_code="UNI001",
            amount=pin_data['amount'],
            certificate_ref=pin_data['certificate_ref'],
            description=f"Certificate verification - {pin_data['certificate_ref']}"
        )
        
        if response.get('output_ResponseCode') == 'INS-0':
            transaction_id = response.get('output_TransactionID')
            
            transaction_details = {
                'amount': pin_data['amount'] / 100,
                'certificate_ref': pin_data['certificate_ref'],
                'transaction_id': transaction_id
            }
            sms_service.send_confirmation_sms(pin_data['phone'], transaction_details)
            
            return jsonify({"status": "success", "transaction_id": transaction_id})
        else:
            return jsonify({"status": "failed", "message": "Payment failed"}), 400
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions"""
    return jsonify({
        "total": len(transactions),
        "transactions": transactions
    })

# ============================================
# Health Check
# ============================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "shortcode": os.getenv('SERVICE_PROVIDER_CODE', '110799'),
        "market": "vodacomLES",
        "active_sessions": len(ussd_sessions),
        "pending_payments": len(pending_payments)
    })

@app.route('/ussd_popup_test.html')
def serve_popup_test():
    """Serve the USSD popup test page"""
    return send_from_directory('.', 'ussd_popup_test.html')

@app.route('/')
def home():
    """Home page with test link"""
    return '''
    <h1>🚀 M-Pesa USSD Payment System</h1>
    <p><strong>Environment:</strong> Sandbox (No real money)</p>
    <p><a href="/ussd_popup_test.html">📱 Test M-Pesa USSD Flow with Popups</a></p>
    <h2>🔗 Available API Endpoints:</h2>
    <ul>
        <li><code>POST /api/ussd/initiate</code> - Start USSD flow</li>
        <li><code>POST /api/ussd/enter-phone</code> - Enter phone number</li>
        <li><code>POST /api/ussd/send-pin</code> - Send PIN request</li>
        <li><code>POST /api/ussd/verify-pin</code> - Verify PIN</li>
        <li><code>POST /api/ussd/process-payment</code> - Process payment</li>
        <li><code>GET /api/ussd/status/<id></code> - Check session status</li>
        <li><code>GET /api/transactions</code> - View all transactions</li>
    </ul>
    '''

# ============================================
# Main Entry Point
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting M-Pesa USSD Payment Flow Server")
    print("="*60)
    print(f"💳 Shortcode: {os.getenv('SERVICE_PROVIDER_CODE', '110799')}")
    print(f"🌐 Market: vodacomLES")
    print(f"🔗 Base URL: {os.getenv('BASE_URL', 'https://openapi.m-pesa.com')}")
    print(f"📱 USSD Flow Ready: /api/ussd/initiate")
    print(f"📨 SMS Service Ready: SMS will be sent with PIN")
    print("="*60)
    print("\n🔧 API Endpoints:")
    print("   POST /api/ussd/initiate - Start USSD flow")
    print("   POST /api/ussd/enter-phone - Enter phone number")
    print("   POST /api/ussd/send-pin - Send PIN via SMS")
    print("   POST /api/ussd/verify-pin - Verify PIN")
    print("   POST /api/ussd/process-payment - Process payment")
    print("   GET  /api/ussd/status/<id> - Check session status")
    print("   GET  /api/transactions - View all transactions")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

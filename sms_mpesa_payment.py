import uuid
import random
import requests
import base64
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import os
from dotenv import load_dotenv

# Import real SMS gateway
from real_sms_gateway import RealSMSGateway

load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================
# REAL SMS GATEWAY
# ============================================
# Use real SMS gateway if configured, otherwise fall back to simulation
try:
    if os.getenv('SMS_PROVIDER') and os.getenv('SMS_PROVIDER') != 'simulation':
        sms_gateway = RealSMSGateway()
        print(f"📱 Using REAL SMS Gateway: {os.getenv('SMS_PROVIDER')}")
    else:
        raise ImportError("Using simulation mode")
except ImportError:
    print("📱 Using SIMULATED SMS Gateway (for testing)")
    # Fall back to simulation
    class SMSGateway:
        """Simulated SMS Gateway for testing"""
        
        def __init__(self):
            self.sent_messages = []
            self.received_messages = []
            self.callback_handlers = []
            
        def send_sms(self, phone_number, message):
            """Simulate sending SMS to phone number"""
            sms_record = {
                "id": str(uuid.uuid4()),
                "to": phone_number,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "status": "sent"
            }
            self.sent_messages.append(sms_record)
            
            # Print to console for testing
            print(f"\n{'='*60}")
            print(f"📤 SIMULATED SMS SENT TO: {phone_number}")
            print(f"📝 MESSAGE:")
            print(f"{message}")
            print(f"{'='*60}\n")
            
            return sms_record
        
        def simulate_incoming_sms(self, from_phone, message):
            """Simulate receiving SMS (for testing)"""
            sms_record = {
                "id": str(uuid.uuid4()),
                "from": from_phone,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "status": "received"
            }
            self.received_messages.append(sms_record)
            
            print(f"\n📩 SMS RECEIVED FROM: {from_phone}")
            print(f"💬 MESSAGE: {message}")
            
            # Trigger callback handlers
            for handler in self.callback_handlers:
                handler(from_phone, message)
            
            return sms_record
        
        def register_callback(self, handler):
            """Register callback for incoming SMS"""
            self.callback_handlers.append(handler)
    
    sms_gateway = SMSGateway()

# ============================================
# SIMULATED M-PESA B2B CLIENT (Sandbox Mode)
# ============================================
class SimulatedMpesaB2BClient:
    """Simulated M-Pesa B2B client for testing"""
    
    def __init__(self):
        self.service_provider_code = os.getenv('SERVICE_PROVIDER_CODE', '110799')
        self.ecol_code = os.getenv('ECOL_CODE', '110799')
    
    def process_b2b_payment(self, university_code, amount, certificate_ref, description=None):
        """Simulate B2B payment processing"""
        print(f"\n💳 Processing B2B Payment...")
        print(f"   University Code: {university_code}")
        print(f"   ECOL Code: {self.ecol_code}")
        print(f"   Amount: {amount/100:.2f} LSL")
        print(f"   Certificate: {certificate_ref}")
        
        # Simulate processing time
        time.sleep(1)
        
        # Generate simulated response
        transaction_id = f"TXN{int(time.time())}{random.randint(1000, 9999)}"
        conversation_id = str(uuid.uuid4()).replace('-', '')[:20]
        
        # Simulate success (90% success rate for testing)
        if random.random() > 0.1:
            return {
                "output_ResponseCode": "INS-0",
                "output_ResponseDesc": "Transaction successful",
                "output_TransactionID": transaction_id,
                "output_ConversationID": conversation_id
            }
        else:
            return {
                "output_ResponseCode": "INS-1",
                "output_ResponseDesc": "Insufficient funds",
                "output_TransactionID": None,
                "output_ConversationID": conversation_id
            }

mpesa_client = SimulatedMpesaB2BClient()

# ============================================
# Transaction Storage
# ============================================
pending_transactions = {}      # Transactions waiting for PIN confirmation
completed_transactions = []    # Completed transactions
pin_attempts = {}              # Track PIN attempts

# ============================================
# SMS Payment Flow
# ============================================
class SMSPaymentFlow:
    
    def initiate_payment(self, phone_number, certificate_ref, university_name, amount, university_code):
        """
        Step 1: Initiate payment - Send SMS with PIN to user's phone
        """
        # Generate 4-digit PIN
        pin = str(random.randint(1000, 9999))
        
        # Create transaction session
        transaction_id = str(uuid.uuid4())
        
        pending_transactions[transaction_id] = {
            'transaction_id': transaction_id,
            'phone': phone_number,
            'certificate_ref': certificate_ref,
            'university_name': university_name,
            'university_code': university_code,
            'amount': amount,
            'pin': pin,
            'pin_attempts': 0,
            'status': 'pending_pin',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        
        # Format amount in LSL
        amount_lsl = f"{amount/100:.2f}"
        
        # Create SMS message with PIN
        sms_message = f"""🏫 ECOL Certificate Verification

Certificate: {certificate_ref}
University: {university_name}
Amount: {amount_lsl} LSL

🔐 Your PIN: {pin}

Reply with this PIN to confirm payment.
Valid for 10 minutes.

If you did not request this, ignore this message."""

        # Send SMS
        sms_gateway.send_sms(phone_number, sms_message)
        
        return {
            'status': 'pending',
            'transaction_id': transaction_id,
            'message': 'PIN sent via SMS',
            'expires_in': '10 minutes'
        }
    
    def process_pin_reply(self, phone_number, received_pin):
        """
        Step 2: Process incoming SMS with PIN
        """
        # Find pending transaction for this phone
        active_transaction = None
        
        for tx_id, tx in pending_transactions.items():
            if tx['phone'] == phone_number and tx['status'] == 'pending_pin':
                # Check if expired
                expires_at = datetime.fromisoformat(tx['expires_at'])
                if datetime.now() > expires_at:
                    tx['status'] = 'expired'
                    continue
                active_transaction = tx
                break
        
        if not active_transaction:
            # Send error SMS
            sms_gateway.send_sms(
                phone_number,
                "❌ No pending payment found. Please initiate a new payment."
            )
            return {'status': 'failed', 'reason': 'no_pending_transaction'}
        
        # Track PIN attempts
        tx_id = active_transaction['transaction_id']
        
        if tx_id not in pin_attempts:
            pin_attempts[tx_id] = 0
        
        pin_attempts[tx_id] += 1
        
        # Check if too many attempts
        if pin_attempts[tx_id] >= 3:
            active_transaction['status'] = 'failed_too_many_attempts'
            sms_gateway.send_sms(
                phone_number,
                "❌ Too many invalid PIN attempts. Please start a new payment."
            )
            return {'status': 'failed', 'reason': 'too_many_attempts'}
        
        # Verify PIN
        if received_pin == active_transaction['pin']:
            # PIN correct - process payment
            active_transaction['status'] = 'pin_verified'
            return self._process_payment(tx_id)
        else:
            # PIN incorrect
            remaining_attempts = 3 - pin_attempts[tx_id]
            sms_gateway.send_sms(
                phone_number,
                f"❌ Invalid PIN. You have {remaining_attempts} attempt(s) remaining.\n\nReply with correct PIN to confirm payment."
            )
            return {'status': 'failed', 'reason': 'invalid_pin', 'remaining_attempts': remaining_attempts}
    
    def _process_payment(self, transaction_id):
        """
        Step 3: Process B2B payment after PIN verification
        """
        tx = pending_transactions[transaction_id]
        phone = tx['phone']
        
        print(f"\n💳 Processing B2B Payment...")
        print(f"   Transaction ID: {transaction_id}")
        print(f"   Phone: {phone}")
        print(f"   Certificate: {tx['certificate_ref']}")
        print(f"   Amount: {tx['amount']/100:.2f} LSL")
        
        try:
            # Call M-Pesa B2B API
            response = mpesa_client.process_b2b_payment(
                university_code=tx['university_code'],
                amount=tx['amount'],
                certificate_ref=tx['certificate_ref'],
                description=f"Certificate verification - {tx['certificate_ref']}"
            )
            
            # Check response
            if response.get('output_ResponseCode') == 'INS-0':
                # Payment successful
                transaction_record = {
                    'transaction_id': transaction_id,
                    'mpesa_transaction_id': response.get('output_TransactionID'),
                    'conversation_id': response.get('output_ConversationID'),
                    'phone': phone,
                    'certificate_ref': tx['certificate_ref'],
                    'university_name': tx['university_name'],
                    'amount': tx['amount'],
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                }
                completed_transactions.append(transaction_record)
                
                # Mark as completed
                tx['status'] = 'completed'
                tx['mpesa_transaction_id'] = response.get('output_TransactionID')
                
                # Send confirmation SMS
                confirmation_sms = f"""✅ PAYMENT CONFIRMED

Amount: {tx['amount']/100:.2f} LSL
Certificate: {tx['certificate_ref']}
Transaction ID: {response.get('output_TransactionID')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Thank you for using ECOL Verification Service.
Your certificate will be verified shortly."""
                
                sms_gateway.send_sms(phone, confirmation_sms)
                
                return {
                    'status': 'success',
                    'transaction_id': transaction_id,
                    'mpesa_transaction_id': response.get('output_TransactionID'),
                    'message': 'Payment completed successfully'
                }
            else:
                # Payment failed
                error_msg = response.get('output_ResponseDesc', 'Payment processing failed')
                tx['status'] = 'failed'
                tx['error'] = error_msg
                
                failure_sms = f"""❌ PAYMENT FAILED

Certificate: {tx['certificate_ref']}
Amount: {tx['amount']/100:.2f} LSL
Reason: {error_msg}

Please try again or contact support."""
                
                sms_gateway.send_sms(phone, failure_sms)
                
                return {
                    'status': 'failed',
                    'reason': error_msg,
                    'message': 'Payment failed'
                }
                
        except Exception as e:
            tx['status'] = 'failed'
            tx['error'] = str(e)
            
            failure_sms = f"""❌ PAYMENT ERROR

Certificate: {tx['certificate_ref']}
Amount: {tx['amount']/100:.2f} LSL
Error: {str(e)}

Please try again later."""
            
            sms_gateway.send_sms(phone, failure_sms)
            
            return {
                'status': 'failed',
                'reason': str(e),
                'message': 'Payment error'
            }

payment_flow = SMSPaymentFlow()

# ============================================
# SMS Callback Handler
# ============================================
def handle_incoming_sms(from_phone, message):
    """Handle incoming SMS replies"""
    # Clean message (remove spaces, convert to uppercase)
    pin = message.strip()
    
    # Process PIN reply
    result = payment_flow.process_pin_reply(from_phone, pin)
    
    if result['status'] == 'success':
        print(f"✅ Payment completed for {from_phone}")
    elif result['status'] == 'failed':
        print(f"❌ Payment failed for {from_phone}: {result.get('reason')}")

# Register SMS callback
sms_gateway.register_callback(handle_incoming_sms)

# ============================================
# API Endpoints for Your App
# ============================================
@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    """
    Your app calls this when user enters phone number
    This sends SMS to user with PIN
    """
    data = request.json
    
    # Required fields
    required_fields = ['phone_number', 'certificate_ref', 'university_name', 'amount']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    phone = data['phone_number']
    certificate_ref = data['certificate_ref']
    university_name = data['university_name']
    amount = data['amount']
    university_code = data.get('university_code', 'UNI001')  # Default for testing
    
    # Validate phone number (Lesotho format)
    if not phone.startswith('266') and not phone.startswith('+266'):
        if phone.startswith('+'):
            phone = phone[1:]
        if len(phone) == 9 and phone.isdigit():
            phone = '266' + phone
        elif len(phone) == 12 and phone.startswith('266'):
            pass
        elif len(phone) == 11 and phone.startswith('266'):
            pass
        else:
            return jsonify({"error": "Invalid phone number. Use format: +266XXXXXXX or 266XXXXXXX"}), 400
    elif phone.startswith('+266'):
        # Keep the + for display but use without + for processing
        display_phone = phone
        phone = phone[1:]  # Remove + for processing
    else:
        display_phone = phone
    
    # Initiate payment flow
    result = payment_flow.initiate_payment(
        phone_number=phone,
        certificate_ref=certificate_ref,
        university_name=university_name,
        amount=amount,
        university_code=university_code
    )
    
    return jsonify(result)

@app.route('/api/payment/status/<transaction_id>', methods=['GET'])
def get_payment_status(transaction_id):
    """Check payment status"""
    if transaction_id in pending_transactions:
        tx = pending_transactions[transaction_id]
        return jsonify({
            'transaction_id': transaction_id,
            'status': tx['status'],
            'phone': tx['phone'],
            'certificate_ref': tx['certificate_ref'],
            'amount': tx['amount'] / 100,
            'expires_at': tx['expires_at']
        })
    
    # Check completed transactions
    for tx in completed_transactions:
        if tx['transaction_id'] == transaction_id:
            return jsonify(tx)
    
    return jsonify({"error": "Transaction not found"}), 404

@app.route('/api/payment/simulate-sms', methods=['POST'])
def simulate_incoming_sms():
    """
    For testing only - simulate SMS reply
    """
    data = request.json
    from_phone = data.get('from_phone')
    message = data.get('message')
    
    sms_gateway.simulate_incoming_sms(from_phone, message)
    
    return jsonify({"status": "sms_simulated"})

@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    """Get all transactions"""
    return jsonify({
        'pending': list(pending_transactions.values()),
        'completed': completed_transactions
    })

@app.route('/api/sms/sent', methods=['GET'])
def get_sent_sms():
    """Get all sent SMS (for monitoring)"""
    return jsonify({
        'total': len(sms_gateway.sent_messages),
        'messages': sms_gateway.sent_messages
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'shortcode': os.getenv('SERVICE_PROVIDER_CODE', '110799'),
        'pending_transactions': len(pending_transactions),
        'completed_transactions': len(completed_transactions)
    })

@app.route('/sms_test_page.html')
def serve_sms_test_page():
    """Serve the SMS test page"""
    return send_from_directory('.', 'sms_test_page.html')

@app.route('/simple_phone_popup.html')
def serve_simple_popup():
    """Serve simple phone popup"""
    return send_from_directory('.', 'simple_phone_popup.html')

@app.route('/')
def home():
    """Home page with test links"""
    return '''
    <h1>📱 SMS-Based M-Pesa Payment System</h1>
    <p><strong>Environment:</strong> Sandbox (No real money)</p>
    <p><a href="/simple_phone_popup.html">📱 Simple Phone Popup (Recommended)</a></p>
    <p><a href="/sms_test_page.html">📱 Full Test Page</a></p>
    <h2>🔗 Available API Endpoints:</h2>
    <ul>
        <li><code>POST /api/payment/initiate</code> - Start payment (send SMS with PIN)</li>
        <li><code>GET /api/payment/status/<id></code> - Check payment status</li>
        <li><code>POST /api/payment/simulate-sms</code> - Simulate SMS reply (testing)</li>
        <li><code>GET /api/transactions</code> - View all transactions</li>
        <li><code>GET /api/sms/sent</code> - View sent SMS logs</li>
    </ul>
    <h2>📱 SMS Flow:</h2>
    <ol>
        <li>User enters phone number in popup</li>
        <li>System sends SMS with PIN to that phone</li>
        <li>User replies to SMS with PIN</li>
        <li>System processes M-Pesa payment</li>
        <li>User receives confirmation SMS</li>
    </ol>
    '''

# ============================================
# Cleanup Expired Transactions (Background Task)
# ============================================
def cleanup_expired_transactions():
    """Remove expired transactions"""
    while True:
        time.sleep(60)  # Run every minute
        now = datetime.now()
        expired = []
        
        for tx_id, tx in pending_transactions.items():
            if tx['status'] == 'pending_pin':
                expires_at = datetime.fromisoformat(tx['expires_at'])
                if now > expires_at:
                    tx['status'] = 'expired'
                    expired.append(tx_id)
                    
                    # Send expiry SMS
                    sms_gateway.send_sms(
                        tx['phone'],
                        "⏰ Payment session expired. Please start a new payment."
                    )
        
        print(f"🧹 Cleaned up {len(expired)} expired transactions")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_transactions, daemon=True)
cleanup_thread.start()

# ============================================
# Main Entry Point
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting SMS-Based M-Pesa Payment System")
    print("="*60)
    print(f"💳 Shortcode: {os.getenv('SERVICE_PROVIDER_CODE', '110799')}")
    print(f"🌐 Market: vodacomLES")
    print(f"📱 SMS Flow: User enters phone → SMS with PIN → Reply with PIN → Payment")
    print("\n🔧 API Endpoints:")
    print("   POST /api/payment/initiate - Start payment (send SMS with PIN)")
    print("   GET  /api/payment/status/<id> - Check payment status")
    print("   POST /api/payment/simulate-sms - Simulate SMS reply (testing)")
    print("   GET  /api/transactions - View all transactions")
    print("   GET  /api/sms/sent - View sent SMS logs")
    print("="*60)
    print("\n📱 SMS FLOW:")
    print("   1. User enters phone number in your app")
    print("   2. System sends SMS with PIN to that phone")
    print("   3. User replies to SMS with the PIN")
    print("   4. System processes M-Pesa payment")
    print("   5. User receives confirmation SMS")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

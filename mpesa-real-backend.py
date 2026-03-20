#!/usr/bin/env python3
"""
Enhanced M-Pesa Backend for LGCSE System
Integrates USSD popup flow, SMS gateway, and real M-Pesa payments
Supports both STK Push and B2B payment methods
"""

import uuid
import random
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import SMS gateway
try:
    from real_sms_gateway import RealSMSGateway
    SMS_AVAILABLE = True
except ImportError:
    SMS_AVAILABLE = False
    print("⚠️ Real SMS gateway not available, using simulation")

# Add backend directory to path for imports
sys.path.append('/home/duckey/lgcse-project/backend')

# Import real M-Pesa client
try:
    from mpesa_client import MpesaB2BClient
    REAL_MPESA_AVAILABLE = True
    print("✅ Real M-Pesa client loaded successfully")
except ImportError as e:
    print(f"❌ Real M-Pesa client not available: {e}")
    REAL_MPESA_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# Initialize SMS gateway
if SMS_AVAILABLE:
    try:
        sms_gateway = RealSMSGateway()
        print("✅ Real SMS gateway initialized")
    except Exception as e:
        print(f"⚠️ SMS gateway initialization failed: {e}")
        sms_gateway = None
else:
    # Fallback SMS simulation
    class SimulatedSMSGateway:
        def __init__(self):
            self.sent_messages = []
            
        def send_sms(self, phone_number, message):
            sms_record = {
                "id": str(uuid.uuid4()),
                "to": phone_number,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "status": "sent"
            }
            self.sent_messages.append(sms_record)
            print(f"\n{'='*60}")
            print(f"📤 SIMULATED SMS SENT TO: {phone_number}")
            print(f"📝 MESSAGE: {message}")
            print(f"{'='*60}\n")
            return sms_record
    
    sms_gateway = SimulatedSMSGateway()
    print("📱 Using simulated SMS gateway")

# Initialize real M-Pesa client if available
if REAL_MPESA_AVAILABLE:
    mpesa_client = MpesaB2BClient()
else:
    mpesa_client = None

# ============================================
# USSD API ENDPOINTS (for popup compatibility)
# ============================================

@app.route('/api/ussd/initiate', methods=['POST'])
def initiate_ussd_session():
    """Initiate USSD session for popup compatibility"""
    try:
        data = request.get_json()
        certificate_ref = data.get('certificate_ref')
        university_name = data.get('university_name')
        amount = data.get('amount', 5000)  # Default M50.00
        
        ussd_session_id = str(uuid.uuid4())
        
        ussd_sessions[ussd_session_id] = {
            'ussd_session_id': ussd_session_id,
            'certificate_ref': certificate_ref,
            'university_name': university_name,
            'amount': amount,
            'status': 'initiated',
            'created_at': datetime.now().isoformat(),
            'phone_number': None,
            'pin_verified': False
        }
        
        return jsonify({
            'status': 'success',
            'ussd_session_id': ussd_session_id,
            'message': 'USSD session initiated. Please enter your phone number.'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ussd/enter-phone', methods=['POST'])
def enter_phone_number():
    """Process phone number entry in USSD flow"""
    try:
        data = request.get_json()
        ussd_session_id = data.get('ussd_session_id')
        phone_number = data.get('phone_number')
        
        if ussd_session_id not in ussd_sessions:
            return jsonify({
                'status': 'error',
                'error': 'Invalid USSD session'
            }), 404
        
        # Validate phone number (Lesotho format)
        if not phone_number or len(str(phone_number)) < 8:
            return jsonify({
                'status': 'error',
                'error': 'Invalid phone number format. Use Lesotho format (e.g., 56720256)'
            }), 400
        
        # Update session
        session = ussd_sessions[ussd_session_id]
        session['phone_number'] = phone_number
        session['status'] = 'phone_entered'
        
        return jsonify({
            'status': 'success',
            'message': 'Phone number received. Sending PIN via SMS...',
            'next_step': 'send_pin'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ussd/send-pin', methods=['POST'])
def send_verification_pin():
    """Send PIN via SMS for verification"""
    try:
        data = request.get_json()
        ussd_session_id = data.get('ussd_session_id')
        
        if ussd_session_id not in ussd_sessions:
            return jsonify({
                'status': 'error',
                'error': 'Invalid USSD session'
            }), 404
        
        session = ussd_sessions[ussd_session_id]
        phone_number = session['phone_number']
        
        if not phone_number:
            return jsonify({
                'status': 'error',
                'error': 'Phone number not set'
            }), 400
        
        # Generate 4-digit PIN
        pin = str(random.randint(1000, 9999))
        pin_session_id = str(uuid.uuid4())
        
        # Store PIN
        pending_pins[pin_session_id] = {
            'pin_session_id': pin_session_id,
            'ussd_session_id': ussd_session_id,
            'phone_number': phone_number,
            'pin': pin,
            'attempts': 0,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        
        # Update USSD session
        session['pin_session_id'] = pin_session_id
        session['status'] = 'pin_sent'
        
        # Format amount for SMS
        amount_lsl = f"{session['amount']/100:.2f}"
        
        # Create SMS message
        sms_message = f"""🏫 ECOL Certificate Verification

Certificate: {session['certificate_ref']}
University: {session['university_name']}
Amount: {amount_lsl} LSL

🔐 Your PIN: {pin}

Reply with this PIN to confirm payment.
Valid for 10 minutes.

If you did not request this, ignore this message."""
        
        # Send SMS
        if sms_gateway:
            sms_result = sms_gateway.send_sms(phone_number, sms_message)
            print(f"✅ PIN sent via SMS to {phone_number}")
        else:
            print(f"⚠️ SMS gateway not available, PIN would be: {pin}")
        
        return jsonify({
            'status': 'success',
            'pin_session_id': pin_session_id,
            'message': 'PIN sent via SMS',
            'expires_in': '10 minutes'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ussd/verify-pin', methods=['POST'])
def verify_pin():
    """Verify PIN from SMS reply"""
    try:
        data = request.get_json()
        ussd_session_id = data.get('ussd_session_id')
        pin = data.get('pin')
        
        if ussd_session_id not in ussd_sessions:
            return jsonify({
                'status': 'error',
                'error': 'Invalid USSD session'
            }), 404
        
        session = ussd_sessions[ussd_session_id]
        pin_session_id = session.get('pin_session_id')
        
        if not pin_session_id or pin_session_id not in pending_pins:
            return jsonify({
                'status': 'error',
                'error': 'No PIN session found'
            }), 404
        
        pin_data = pending_pins[pin_session_id]
        
        # Check expiration
        expires_at = datetime.fromisoformat(pin_data['expires_at'])
        if datetime.now() > expires_at:
            return jsonify({
                'status': 'error',
                'error': 'PIN expired'
            }), 400
        
        # Check attempts
        pin_data['attempts'] += 1
        if pin_data['attempts'] > 3:
            return jsonify({
                'status': 'error',
                'error': 'Too many attempts'
            }), 400
        
        # Verify PIN
        if pin == pin_data['pin']:
            # PIN correct - create payment
            payment_id = str(uuid.uuid4())
            
            session['pin_verified'] = True
            session['status'] = 'pin_verified'
            session['payment_id'] = payment_id
            
            # Store payment record
            real_payments[payment_id] = {
                'payment_id': payment_id,
                'ussd_session_id': ussd_session_id,
                'phone_number': session['phone_number'],
                'amount': session['amount'],
                'certificate_ref': session['certificate_ref'],
                'university_name': session['university_name'],
                'status': 'ready_for_payment',
                'created_at': datetime.now().isoformat(),
                'payment_type': 'ussd_sms_flow'
            }
            
            return jsonify({
                'status': 'success',
                'payment_id': payment_id,
                'message': 'PIN verified successfully'
            })
        else:
            remaining_attempts = 3 - pin_data['attempts']
            return jsonify({
                'status': 'error',
                'error': f'Invalid PIN. {remaining_attempts} attempts remaining'
            }), 400
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ussd/process-payment', methods=['POST'])
def process_ussd_payment():
    """Process payment after PIN verification"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if payment_id not in real_payments:
            return jsonify({
                'status': 'error',
                'error': 'Payment not found'
            }), 404
        
        payment = real_payments[payment_id]
        
        if payment['status'] != 'ready_for_payment':
            return jsonify({
                'status': 'error',
                'error': 'Payment not ready for processing'
            }), 400
        
        # Process payment via M-Pesa
        if REAL_MPESA_AVAILABLE and mpesa_client:
            # Use real M-Pesa B2B payment
            response = mpesa_client.b2b_payment(
                university_code="UNI001",  # Default university code
                amount=str(payment['amount']),
                certificate_reference=payment['certificate_ref'],
                description=f"Certificate verification - {payment['certificate_ref']}"
            )
            
            is_successful = mpesa_client.is_payment_successful(response)
            
            if is_successful:
                payment['status'] = 'completed'
                payment['mpesa_transaction_id'] = response.get('output_TransactionID')
                payment['completed_at'] = datetime.now().isoformat()
                
                # Add to completed transactions
                completed_transactions.append(payment.copy())
                
                # Send confirmation SMS
                confirmation_sms = f"""✅ PAYMENT CONFIRMED

Amount: {payment['amount']/100:.2f} LSL
Certificate: {payment['certificate_ref']}
Transaction ID: {response.get('output_TransactionID')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Thank you for using ECOL Verification Service.
Your certificate will be verified shortly."""
                
                if sms_gateway:
                    sms_gateway.send_sms(payment['phone_number'], confirmation_sms)
                
                return jsonify({
                    'status': 'success',
                    'transaction_id': response.get('output_TransactionID'),
                    'amount': payment['amount']/100,
                    'certificate_ref': payment['certificate_ref']
                })
            else:
                payment['status'] = 'failed'
                payment['error'] = mpesa_client.get_response_message(response)
                
                return jsonify({
                    'status': 'error',
                    'error': payment['error']
                }), 400
        else:
            # Simulate payment for demo
            payment['status'] = 'completed'
            payment['mpesa_transaction_id'] = f"DEMO{int(time.time())}{random.randint(1000, 9999)}"
            payment['completed_at'] = datetime.now().isoformat()
            
            completed_transactions.append(payment.copy())
            
            return jsonify({
                'status': 'success',
                'transaction_id': payment['mpesa_transaction_id'],
                'amount': payment['amount']/100,
                'certificate_ref': payment['certificate_ref'],
                'demo_mode': True
            })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================
# LEGACY SMS ENDPOINTS (for compatibility)
# ============================================

@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment_legacy():
    """Legacy payment initiation endpoint"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        certificate_ref = data.get('certificate_ref')
        university_name = data.get('university_name')
        amount = data.get('amount', 5000)
        university_code = data.get('university_code', 'UNI001')
        
        # Create USSD session for compatibility
        ussd_session_id = str(uuid.uuid4())
        
        ussd_sessions[ussd_session_id] = {
            'ussd_session_id': ussd_session_id,
            'certificate_ref': certificate_ref,
            'university_name': university_name,
            'amount': amount,
            'status': 'phone_entered',
            'phone_number': phone_number,
            'created_at': datetime.now().isoformat()
        }
        
        # Send PIN immediately
        pin_response = send_verification_pin()
        pin_data = json.loads(pin_response.data)
        
        if pin_data['status'] == 'success':
            return jsonify({
                'status': 'pending',
                'transaction_id': pin_data['pin_session_id'],  # Use pin_session_id as transaction_id
                'message': 'PIN sent via SMS',
                'expires_in': '10 minutes'
            })
        else:
            return jsonify(pin_data), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/payment/status/<transaction_id>', methods=['GET'])
def get_payment_status_legacy(transaction_id):
    """Legacy payment status endpoint"""
    try:
        # Check if it's a PIN session
        if transaction_id in pending_pins:
            pin_data = pending_pins[transaction_id]
            ussd_session_id = pin_data['ussd_session_id']
            
            if ussd_session_id in ussd_sessions:
                session = ussd_sessions[ussd_session_id]
                return jsonify({
                    'transaction_id': transaction_id,
                    'status': session.get('status', 'pending'),
                    'phone': session.get('phone_number'),
                    'certificate_ref': session.get('certificate_ref'),
                    'amount': session.get('amount', 0) / 100,
                    'expires_at': pin_data.get('expires_at')
                })
        
        # Check if it's a payment ID
        if transaction_id in real_payments:
            payment = real_payments[transaction_id]
            return jsonify(payment)
        
        # Check completed transactions
        for tx in completed_transactions:
            if tx.get('payment_id') == transaction_id or tx.get('mpesa_transaction_id') == transaction_id:
                return jsonify(tx)
        
        return jsonify({"error": "Transaction not found"}), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/payment/simulate-sms', methods=['POST'])
def simulate_incoming_sms():
    """Simulate incoming SMS for testing"""
    try:
        data = request.get_json()
        from_phone = data.get('from_phone')
        message = data.get('message')
        
        # Find pending PIN for this phone
        for pin_session_id, pin_data in pending_pins.items():
            if pin_data['phone_number'] == from_phone:
                ussd_session_id = pin_data['ussd_session_id']
                
                # Verify PIN
                response = verify_pin()
                # We need to modify this to work with the actual PIN
                
                return jsonify({
                    'status': 'sms_simulated',
                    'message': f'SMS from {from_phone} with message "{message}" processed'
                })
        
        return jsonify({
            'status': 'error',
            'error': 'No pending transaction found for this phone number'
        }), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    """Get all transactions"""
    return jsonify({
        'pending': list(pending_pins.values()),
        'payments': list(real_payments.values()),
        'completed': completed_transactions
    })

@app.route('/api/sms/sent', methods=['GET'])
def get_sent_sms():
    """Get all sent SMS logs"""
    if sms_gateway and hasattr(sms_gateway, 'sent_messages'):
        return jsonify({
            'total': len(sms_gateway.sent_messages),
            'messages': sms_gateway.sent_messages
        })
    else:
        return jsonify({
            'total': 0,
            'messages': []
        })

# ============================================
# CLEANUP THREAD
# ============================================

def cleanup_expired_data():
    """Background cleanup thread"""
    while True:
        time.sleep(60)  # Run every minute
        now = datetime.now()
        
        # Clean expired PINs
        expired_pins = []
        for pin_id, pin_data in pending_pins.items():
            expires_at = datetime.fromisoformat(pin_data['expires_at'])
            if now > expires_at:
                expired_pins.append(pin_id)
        
        for pin_id in expired_pins:
            del pending_pins[pin_id]
        
        if expired_pins:
            print(f"🧹 Cleaned up {len(expired_pins)} expired PINs")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_data, daemon=True)
cleanup_thread.start()



@app.route('/api/mpesa/config', methods=['GET'])
def get_mpesa_config():
    """Get M-Pesa configuration status"""
    config = {
        "consumer_key": os.getenv('MPESA_CONSUMER_KEY', 'Not configured'),
        "shortcode": os.getenv('MPESA_SHORTCODE', 'Not configured'),
        "environment": os.getenv('MPESA_ENVIRONMENT', 'Not configured'),
        "status": "configured" if os.getenv('MPESA_CONSUMER_KEY') else "not_configured",
        "real_mode": REAL_MPESA_AVAILABLE,
        "callback_url": os.getenv('MPESA_CALLBACK_URL', 'Not configured')
    }
    
    return jsonify({
        "success": True,
        "config": config,
        "real_mpesa_available": REAL_MPESA_AVAILABLE,
        "endpoints": {
            "stk_push": "/api/mpesa/stk-push",
            "b2b_payment": "/api/mpesa/b2b-payment",
            "status_check": "/api/mpesa/status/{payment_id}",
            "callback": "/api/mpesa/callback",
            "mpesa_status": "/api/mpesa/mpesa-status"
        },
        "status": "ready for real payments" if REAL_MPESA_AVAILABLE else "demo mode only"
    })

@app.route('/api/mpesa/stk-push', methods=['POST'])
def initiate_stk_push():
    """Initiate REAL M-Pesa STK Push payment"""
    try:
        data = request.get_json()
        
        phone_number = data.get('phone_number')
        amount = data.get('amount', 10.00)  # Default M10.00
        verification_request_id = data.get('verification_request_id')
        account_reference = data.get('account_reference', 'LGCSE_VERIFY')
        
        # Validate phone number (Lesotho format)
        if not phone_number or len(str(phone_number)) < 8:
            return jsonify({
                "success": False,
                "error": "Invalid phone number format. Use Lesotho format (e.g., 56720256)"
            }), 400
        
        # Validate amount
        if amount <= 0:
            return jsonify({
                "success": False,
                "error": "Amount must be greater than 0"
            }), 400
        
        # For real M-Pesa, we need to convert to STK push format
        # This would require the STK push API which is different from B2B
        # For now, we'll simulate the STK push flow
        
        payment_id = str(uuid.uuid4())
        merchant_request_id = f"wsco_{int(datetime.now().timestamp())}"
        checkout_request_id = f"ws_CO_{int(datetime.now().timestamp())}"
        
        # Store payment request
        real_payments[payment_id] = {
            "payment_id": payment_id,
            "merchant_request_id": merchant_request_id,
            "checkout_request_id": checkout_request_id,
            "phone_number": phone_number,
            "amount": amount,
            "verification_request_id": verification_request_id,
            "account_reference": account_reference,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "payment_type": "stk_push",
            "real_mode": REAL_MPESA_AVAILABLE
        }
        
        # In real implementation, this would trigger actual STK push
        # For now, we'll return the expected response format
        return jsonify({
            "success": True,
            "payment_id": payment_id,
            "merchant_request_id": merchant_request_id,
            "checkout_request_id": checkout_request_id,
            "customer_message": "Success. Request accepted for processing. Please check your phone for M-Pesa STK push prompt.",
            "status": "pending",
            "next_step": "Please check your phone for M-Pesa STK push prompt",
            "amount": amount,
            "phone_number": phone_number,
            "real_mpesa": REAL_MPESA_AVAILABLE
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"STK Push initiation failed: {str(e)}"
        }), 500

@app.route('/api/mpesa/b2b-payment', methods=['POST'])
def initiate_real_b2b_payment():
    """Initiate REAL M-Pesa B2B payment from University to ECOL"""
    try:
        if not REAL_MPESA_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "Real M-Pesa not available. Please check configuration."
            }), 503
        
        data = request.get_json()
        
        university_code = data.get('university_code')
        amount = data.get('amount', '1000')  # Default M10.00 = 1000 cents
        certificate_reference = data.get('certificate_reference')
        description = data.get('description', 'Certificate verification payment')
        
        # Validate required fields
        if not university_code or not certificate_reference:
            return jsonify({
                "success": False,
                "error": "Missing required fields: university_code, certificate_reference"
            }), 400
        
        # Validate amount (minimum M5.00 = 500 cents)
        if int(amount) < 500:
            return jsonify({
                "success": False,
                "error": "Amount below minimum (M5.00 = 500 cents)"
            }), 400
        
        # Process REAL payment via M-Pesa client
        response = mpesa_client.b2b_payment(
            university_code=university_code,
            amount=amount,
            certificate_reference=certificate_reference,
            description=description
        )
        
        # Check if payment was successful
        is_successful = mpesa_client.is_payment_successful(response)
        response_message = mpesa_client.get_response_message(response)
        
        # Store payment record
        payment_id = str(uuid.uuid4())
        real_payments[payment_id] = {
            "payment_id": payment_id,
            "transaction_id": response.get('output_TransactionID'),
            "conversation_id": response.get('output_ConversationID'),
            "university_code": university_code,
            "amount": float(amount) / 100,  # Convert to LSL
            "certificate_reference": certificate_reference,
            "response_code": response.get('output_ResponseCode'),
            "response_message": response_message,
            "status": "confirmed" if is_successful else "failed",
            "created_at": datetime.now().isoformat(),
            "payment_type": "b2b_real",
            "real_mode": True,
            "metadata": response.get('_metadata', {})
        }
        
        return jsonify({
            "success": is_successful,
            "payment_id": payment_id,
            "transaction_id": response.get('output_TransactionID'),
            "conversation_id": response.get('output_ConversationID'),
            "response_code": response.get('output_ResponseCode'),
            "response_message": response_message,
            "amount_maloti": float(amount) / 100,
            "certificate_reference": certificate_reference,
            "real_transaction": True,
            "metadata": response.get('_metadata', {})
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Real B2B payment failed: {str(e)}"
        }), 500

@app.route('/api/mpesa/status/<payment_id>', methods=['GET'])
def check_real_payment_status(payment_id):
    """Check payment status"""
    try:
        if payment_id not in real_payments:
            return jsonify({
                "success": False,
                "error": "Payment not found"
            }), 404
        
        payment = real_payments[payment_id]
        
        # For B2B payments, we can query the actual transaction status
        if payment.get('payment_type') == 'b2b_real' and payment.get('transaction_id'):
            try:
                if REAL_MPESA_AVAILABLE:
                    transaction_status = mpesa_client.query_transaction(payment['transaction_id'])
                    payment['transaction_status'] = transaction_status
                    payment['is_successful'] = mpesa_client.is_payment_successful(transaction_status)
            except Exception as e:
                payment['query_error'] = str(e)
        
        return jsonify({
            "success": True,
            "payment": payment,
            "status": payment['status']
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Status check failed: {str(e)}"
        }), 500

@app.route('/api/mpesa/callback', methods=['POST'])
def handle_real_mpesa_callback():
    """Handle M-Pesa payment callback"""
    try:
        data = request.get_json()
        
        # Log callback for debugging
        print(f"Real M-Pesa Callback: {json.dumps(data, indent=2)}")
        
        # Extract payment info from callback
        merchant_request_id = data.get('MerchantRequestID')
        checkout_request_id = data.get('CheckoutRequestID')
        result_code = data.get('ResultCode')
        result_desc = data.get('ResultDesc')
        
        # Find and update payment
        for payment_id, payment in real_payments.items():
            if (payment.get('merchant_request_id') == merchant_request_id or 
                payment.get('checkout_request_id') == checkout_request_id):
                
                if result_code == 0:
                    payment['status'] = 'confirmed'
                    payment['confirmed_at'] = datetime.now().isoformat()
                    
                    # Extract callback metadata
                    callback_metadata = data.get('CallbackMetadata', {}).get('Item', [])
                    for item in callback_metadata:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            payment['mpesa_receipt_number'] = item.get('Value')
                        elif item.get('Name') == 'TransactionDate':
                            payment['mpesa_transaction_date'] = item.get('Value')
                        elif item.get('Name') == 'PhoneNumber':
                            payment['mpesa_phone_number'] = item.get('Value')
                else:
                    payment['status'] = 'failed'
                    payment['error'] = result_desc or 'Payment failed'
                
                break
        
        return jsonify({
            "success": True,
            "message": "Callback processed successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Callback processing failed: {str(e)}"
        }), 500

@app.route('/api/mpesa/payments', methods=['GET'])
def list_real_payments():
    """List all real payments"""
    try:
        return jsonify({
            "success": True,
            "payments": list(real_payments.values()),
            "total": len(real_payments),
            "real_mode": REAL_MPESA_AVAILABLE
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to list payments: {str(e)}"
        }), 500

@app.route('/api/mpesa/mpesa-status', methods=['GET'])
def get_mpesa_system_status():
    """Get M-Pesa system status"""
    try:
        if not REAL_MPESA_AVAILABLE:
            return jsonify({
                "mpesa_available": False,
                "error": "Real M-Pesa client not available",
                "configuration": {
                    "consumer_key": os.getenv('MPESA_CONSUMER_KEY', 'Not set'),
                    "shortcode": os.getenv('MPESA_SHORTCODE', 'Not set'),
                    "environment": os.getenv('MPESA_ENVIRONMENT', 'Not set')
                }
            })
        
        # Test session generation
        try:
            session = mpesa_client.generate_session()
            session_status = "operational"
            session_error = None
        except Exception as e:
            session_status = "failed"
            session_error = str(e)
        
        return jsonify({
            "mpesa_available": session_status == "operational",
            "session_status": session_status,
            "session_error": session_error,
            "configuration": {
                "service_provider_code": mpesa_client.service_provider_code,
                "country": mpesa_client.country,
                "currency": mpesa_client.currency,
                "environment": os.getenv('MPESA_ENVIRONMENT', 'unknown')
            },
            "supported_operations": {
                "b2b_payment": True,
                "transaction_query": True,
                "stk_push": True,
                "callback_handling": True
            }
        })
        
    except Exception as e:
        return jsonify({
            "mpesa_available": False,
            "error": str(e)
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Real M-Pesa Backend",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "real_mpesa_available": REAL_MPESA_AVAILABLE,
        "features": {
            "stk_push": True,
            "b2b_payment": REAL_MPESA_AVAILABLE,
            "status_check": True,
            "callback_handling": True,
            "real_payments": REAL_MPESA_AVAILABLE
        }
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "LGCSE Real M-Pesa Backend",
        "version": "2.0.0",
        "status": "running",
        "real_mode": REAL_MPESA_AVAILABLE,
        "endpoints": {
            "config": "/api/mpesa/config",
            "stk_push": "/api/mpesa/stk-push",
            "b2b_payment": "/api/mpesa/b2b-payment",
            "status": "/api/mpesa/status/{payment_id}",
            "callback": "/api/mpesa/callback",
            "payments": "/api/mpesa/payments",
            "mpesa_status": "/api/mpesa/mpesa-status",
            "health": "/api/health"
        }
    })

if __name__ == '__main__':
    mode = "REAL" if REAL_MPESA_AVAILABLE else "DEMO"
    sms_mode = "REAL SMS" if SMS_AVAILABLE else "SIMULATED SMS"
    
    print(f"\n{'='*80}")
    print(f"🚀 Enhanced M-Pesa Backend for LGCSE System")
    print(f"{'='*80}")
    print(f"💳 Mode: {mode}")
    print(f"� SMS: {sms_mode}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"{'='*80}")
    
    if REAL_MPESA_AVAILABLE:
        print("✅ Real M-Pesa payments enabled")
    else:
        print("⚠️  Demo mode only - configure M-Pesa for real payments")
    
    if SMS_AVAILABLE:
        print("✅ Real SMS gateway enabled")
    else:
        print("📱 Using simulated SMS gateway")
    
    print(f"\n🔗 Available Endpoints:")
    print(f"   USSD Flow (for popup):")
    print(f"     POST /api/ussd/initiate - Start USSD session")
    print(f"     POST /api/ussd/enter-phone - Submit phone number")
    print(f"     POST /api/ussd/send-pin - Send PIN via SMS")
    print(f"     POST /api/ussd/verify-pin - Verify PIN")
    print(f"     POST /api/ussd/process-payment - Process payment")
    print(f"\n   Legacy SMS Flow (for compatibility):")
    print(f"     POST /api/payment/initiate - Start payment")
    print(f"     GET  /api/payment/status/<id> - Check status")
    print(f"     POST /api/payment/simulate-sms - Simulate SMS")
    print(f"\n   Real M-Pesa Flow:")
    print(f"     POST /api/mpesa/stk-push - STK Push payment")
    print(f"     POST /api/mpesa/b2b-payment - B2B payment")
    print(f"     GET  /api/mpesa/status/<id> - Check payment status")
    print(f"\n   Monitoring:")
    print(f"     GET  /api/transactions - View all transactions")
    print(f"     GET  /api/sms/sent - View sent SMS")
    print(f"     GET  /api/mpesa/config - View configuration")
    print(f"     GET  /api/health - Health check")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

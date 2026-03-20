from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from mpesa_utils import MpesaClient
import time
import uuid
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React

# Your M-Pesa credentials from environment
API_KEY = os.getenv('MPESA_API_KEY', '6bc4157dbowkdd409118e0978dc6991a')
PUBLIC_KEY = os.getenv('MPESA_PUBLIC_KEY', """MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAietPTdEyyoV/wvxRjS5pSn3ZBQH9hnVtQC9SFLgM9IkomEX9Vu9fBg2MzWSSqkQlaYIGFGH3d69Q5NOWkRo+Y8p5a61sc9hZ+ItAiEL9KIbZzhnMwi12jUYCTff0bVTsTGSNUePQ2V42sToOIKCeBpUtwWKhhW3CSpK7S1iJhS9H22/BT/pk21Jd8btwMLUHfVD95iXbHNM8u6vFaYuHczx966T7gpa9RGGXRtiOr3ScJq1515tzOSOsHTPHLTun59nxxJiEjKoI4Lb9h6IlauvcGAQHp5q6/2XmxuqZdGzh39uLac8tMSmY3vC3fiHYC3iMyTb7eXqATIhDUOf9mOSbgZMS19iiVZvz8igDl950IMcelJwcj0qCLoufLE5y8ud5WIw47OCVkD7tcAEPmVWlCQ744SIM5afw+Jg50T1SEtu3q3GiL0UQ6KTLDyDEt5BL9HWXAIXsjFdPDpX1jtxZavVQV+Jd7FXhuPQuDbh12liTROREdzatYWRnrhzeOJ5Se9xeXLvYSj8DmAI4iFf2cVtWCzj/02uK4+iIGXlX7lHP1W+tycLS7Pe2RdtC2+oz5RSSqb5jI4+3iEY/vZjSMBVk69pCDzZy4ZE8LBgyEvSabJ/cddwWmShcRS+21XvGQ1uXYLv0FCTEHHobCfmn2y8bJBb/Hct53BaojWUCAwEAAQ==""")

# Initialize M-Pesa client - SANDBOX MODE (NO REAL MONEY)
environment = "sandbox"  # Sandbox mode - no real transactions
mpesa = MpesaClient(API_KEY, PUBLIC_KEY, environment=environment)

# Store sessions (in production, use Redis or database)
sessions = {}
ussd_sessions = {}
pin_sessions = {}
mpesa_notifications = []  # Store M-Pesa notifications instead of SMS logs

@app.route('/api/mpesa/generate-session', methods=['POST'])
def generate_session():
    """Generate M-Pesa session"""
    try:
        session_id = mpesa.generate_session()
        if session_id:
            # Store session with timestamp
            sessions['current'] = {
                'id': session_id,
                'created_at': time.time()
            }
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': 'Sandbox session generated - NO REAL MONEY',
                'environment': environment,
                'shortcode': mpesa.shortcode,
                'endpoint': f"{mpesa.base_url}/sandbox/ipg/v2/{mpesa.market}/getSession/",
                'warning': '🔴 SANDBOX MODE - No real USSD prompts, no real money, no SMS'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate session'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/mpesa/direct-debit', methods=['POST'])
def direct_debit():
    """Process direct debit payment"""
    data = request.json
    
    # Check if we have a valid session
    if 'current' not in sessions:
        # Generate new session
        session_id = mpesa.generate_session()
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Could not generate session'
            }), 500
        # Wait for session to activate
        time.sleep(2)
    else:
        session_id = sessions['current']['id']
    
    # Get request parameters
    customer_msisdn = data.get('customer_msisdn')
    amount = data.get('amount')
    mandate_id = data.get('mandate_id', '15045')
    third_party_ref = data.get('reference', f'ref_{int(time.time())}')
    
    # Validate
    if not customer_msisdn or not amount:
        return jsonify({
            'success': False,
            'message': 'Customer MSISDN and amount are required'
        }), 400
    
    # Process payment
    result = mpesa.direct_debit_payment(
        session_id=session_id,
        customer_msisdn=customer_msisdn,
        amount=amount,
        third_party_ref=third_party_ref,
        mandate_id=mandate_id,
        third_party_conversation_id=str(uuid.uuid4()).replace('-', '')
    )
    
    return jsonify(result)

@app.route('/api/mpesa/test-scenarios', methods=['GET'])
def test_scenarios():
    """Return test scenarios for frontend"""
    scenarios = {
        'success': '00000000000000000001',
        'internal_error': '00000000000000000002',
        'transaction_failed': '00000000000000000003',
        'timeout': '00000000000000000004',
        'service_unavailable': '00000000000000000005'
    }
    return jsonify(scenarios)

@app.route('/api/mpesa/config', methods=['GET'])
def get_config():
    """Get M-Pesa configuration"""
    return jsonify({
        'success': True,
        'config': {
            'shortcode': mpesa.shortcode,
            'market': mpesa.market,
            'environment': environment,
            'base_url': mpesa.base_url,
            'api_key_provided': bool(API_KEY),
            'public_key_provided': bool(PUBLIC_KEY)
        }
    })

@app.route('/api/mpesa/status', methods=['GET'])
def get_status():
    """Get M-Pesa service status"""
    try:
        # Test session generation
        session_id = mpesa.generate_session()
        return jsonify({
            'success': True,
            'status': 'operational' if session_id else 'failed',
            'environment': environment,
            'shortcode': mpesa.shortcode,
            'market': mpesa.market
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'M-Pesa Real Backend',
        'environment': environment,
        'shortcode': mpesa.shortcode,
        'timestamp': time.time()
    })

# USSD Push Flow Endpoints

@app.route('/api/ussd/initiate', methods=['POST'])
def ussd_initiate():
    """Initiate USSD push flow - send M-Pesa popup to enter phone number"""
    try:
        # Generate USSD session ID first (no phone number yet)
        ussd_session_id = str(uuid.uuid4())
        
        # Store USSD session with waiting for phone number status
        ussd_sessions[ussd_session_id] = {
            'status': 'awaiting_phone_number',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=5)
        }
        
        # Create M-Pesa notification popup
        notification = {
            'id': str(uuid.uuid4()),
            'type': 'phone_number_request',
            'title': 'M-Pesa',
            'message': 'Please enter your phone number to continue',
            'ussd_session_id': ussd_session_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        mpesa_notifications.append(notification)
        
        print(f"📱 M-Pesa Popup: 'Please enter your phone number'")
        print(f"🔗 Session ID: {ussd_session_id}")
        
        return jsonify({
            'success': True,
            'ussd_session_id': ussd_session_id,
            'message': 'M-Pesa popup initiated - requesting phone number',
            'mpesa_notification': {
                'title': 'M-Pesa',
                'message': 'Please enter your phone number to continue',
                'type': 'phone_number_request'
            },
            'next_step': 'User will enter phone number via M-Pesa popup',
            'environment': environment,
            'warning': '🔴 SANDBOX MODE - Simulated M-Pesa popup'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/ussd/enter-phone', methods=['POST'])
def ussd_enter_phone():
    """User enters phone number via USSD"""
    try:
        data = request.json
        ussd_session_id = data.get('ussd_session_id')
        phone_number = data.get('phone_number')
        
        if not ussd_session_id or ussd_session_id not in ussd_sessions:
            return jsonify({
                'success': False,
                'message': 'Invalid USSD session'
            }), 400
        
        if not phone_number:
            return jsonify({
                'success': False,
                'message': 'Phone number is required'
            }), 400
        
        session = ussd_sessions[ussd_session_id]
        
        # Check if session is still valid
        if datetime.now() > session['expires_at']:
            return jsonify({
                'success': False,
                'message': 'USSD session expired'
            }), 400
        
        # Validate phone number format (Lesotho format)
        cleaned_phone = phone_number.replace(' ', '').replace('-', '')
        if not (cleaned_phone.startswith('+266') or cleaned_phone.startswith('0') or len(cleaned_phone) == 8):
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format. Use +266XXXXXXX, 05XXXXXXX, or 5XXXXXXX'
            }), 400
        
        # Update session with phone number
        session['phone_number'] = cleaned_phone
        session['status'] = 'phone_entered'
        
        print(f"📱 User entered phone number: {cleaned_phone}")
        print(f"🔗 Session ID: {ussd_session_id}")
        
        return jsonify({
            'success': True,
            'ussd_session_id': ussd_session_id,
            'message': 'Phone number received successfully',
            'phone_number': cleaned_phone,
            'next_step': 'Send PIN request SMS',
            'environment': environment
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/ussd/send-pin-sms', methods=['POST'])
def send_pin_sms():
    """Send M-Pesa popup requesting PIN"""
    try:
        data = request.json
        ussd_session_id = data.get('ussd_session_id')
        
        if not ussd_session_id or ussd_session_id not in ussd_sessions:
            return jsonify({
                'success': False,
                'message': 'Invalid USSD session'
            }), 400
        
        session = ussd_sessions[ussd_session_id]
        
        # Check if session is still valid
        if datetime.now() > session['expires_at']:
            return jsonify({
                'success': False,
                'message': 'USSD session expired'
            }), 400
        
        # Generate PIN for demo (in production, this would be user's existing PIN)
        pin = str(random.randint(1000, 9999))
        
        # Store PIN session
        pin_session_id = str(uuid.uuid4())
        pin_sessions[pin_session_id] = {
            'ussd_session_id': ussd_session_id,
            'phone_number': session['phone_number'],
            'generated_pin': pin,
            'status': 'pin_sent',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=3),
            'attempts': 0,
            'max_attempts': 3
        }
        
        # Create M-Pesa notification popup for PIN
        notification = {
            'id': str(uuid.uuid4()),
            'type': 'pin_request',
            'title': 'M-Pesa',
            'message': f'Enter your M-Pesa PIN to continue',
            'phone_number': session['phone_number'],
            'pin_session_id': pin_session_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'expires_at': (datetime.now() + timedelta(minutes=3)).isoformat()
        }
        mpesa_notifications.append(notification)
        
        print(f"� M-Pesa Popup: 'Enter your M-Pesa PIN to continue'")
        print(f"🔢 Generated PIN: {pin}")
        print(f"📱 Phone: {session['phone_number']}")
        print(f"🆔 PIN Session ID: {pin_session_id}")
        
        return jsonify({
            'success': True,
            'pin_session_id': pin_session_id,
            'message': 'M-Pesa PIN popup sent successfully',
            'phone_number': session['phone_number'],
            'expires_in': '3 minutes',
            'next_step': 'Enter PIN via M-Pesa popup',
            'mpesa_notification': {
                'title': 'M-Pesa',
                'message': 'Enter your M-Pesa PIN to continue',
                'type': 'pin_request',
                'expires_in': '3 minutes'
            },
            'environment': environment,
            'warning': '🔴 SANDBOX MODE - Check console for PIN (simulated popup)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/ussd/verify-pin', methods=['POST'])
def verify_pin():
    """Verify entered PIN"""
    try:
        data = request.json
        pin_session_id = data.get('pin_session_id')
        entered_pin = data.get('pin')
        
        if not pin_session_id or pin_session_id not in pin_sessions:
            return jsonify({
                'success': False,
                'message': 'Invalid PIN session'
            }), 400
        
        if not entered_pin:
            return jsonify({
                'success': False,
                'message': 'PIN is required'
            }), 400
        
        pin_session = pin_sessions[pin_session_id]
        
        # Check if session is still valid
        if datetime.now() > pin_session['expires_at']:
            return jsonify({
                'success': False,
                'message': 'PIN session expired'
            }), 400
        
        # Check attempts
        if pin_session['attempts'] >= pin_session['max_attempts']:
            return jsonify({
                'success': False,
                'message': 'Maximum PIN attempts exceeded'
            }), 400
        
        # Increment attempts
        pin_session['attempts'] += 1
        
        # Verify PIN
        if entered_pin == pin_session['generated_pin']:
            # PIN correct - update status
            pin_session['status'] = 'pin_verified'
            pin_session['verified_at'] = datetime.now()
            
            print(f"✅ PIN verified successfully for {pin_session['phone_number']}")
            
            return jsonify({
                'success': True,
                'message': 'PIN verified successfully',
                'status': 'pin_verified',
                'next_step': 'Confirm transaction',
                'attempts_remaining': pin_session['max_attempts'] - pin_session['attempts']
            })
        else:
            # PIN incorrect
            attempts_remaining = pin_session['max_attempts'] - pin_session['attempts']
            
            print(f"❌ Incorrect PIN attempt {pin_session['attempts']} for {pin_session['phone_number']}")
            
            if attempts_remaining == 0:
                pin_session['status'] = 'failed'
                return jsonify({
                    'success': False,
                    'message': 'Maximum PIN attempts exceeded. Session terminated.',
                    'attempts_remaining': 0
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': f'Incorrect PIN. {attempts_remaining} attempts remaining.',
                    'attempts_remaining': attempts_remaining
                }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/ussd/confirm-transaction', methods=['POST'])
def confirm_transaction():
    """Send B2B payment request to M-Pesa"""
    try:
        data = request.json
        pin_session_id = data.get('pin_session_id')
        amount = data.get('amount', 50.00)  # Default 50 LSL for certificate verification
        reference = data.get('reference', 'VERIFY-CERT-001')
        
        if not pin_session_id or pin_session_id not in pin_sessions:
            return jsonify({
                'success': False,
                'message': 'Invalid PIN session'
            }), 400
        
        pin_session = pin_sessions[pin_session_id]
        
        # Check if PIN was verified
        if pin_session['status'] != 'pin_verified':
            return jsonify({
                'success': False,
                'message': 'PIN not verified. Please verify PIN first.'
            }), 400
        
        # Get current session
        if 'current' not in sessions:
            # Generate new session
            session_id = mpesa.generate_session()
            if not session_id:
                return jsonify({
                    'success': False,
                    'message': 'Could not generate M-Pesa session'
                }), 500
            sessions['current'] = {
                'id': session_id,
                'created_at': time.time()
            }
        else:
            session_id = sessions['current']['id']
        
        # Generate unique conversation ID
        conversation_id = str(uuid.uuid4()).replace('-', '')[:20]
        transaction_reference = f"VERIFY-CERT-{int(time.time())}"
        
        # B2B Payment Request Payload
        b2b_payload = {
            "input_Amount": str(int(amount * 100)),  # Convert to cents
            "input_Country": "LES",
            "input_Currency": "LSL",
            "input_PrimaryPartyCode": "UNI001",      # University pays
            "input_SecondaryPartyCode": "110799",    # ECOL receives (your shortcode)
            "input_ThirdPartyConversationID": conversation_id,
            "input_TransactionReference": transaction_reference,
            "input_ServiceProviderCode": "110799"
        }
        
        # Create M-Pesa notification for B2B payment
        notification = {
            'id': str(uuid.uuid4()),
            'type': 'b2b_payment_request',
            'title': 'M-Pesa',
            'message': f'Processing payment of M{amount:.2f} from University to ECOL...',
            'pin_session_id': pin_session_id,
            'conversation_id': conversation_id,
            'transaction_reference': transaction_reference,
            'amount': amount,
            'reference': reference,
            'phone_number': pin_session['phone_number'],
            'created_at': datetime.now().isoformat(),
            'status': 'processing'
        }
        mpesa_notifications.append(notification)
        
        print(f"💰 B2B Payment Request:")
        print(f"   Amount: M{amount:.2f} ({int(amount * 100)} cents)")
        print(f"   From: UNI001 (University)")
        print(f"   To: 110799 (ECOL)")
        print(f"   Reference: {transaction_reference}")
        print(f"   Conversation ID: {conversation_id}")
        
        # In production, this would call the actual M-Pesa B2B endpoint
        # For now, simulate the B2B payment processing
        mpesa_session_id = sessions['current']['id']
        
        # Simulate B2B payment processing
        result = {
            'body': {
                'output_ResponseCode': 'INS-0',  # SUCCESS
                'output_ResponseDesc': 'Request processed successfully',
                'output_TransactionID': f'TXN{int(time.time())}',
                'output_ConversationID': f'conv-{conversation_id[:8]}',
                'output_ThirdPartyConversationID': conversation_id
            }
        }
        
        # Update session
        pin_session['status'] = 'payment_processed'
        pin_session['transaction_id'] = result['body']['output_TransactionID']
        pin_session['conversation_id'] = conversation_id
        pin_session['amount'] = amount
        pin_session['reference'] = reference
        pin_session['b2b_result'] = result
        
        # Create success notification
        success_notification = {
            'id': str(uuid.uuid4()),
            'type': 'b2b_payment_success',
            'title': 'M-Pesa',
            'message': f'Payment of M{amount:.2f} processed successfully! Transaction ID: {result["body"]["output_TransactionID"]}',
            'pin_session_id': pin_session_id,
            'transaction_id': result['body']['output_TransactionID'],
            'conversation_id': conversation_id,
            'amount': amount,
            'phone_number': pin_session['phone_number'],
            'created_at': datetime.now().isoformat(),
            'status': 'completed'
        }
        mpesa_notifications.append(success_notification)
        
        print(f"✅ B2B Payment SUCCESS!")
        print(f"   Transaction ID: {result['body']['output_TransactionID']}")
        print(f"   Response Code: {result['body']['output_ResponseCode']}")
        print(f"   Description: {result['body']['output_ResponseDesc']}")
        
        return jsonify({
            'success': True,
            'message': 'B2B payment processed successfully',
            'transaction_id': result['body']['output_TransactionID'],
            'conversation_id': conversation_id,
            'transaction_reference': transaction_reference,
            'amount': amount,
            'response_code': result['body']['output_ResponseCode'],
            'response_description': result['body']['output_ResponseDesc'],
            'b2b_payload': b2b_payload,
            'mpesa_notification': {
                'title': 'M-Pesa',
                'message': f'Payment of M{amount:.2f} processed successfully!',
                'type': 'b2b_payment_success',
                'transaction_id': result['body']['output_TransactionID']
            },
            'environment': environment,
            'warning': '🔴 SANDBOX MODE - Simulated B2B payment (no real money)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/ussd/finalize-transaction', methods=['POST'])
def finalize_transaction():
    """Finalize B2B transaction and send confirmations"""
    try:
        data = request.json
        pin_session_id = data.get('pin_session_id')
        
        if not pin_session_id or pin_session_id not in pin_sessions:
            return jsonify({
                'success': False,
                'message': 'Invalid PIN session'
            }), 400
        
        pin_session = pin_sessions[pin_session_id]
        
        # Check if payment was processed
        if pin_session['status'] != 'payment_processed':
            return jsonify({
                'success': False,
                'message': 'No payment processed yet'
            }), 400
        
        # Get B2B result from session
        b2b_result = pin_session.get('b2b_result', {})
        transaction_id = pin_session.get('transaction_id')
        amount = pin_session.get('amount', 0)
        conversation_id = pin_session.get('conversation_id')
        
        # Create SMS confirmations for both parties
        university_sms = {
            'id': str(uuid.uuid4()),
            'type': 'sms_confirmation',
            'recipient': 'UNI001 (University)',
            'message': f'You have paid M{amount:.2f} to ECOL. Ref: {pin_session.get("reference", "VERIFY-CERT")}. New balance: 9,950.00 LSL',
            'transaction_id': transaction_id,
            'created_at': datetime.now().isoformat()
        }
        
        ecol_sms = {
            'id': str(uuid.uuid4()),
            'type': 'sms_confirmation',
            'recipient': '110799 (ECOL)',
            'message': f'You have received M{amount:.2f} from University. Ref: {pin_session.get("reference", "VERIFY-CERT")}. New balance: 5,050.00 LSL',
            'transaction_id': transaction_id,
            'created_at': datetime.now().isoformat()
        }
        
        # Add to notifications log
        mpesa_notifications.append(university_sms)
        mpesa_notifications.append(ecol_sms)
        
        # Simulate callback to your system
        callback_payload = {
            'output_TransactionID': transaction_id,
            'output_ResponseCode': b2b_result.get('body', {}).get('output_ResponseCode', 'INS-0'),
            'output_TransactionReference': pin_session.get('reference', 'VERIFY-CERT-001'),
            'output_ThirdPartyConversationID': conversation_id,
            'amount': str(int(amount * 100)),
            'payer': 'UNI001',
            'payee': '110799'
        }
        
        print(f"📩 SMS Confirmations Sent:")
        print(f"   To University: {university_sms['message']}")
        print(f"   To ECOL: {ecol_sms['message']}")
        print(f"🔄 Callback Payload: {callback_payload}")
        
        # Update session status
        pin_session['status'] = 'completed'
        pin_session['completed_at'] = datetime.now()
        pin_session['sms_confirmations'] = [university_sms, ecol_sms]
        pin_session['callback_payload'] = callback_payload
        
        # Create final notification
        final_notification = {
            'id': str(uuid.uuid4()),
            'type': 'transaction_complete',
            'title': 'M-Pesa',
            'message': f'Certificate verification payment completed! Transaction ID: {transaction_id}',
            'transaction_id': transaction_id,
            'amount': amount,
            'status': 'completed',
            'created_at': datetime.now().isoformat()
        }
        mpesa_notifications.append(final_notification)
        
        return jsonify({
            'success': True,
            'message': 'B2B transaction completed successfully',
            'transaction_id': transaction_id,
            'conversation_id': conversation_id,
            'amount': amount,
            'status': 'completed',
            'completed_at': pin_session['completed_at'].isoformat(),
            'sms_confirmations': {
                'university': university_sms['message'],
                'ecol': ecol_sms['message']
            },
            'callback_payload': callback_payload,
            'b2b_result': b2b_result,
            'mpesa_notification': {
                'title': 'M-Pesa',
                'message': f'Certificate verification payment completed!',
                'type': 'transaction_complete',
                'transaction_id': transaction_id
            },
            'environment': environment,
            'warning': '🔴 SANDBOX MODE - Simulated B2B completion (no real money)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/ussd/status/<session_id>', methods=['GET'])
def get_ussd_status(session_id):
    """Get USSD session status"""
    try:
        # Check USSD session
        if session_id in ussd_sessions:
            return jsonify({
                'session_type': 'ussd',
                'session_id': session_id,
                'status': ussd_sessions[session_id]['status'],
                'phone_number': ussd_sessions[session_id]['phone_number'],
                'created_at': ussd_sessions[session_id]['created_at'].isoformat(),
                'expires_at': ussd_sessions[session_id]['expires_at'].isoformat()
            })
        
        # Check PIN session
        if session_id in pin_sessions:
            pin_session = pin_sessions[session_id]
            response = {
                'session_type': 'pin',
                'session_id': session_id,
                'status': pin_session['status'],
                'phone_number': pin_session['phone_number'],
                'created_at': pin_session['created_at'].isoformat(),
                'expires_at': pin_session['expires_at'].isoformat(),
                'attempts': pin_session['attempts'],
                'max_attempts': pin_session['max_attempts']
            }
            
            # Add transaction details if available
            if 'transaction_id' in pin_session:
                response.update({
                    'transaction_id': pin_session['transaction_id'],
                    'amount': pin_session.get('amount'),
                    'reference': pin_session.get('reference')
                })
            
            return jsonify(response)
        
        return jsonify({
            'error': 'Session not found'
        }), 404
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/mpesa/notifications', methods=['GET'])
def get_mpesa_notifications():
    """Get M-Pesa notifications (for debugging)"""
    try:
        return jsonify({
            'success': True,
            'notifications': mpesa_notifications[-20:],  # Return last 20 notifications
            'total_notifications': len(mpesa_notifications),
            'environment': environment
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/ussd_test.html')
def serve_test_page():
    """Serve the USSD test HTML page"""
    return send_from_directory('.', 'ussd_test.html')

@app.route('/')
def home():
    """Home page with test link"""
    return '''
    <h1>🚀 M-Pesa B2B Payment System</h1>
    <p><strong>Environment:</strong> Sandbox (No real money)</p>
    <p><a href="/ussd_test.html">📱 Test M-Pesa USSD Flow</a></p>
    <h2>🔗 Available API Endpoints:</h2>
    <ul>
        <li><code>POST /api/ussd/initiate</code> - Start USSD flow</li>
        <li><code>POST /api/ussd/enter-phone</code> - Enter phone number</li>
        <li><code>POST /api/ussd/send-pin-sms</code> - Send PIN request</li>
        <li><code>POST /api/ussd/verify-pin</code> - Verify PIN</li>
        <li><code>POST /api/ussd/confirm-transaction</code> - Process B2B payment</li>
        <li><code>POST /api/ussd/finalize-transaction</code> - Complete transaction</li>
        <li><code>GET /api/mpesa/notifications</code> - View notifications</li>
    </ul>
    '''

if __name__ == '__main__':
    print(f"🚀 Starting M-Pesa Backend ({environment} mode)...")
    print(f"💳 Shortcode: {mpesa.shortcode}")
    print(f"🌐 Market: {mpesa.market}")
    print(f"🔗 Base URL: {mpesa.base_url}")
    app.run(debug=True, port=5000)

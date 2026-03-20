#!/usr/bin/env python3
"""
Simple M-Pesa Demo Backend for LGCSE System
Provides working M-Pesa API endpoints without database dependencies
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import uuid
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# In-memory storage for demo
payments = {}
mpesa_config = {
    "consumer_key": "demo_consumer_key",
    "environment": "sandbox",
    "shortcode": "123456",
    "status": "configured",
    "demo_mode": True
}

@app.route('/api/mpesa/config', methods=['GET'])
def get_mpesa_config():
    """Get M-Pesa configuration status"""
    return jsonify({
        "success": True,
        "config": mpesa_config,
        "endpoints": {
            "stk_push": "/api/mpesa/stk-push",
            "b2b_payment": "/api/mpesa/b2b-payment",
            "status_check": "/api/mpesa/status/{payment_id}",
            "callback": "/api/mpesa/callback"
        },
        "status": "ready for demo"
    })

@app.route('/api/mpesa/stk-push', methods=['POST'])
def initiate_stk_push():
    """Initiate M-Pesa STK Push payment (Demo)"""
    try:
        data = request.get_json()
        
        phone_number = data.get('phone_number')
        amount = data.get('amount', 5.00)
        verification_request_id = data.get('verification_request_id')
        account_reference = data.get('account_reference', 'TEST')
        
        # Validate phone number
        if not phone_number or len(phone_number) < 10:
            return jsonify({
                "success": False,
                "error": "Invalid phone number format"
            }), 400
        
        # Validate amount
        if amount <= 0:
            return jsonify({
                "success": False,
                "error": "Amount must be greater than 0"
            }), 400
        
        # Generate payment record
        payment_id = str(uuid.uuid4())
        merchant_request_id = f"wsco_{int(datetime.now().timestamp())}"
        checkout_request_id = f"ws_CO_{int(datetime.now().timestamp())}"
        
        # Store payment
        payments[payment_id] = {
            "payment_id": payment_id,
            "merchant_request_id": merchant_request_id,
            "checkout_request_id": checkout_request_id,
            "phone_number": phone_number,
            "amount": amount,
            "verification_request_id": verification_request_id,
            "account_reference": account_reference,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "customer_message": "Success. Request accepted for processing. Please check your phone for M-Pesa STK push prompt.",
            "demo_mode": True
        }
        
        return jsonify({
            "success": True,
            "payment_id": payment_id,
            "merchant_request_id": merchant_request_id,
            "checkout_request_id": checkout_request_id,
            "customer_message": "Success. Request accepted for processing. Please check your phone for M-Pesa STK push prompt.",
            "status": "pending",
            "next_step": "Please check your phone for M-Pesa STK push prompt",
            "amount": amount,
            "phone_number": phone_number
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Payment initiation failed: {str(e)}"
        }), 500

@app.route('/api/mpesa/b2b-payment', methods=['POST'])
def initiate_b2b_payment():
    """Initiate M-Pesa B2B payment (Demo)"""
    try:
        data = request.get_json()
        
        university_code = data.get('university_code')
        amount = data.get('amount', '500')  # M5.00 in cents
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
                "error": "Amount below minimum (M5.00)"
            }), 400
        
        # Generate transaction
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        transaction_id = f"VERIFY{certificate_reference[-8:]}{timestamp[-6:]}"
        conversation_id = f"CONV{timestamp}"
        
        # Simulate successful payment
        result = {
            "success": True,
            "output_ResponseCode": "INS-0",
            "output_ResponseDesc": "The service request is processed successfully.",
            "output_TransactionID": transaction_id,
            "output_ConversationID": conversation_id,
            "_metadata": {
                "timestamp": timestamp,
                "amount_maloti": float(amount) / 100,
                "currency": "LSL",
                "certificate": certificate_reference,
                "university": university_code,
                "demo_mode": True
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"B2B payment failed: {str(e)}"
        }), 500

@app.route('/api/mpesa/status/<payment_id>', methods=['GET'])
def check_payment_status(payment_id):
    """Check payment status"""
    try:
        if payment_id not in payments:
            return jsonify({
                "success": False,
                "error": "Payment not found"
            }), 404
        
        payment = payments[payment_id]
        
        # Simulate payment confirmation after some time
        if payment['status'] == 'pending':
            created_time = datetime.fromisoformat(payment['created_at'])
            if datetime.now() - created_time > timedelta(seconds=10):
                # Auto-confirm for demo
                payment['status'] = 'confirmed'
                payment['confirmed_at'] = datetime.now().isoformat()
                payment['mpesa_transaction_id'] = f"LHR{int(datetime.now().timestamp())}"
                payment['mpesa_receipt_number'] = f"MP{payment_id[:8]}"
        
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
def handle_mpesa_callback():
    """Handle M-Pesa payment callback"""
    try:
        data = request.get_json()
        
        # Log callback for demo
        print(f"M-Pesa Callback: {json.dumps(data, indent=2)}")
        
        # Extract payment info
        merchant_request_id = data.get('MerchantRequestID')
        checkout_request_id = data.get('CheckoutRequestID')
        result_code = data.get('ResultCode')
        
        # Find and update payment
        for payment_id, payment in payments.items():
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
                    payment['error'] = data.get('ResultDesc', 'Payment failed')
                
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
def list_payments():
    """List all payments (Demo)"""
    try:
        return jsonify({
            "success": True,
            "payments": list(payments.values()),
            "total": len(payments),
            "demo_mode": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to list payments: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "M-Pesa Demo Backend",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": {
            "stk_push": True,
            "b2b_payment": True,
            "status_check": True,
            "callback_handling": True,
            "demo_mode": True
        }
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "LGCSE M-Pesa Demo Backend",
        "version": "1.0.0",
        "status": "running",
        "demo_mode": True,
        "endpoints": {
            "config": "/api/mpesa/config",
            "stk_push": "/api/mpesa/stk-push",
            "b2b_payment": "/api/mpesa/b2b-payment",
            "status": "/api/mpesa/status/{payment_id}",
            "callback": "/api/mpesa/callback",
            "payments": "/api/mpesa/payments",
            "health": "/api/health"
        }
    })

if __name__ == '__main__':
    print("🚀 Starting M-Pesa Demo Backend...")
    print("💳 M-Pesa Demo API running on http://localhost:5000")
    print("📱 Demo mode enabled - no real payments")
    print("🔗 Available endpoints:")
    print("   GET  /api/mpesa/config")
    print("   POST /api/mpesa/stk-push")
    print("   POST /api/mpesa/b2b-payment")
    print("   GET  /api/mpesa/status/{payment_id}")
    print("   POST /api/mpesa/callback")
    print("   GET  /api/mpesa/payments")
    print("   GET  /api/health")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

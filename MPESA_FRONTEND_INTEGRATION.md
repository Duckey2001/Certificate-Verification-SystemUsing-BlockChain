# M-Pesa Frontend Integration Guide

## Overview
The enhanced M-Pesa backend now supports multiple payment flows through a single unified API. This guide shows how to integrate frontend applications.

## Base URL
```
http://localhost:5000
```

## Payment Flows

### 1. USSD Popup Flow (Recommended for Web)
Perfect for the existing popup interface with step-by-step flow.

#### Step 1: Initiate Session
```javascript
const response = await fetch('/api/ussd/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        certificate_ref: 'CERT-2024-001',
        university_name: 'National University of Lesotho',
        amount: 5000  // Amount in cents (M50.00)
    })
});
const { ussd_session_id } = await response.json();
```

#### Step 2: Submit Phone Number
```javascript
const response = await fetch('/api/ussd/enter-phone', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        ussd_session_id: ussd_session_id,
        phone_number: '26657620256'
    })
});
```

#### Step 3: Send PIN (Automatic)
```javascript
const response = await fetch('/api/ussd/send-pin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        ussd_session_id: ussd_session_id
    })
});
// SMS with PIN is sent automatically
```

#### Step 4: Verify PIN
```javascript
const response = await fetch('/api/ussd/verify-pin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        ussd_session_id: ussd_session_id,
        pin: '1234'  // PIN from user input
    })
});
const { payment_id } = await response.json();
```

#### Step 5: Process Payment
```javascript
const response = await fetch('/api/ussd/process-payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        payment_id: payment_id
    })
});
const { transaction_id, amount } = await response.json();
```

### 2. Legacy SMS Flow (For Existing Integrations)
Maintains compatibility with existing SMS-based implementations.

#### Initiate Payment
```javascript
const response = await fetch('/api/payment/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        phone_number: '26657620256',
        certificate_ref: 'CERT-2024-001',
        university_name: 'National University of Lesotho',
        amount: 5000,
        university_code: 'UNI001'
    })
});
const { transaction_id } = await response.json();
```

#### Check Status
```javascript
const response = await fetch(`/api/payment/status/${transaction_id}`);
const status = await response.json();
```

### 3. Real M-Pesa B2B Flow (Direct Integration)
For direct M-Pesa B2B payments without SMS verification.

```javascript
const response = await fetch('/api/mpesa/b2b-payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        university_code: 'UNI001',
        amount: '1000',  // Amount in cents
        certificate_reference: 'CERT-2024-001',
        description: 'Certificate verification payment'
    })
});
const { success, transaction_id } = await response.json();
```

### 4. STK Push Flow (Mobile Payments)
For direct STK push to user's phone.

```javascript
const response = await fetch('/api/mpesa/stk-push', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        phone_number: '26657620256',
        amount: 25.00,  // Amount in LSL
        verification_request_id: 'VERIFY-001',
        account_reference: 'LGCSE_VERIFY'
    })
});
const { payment_id, merchant_request_id } = await response.json();
```

## Monitoring Endpoints

### Check System Health
```javascript
const response = await fetch('/api/health');
const { status, real_mpesa_available } = await response.json();
```

### View Configuration
```javascript
const response = await fetch('/api/mpesa/config');
const config = await response.json();
```

### View All Transactions
```javascript
const response = await fetch('/api/transactions');
const { pending, payments, completed } = await response.json();
```

### View SMS Logs
```javascript
const response = await fetch('/api/sms/sent');
const { total, messages } = await response.json();
```

## Error Handling

All endpoints return consistent error responses:

```javascript
try {
    const response = await fetch('/api/ussd/initiate', { /* ... */ });
    const data = await response.json();
    
    if (!response.ok || data.status === 'error') {
        throw new Error(data.error || 'Request failed');
    }
    
    // Process success response
} catch (error) {
    console.error('M-Pesa error:', error.message);
    // Show user-friendly error message
}
```

## Response Formats

### Success Response
```json
{
    "status": "success",
    "ussd_session_id": "uuid-string",
    "message": "Session created successfully"
}
```

### Error Response
```json
{
    "status": "error",
    "error": "Invalid phone number format"
}
```

## Integration Example (React Component)

```javascript
import React, { useState } from 'react';

function MpesaPayment({ certificateRef, universityName, amount }) {
    const [step, setStep] = useState(1);
    const [sessionId, setSessionId] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [pin, setPin] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const initiateSession = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch('/api/ussd/initiate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    certificate_ref: certificateRef,
                    university_name: universityName,
                    amount: amount * 100  // Convert to cents
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                setSessionId(data.ussd_session_id);
                setStep(2);
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const submitPhone = async () => {
        // Similar implementation for phone submission
        // ... follow the API pattern above
    };

    const verifyPin = async () => {
        // Similar implementation for PIN verification
        // ... follow the API pattern above
    };

    const processPayment = async () => {
        // Similar implementation for payment processing
        // ... follow the API pattern above
    };

    return (
        <div>
            {step === 1 && (
                <div>
                    <h3>Certificate Verification Payment</h3>
                    <p>Amount: M{amount}</p>
                    <button onClick={initiateSession} disabled={loading}>
                        {loading ? 'Processing...' : 'Start Payment'}
                    </button>
                </div>
            )}
            
            {step === 2 && (
                <div>
                    <h3>Enter Phone Number</h3>
                    <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="26657620256"
                    />
                    <button onClick={submitPhone}>Send PIN</button>
                </div>
            )}
            
            {/* Continue with other steps... */}
            
            {error && <div className="error">{error}</div>}
        </div>
    );
}
```

## Testing

Use the comprehensive test script to validate the integration:

```bash
python test_mpesa_complete.py
```

## Production Configuration

For production, update the `.env` file with real M-Pesa credentials:

```bash
# Copy the template
cp .env.mpesa .env

# Edit with real values
nano .env
```

Key production settings:
- `MPESA_ENVIRONMENT=production`
- `SMS_PROVIDER=africastalking` (or your preferred provider)
- `FLASK_DEBUG=false`
- `CORS_ORIGINS=https://yourdomain.com`

## Security Considerations

1. **Never expose API keys** in frontend code
2. **Use HTTPS** in production
3. **Validate phone numbers** on both client and server
4. **Implement rate limiting** for payment endpoints
5. **Log all transactions** for audit purposes
6. **Use webhook signatures** for callbacks if applicable

## Support

For issues or questions:
1. Check the server logs for detailed error messages
2. Run the test script to identify problems
3. Verify environment configuration
4. Test with simulated mode before production

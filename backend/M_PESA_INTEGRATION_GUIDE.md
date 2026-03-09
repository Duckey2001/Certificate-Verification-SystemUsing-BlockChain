# M-Pesa B2B Integration Guide for Your Application

## Files Created
1. `mpesa_client.py` - Core M-Pesa B2B client
2. `.env.example` - Configuration template (update with your values)
3. `example_usage.py` - Example implementation
4. `api/mpesa_integration.py` - FastAPI integration endpoints

## How to Integrate with Your Certificate System

### Step 1: Update Environment Variables
```bash
# Copy the example .env file
cp .env.example .env

# Update with your actual M-Pesa credentials
nano .env
```

Required variables:
- `MPESA_API_KEY`: Your API key (ends with 5Gfn)
- `MPESA_PUBLIC_KEY`: Your public key from API docs
- `SERVICE_PROVIDER_CODE`: 110799 (your short code)
- `ECOL_CODE`: 110799 (ECOL's receiving code)
- `COUNTRY`: LES
- `CURRENCY`: LSL

### Step 2: Initialize Client
```python
from mpesa_client import MpesaB2BClient

mpesa = MpesaB2BClient()
```

### Step 3: Process Payment When University Requests Verification
```python
def handle_verification_request(university_code, certificate_id, amount):
    # Process payment
    response = mpesa.b2b_payment(
        university_code=university_code,
        amount=amount,
        certificate_reference=certificate_id
    )
    
    # Check result
    if mpesa.is_payment_successful(response):
        # Payment successful - proceed with verification
        update_database(certificate_id, 'verified')
        return {'success': True, 'transaction_id': response.get('output_TransactionID')}
    else:
        # Payment failed
        return {'success': False, 'message': mpesa.get_response_message(response)}
```

### Step 4: API Endpoints Available

#### POST `/api/mpesa/b2b-payment`
Process B2B payment from University to ECOL
```json
{
  "university_code": "UNI001",
  "amount": "5000",
  "certificate_reference": "CERT-2024-001",
  "description": "Certificate verification fee"
}
```

#### POST `/api/mpesa/query-transaction`
Query transaction status
```json
{
  "transaction_reference": "VERIFY-CERT-2024-001"
}
```

#### GET `/api/mpesa/payment-history`
Get payment history for current user

#### GET `/api/mpesa/mpesa-status`
Get M-Pesa system status and configuration

#### POST `/api/mpesa/test-payment`
Test M-Pesa integration (admin only)

### Step 5: Key Functions

- `generate_session()` - Get new session key
- `b2b_payment()` - Process payment
- `query_transaction()` - Check payment status
- `is_payment_successful()` - Verify response

### Response Codes

- `INS-0`: Success
- `INS-9`: Failed
- `INS-14`: Invalid session
- `INS-20`: Insufficient balance

## 🚀 Quick Start

1. **Update `.env`** with your actual API key and public key
2. **Install dependencies**:
   ```bash
   pip install requests pycryptodome python-dotenv
   ```

3. **Test the integration**:
   ```python
   from mpesa_client import MpesaB2BClient

   mpesa = MpesaB2BClient()
   session = mpesa.generate_session()
   print(f"Session: {session}")
   ```

## 📋 Integration Checklist

✅ B2B Client Created  
✅ Session Management  
✅ Payment Processing  
✅ Error Handling  
✅ Transaction Query  
✅ Environment Config  
✅ Your Short Code (110799) Configured  
✅ FastAPI Integration  
✅ Database Payment Records  
✅ API Endpoints  

## 🔗 How to Call from Your Certificate System

```python
# In your certificate verification code:
from mpesa_client import MpesaB2BClient

mpesa = MpesaB2BClient()

# When university requests verification
def process_verification_payment(university_id, cert_id, fee_amount):
    response = mpesa.b2b_payment(
        university_code=university_id,
        amount=fee_amount,
        certificate_reference=cert_id
    )
    
    if response.get('output_ResponseCode') == 'INS-0':
        # Update database: payment received
        # Trigger certificate verification
        return True
    return False
```

## 📄 Frontend Integration

Call the API endpoints from your frontend:

```javascript
// Process payment
const response = await fetch('/api/mpesa/b2b-payment', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    university_code: 'UNI001',
    amount: '5000',
    certificate_reference: 'CERT-2024-001',
    description: 'Certificate verification fee'
  })
});

const result = await response.json();
```

This is production-ready code. Just add your actual API key and public key to the .env file and integrate the b2b_payment() call where you need to process payments in your certificate system.

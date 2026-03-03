"""
M-Pesa Payment Integration for CertiVert LGCSE (Lesotho)
"""

import os
import requests
import json
import base64
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Payment, User, VerificationRequest

router = APIRouter(prefix="/api/mpesa", tags=["mpesa"])

# M-Pesa Lesotho Configuration (Vodacom Lesotho)
MPESA_CONSUMER_KEY = os.getenv("MPESA_LESOTHO_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_LESOTHO_CONSUMER_SECRET", "")
MPESA_PASSKEY = os.getenv("MPESA_LESOTHO_PASSKEY", "")
MPESA_SHORTCODE = os.getenv("MPESA_LESOTHO_SHORTCODE", "")  # Vodacom Lesotho shortcode
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL", "https://your-domain.com/api/mpesa/callback")
MPESA_ENVIRONMENT = os.getenv("MPESA_ENVIRONMENT", "sandbox")  # sandbox or production

# M-Pesa API URLs for Lesotho (Vodacom Lesotho uses Safaricom's API)
MPESA_BASE_URL = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke"
}

# Currency for Lesotho
CURRENCY = "LSL"  # Lesotho Loti (Maloti)

class MpesaSTKRequest(BaseModel):
    phone_number: str
    amount: float = Field(5.0, ge=1.0, description="Amount in Maloti (M)")
    verification_request_id: Optional[int] = None
    account_reference: str = "CertiVert-LS"
    transaction_desc: str = "Certificate Verification Fee (Lesotho)"

    @validator('phone_number')
    def validate_lesotho_phone(cls, v):
        """Validate Lesotho phone number format"""
        # Remove any whitespace and common separators
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Lesotho phone numbers:
        # - Start with +266 (country code) or 0
        # - Followed by 8 digits (mobile numbers start with 5, 6)
        
        if cleaned.startswith('+266'):
            if len(cleaned) != 13:  # +266 + 8 digits = 13 characters
                raise ValueError('Invalid Lesotho phone number length. Expected format: +2665XXXXXXX')
            number_part = cleaned[4:]
            if not (number_part.startswith('5') or number_part.startswith('6')):
                raise ValueError('Lesotho mobile numbers must start with 5 or 6')
        elif cleaned.startswith('0'):
            if len(cleaned) != 9:  # 0 + 8 digits = 9 characters
                raise ValueError('Invalid Lesotho phone number length. Expected format: 05XXXXXXX')
            if not (cleaned[1] == '5' or cleaned[1] == '6'):
                raise ValueError('Lesotho mobile numbers must start with 5 or 6')
        elif len(cleaned) == 8:
            if not (cleaned.startswith('5') or cleaned.startswith('6')):
                raise ValueError('Lesotho mobile numbers must start with 5 or 6')
        else:
            raise ValueError('Invalid Lesotho phone number format. Use: +2665XXXXXXX, 05XXXXXXX, or 5XXXXXXX')
        
        return v

class MpesaCallbackData(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[Dict[str, Any]] = None

class MpesaService:
    def __init__(self):
        self.base_url = MPESA_BASE_URL.get(MPESA_ENVIRONMENT, MPESA_BASE_URL["sandbox"])
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self) -> str:
        """Get M-Pesa OAuth access token"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
            raise HTTPException(
                status_code=500, 
                detail="M-Pesa credentials not configured. Please set MPESA_LESOTHO_CONSUMER_KEY and MPESA_LESOTHO_CONSUMER_SECRET"
            )
        
        try:
            url = f"{self.base_url}/oauth/v1/generate"
            params = {"grant_type": "client_credentials"}
            auth = (MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET)
            
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data["access_token"]
            
            # Token expires in 1 hour (3600 seconds)
            self.token_expires_at = datetime.now().timestamp() + 3500  # 50 minutes buffer
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to get M-Pesa access token: {str(e)}")
    
    def format_phone_for_mpesa(self, phone_number: str) -> str:
        """Format phone number for M-Pesa API (international format without +)"""
        # Remove any whitespace
        cleaned = phone_number.replace(" ", "").replace("-", "")
        
        if cleaned.startswith('+266'):
            return cleaned[1:]  # Remove the + but keep 266
        elif cleaned.startswith('0'):
            return '266' + cleaned[1:]  # Replace leading 0 with 266
        elif len(cleaned) == 8:
            return '266' + cleaned  # Add country code
        else:
            return cleaned
    
    def initiate_stk_push(self, phone_number: str, amount: float, 
                         account_reference: str = "CertiVert-LS",
                         transaction_desc: str = "Certificate Verification Fee (Lesotho)") -> Dict[str, Any]:
        """Initiate M-Pesa STK Push payment for Lesotho"""
        if not MPESA_SHORTCODE or not MPESA_PASSKEY:
            raise HTTPException(
                status_code=500,
                detail="M-Pesa shortcode and passkey not configured. Please set MPESA_LESOTHO_SHORTCODE and MPESA_LESOTHO_PASSKEY"
            )
        
        # Format phone number for M-Pesa API
        formatted_phone = self.format_phone_for_mpesa(phone_number)
        
        # Validate formatted phone number
        if len(formatted_phone) != 12 or not formatted_phone.startswith('266'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phone number format after formatting: {formatted_phone}. Expected 266XXXXXXXX"
            )
        
        try:
            access_token = self.get_access_token()
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Generate timestamps
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Generate password (Base64 encode of shortcode + passkey + timestamp)
            password_string = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
            password = base64.b64encode(password_string.encode()).decode()
            
            # Convert amount to integer (M-Pesa requires integer amount in cents)
            amount_in_cents = int(amount * 100)  # Convert to the smallest currency unit
            
            payload = {
                "BusinessShortCode": MPESA_SHORTCODE,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount_in_cents,  # Amount in cents
                "PartyA": formatted_phone,
                "PartyB": MPESA_SHORTCODE,
                "PhoneNumber": formatted_phone,
                "CallBackURL": MPESA_CALLBACK_URL,
                "AccountReference": account_reference[:12],  # Max 12 chars
                "TransactionDesc": transaction_desc[:13],  # Max 13 chars
                "Remark": "Certificate verification payment"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"M-Pesa STK push failed: {str(e)}")
    
    def process_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process M-Pesa callback"""
        try:
            # Extract callback metadata
            merchant_request_id = callback_data.get("MerchantRequestID")
            checkout_request_id = callback_data.get("CheckoutRequestID")
            result_code = callback_data.get("ResultCode")
            result_desc = callback_data.get("ResultDesc")
            
            # Extract payment details from metadata
            callback_metadata = callback_data.get("CallbackMetadata", {})
            metadata_items = callback_metadata.get("Item", [])
            
            payment_details = {}
            for item in metadata_items:
                name = item.get("Name")
                value = item.get("Value")
                payment_details[name] = value
            
            # Convert amount back from cents to Maloti if present
            if "Amount" in payment_details:
                payment_details["Amount"] = payment_details["Amount"] / 100
            
            return {
                "merchant_request_id": merchant_request_id,
                "checkout_request_id": checkout_request_id,
                "result_code": result_code,
                "result_desc": result_desc,
                "payment_details": payment_details,
                "success": result_code == 0  # 0 means success
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process M-Pesa callback: {str(e)}")

# Global M-Pesa service instance
mpesa_service = MpesaService()

@router.post("/stk-push")
async def initiate_stk_push(
    request: MpesaSTKRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate M-Pesa STK Push payment for Lesotho"""
    
    # Create payment record with pending status
    payment = Payment(
        verification_request_id=request.verification_request_id,
        payer_user_id=current_user.id,
        method="mpesa_lesotho",
        digits=request.phone_number[-6:],  # Last 6 digits
        reference=f"{request.account_reference}-{current_user.id}",
        amount=request.amount,
        currency="LSL",  # Lesotho Loti
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    try:
        # Initiate STK push
        result = mpesa_service.initiate_stk_push(
            phone_number=request.phone_number,
            amount=request.amount,
            account_reference=f"{request.account_reference[:8]}-{payment.id}",
            transaction_desc=request.transaction_desc
        )
        
        # Update payment with M-Pesa details
        payment.mpesa_merchant_request_id = result.get("MerchantRequestID")
        payment.mpesa_checkout_request_id = result.get("CheckoutRequestID")
        payment.mpesa_response_code = result.get("ResponseCode")
        payment.mpesa_response_description = result.get("ResponseDescription")
        payment.mpesa_customer_message = result.get("CustomerMessage")
        db.commit()
        
        return {
            "payment_id": payment.id,
            "merchant_request_id": result.get("MerchantRequestID"),
            "checkout_request_id": result.get("CheckoutRequestID"),
            "customer_message": "STK push sent. Please check your phone and enter your M-Pesa PIN.",
            "response_description": result.get("ResponseDescription"),
            "status": "pending",
            "next_step": "Please check your phone for M-Pesa STK push prompt and enter your PIN to complete payment.",
            "amount": request.amount,
            "currency": "LSL"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Update payment status to failed
        payment.status = "failed"
        payment.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to initiate M-Pesa payment: {str(e)}")

@router.post("/callback")
async def mpesa_callback(
    callback_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Handle M-Pesa payment callback"""
    
    try:
        # Process callback data
        result = mpesa_service.process_callback(callback_data)
        
        # Find payment by checkout request ID
        payment = db.query(Payment).filter(
            Payment.mpesa_checkout_request_id == result["checkout_request_id"]
        ).first()
        
        if not payment:
            return {"status": "error", "message": "Payment record not found"}
        
        # Update payment status based on result
        if result["success"]:
            payment.status = "confirmed"
            payment.confirmed_at = datetime.utcnow()
            
            # Extract payment details
            payment_details = result.get("payment_details", {})
            payment.mpesa_transaction_id = payment_details.get("MpesaReceiptNumber")
            payment.mpesa_phone_number = payment_details.get("PhoneNumber")
            payment.mpesa_amount = payment_details.get("Amount")
            payment.mpesa_transaction_date = payment_details.get("TransactionDate")
            
            # Update verification request if linked
            if payment.verification_request_id:
                vr = db.query(VerificationRequest).filter(
                    VerificationRequest.id == payment.verification_request_id
                ).first()
                if vr:
                    vr.payment_status = "confirmed"
                    vr.payment_method = "mpesa_lesotho"
                    vr.payment_reference = payment.mpesa_transaction_id
                    vr.payment_confirmed_at = datetime.utcnow()
        else:
            payment.status = "failed"
            payment.error_message = result.get("result_desc", "Payment failed")
        
        db.commit()
        
        return {
            "status": "success",
            "payment_id": payment.id,
            "result_code": result["result_code"],
            "result_desc": result["result_desc"]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/status/{payment_id}")
async def get_payment_status(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment status"""
    
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.payer_user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "payment_id": payment.id,
        "status": payment.status,
        "amount": payment.amount,
        "currency": payment.currency or "LSL",
        "method": payment.method,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None,
        "mpesa_transaction_id": payment.mpesa_transaction_id,
        "error_message": payment.error_message
    }

@router.get("/config")
async def get_mpesa_config():
    """Get M-Pesa configuration status for Lesotho"""
    return {
        "configured": bool(
            MPESA_CONSUMER_KEY and 
            MPESA_CONSUMER_SECRET and 
            MPESA_SHORTCODE and 
            MPESA_PASSKEY
        ),
        "environment": MPESA_ENVIRONMENT,
        "shortcode": MPESA_SHORTCODE[:4] + "****" if MPESA_SHORTCODE else None,
        "callback_url": MPESA_CALLBACK_URL,
        "currency": "LSL (Lesotho Loti/Maloti)"
    }
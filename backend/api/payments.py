from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from auth import get_current_user, require_admin, require_role
from database import get_db
from models import Payment, User, VerificationRequest, PaymentCallback, Institution

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Pydantic models for request/response
class PaymentRecordRequest(BaseModel):
    verification_request_id: Optional[int] = None
    method: str = Field(..., description="Payment method: mpesa_lesotho, mpesa, ecocash, bank")
    digits: str = Field(..., min_length=4, max_length=6, description="Last digits of phone/account")
    reference: Optional[str] = Field(None, description="Payment reference")
    amount: float = Field(5.0, ge=1.0, description="Payment amount")
    phone_number: Optional[str] = Field(None, description="Full phone number for M-Pesa")
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = {"mpesa_lesotho", "mpesa", "ecocash", "bank", "cash"}
        if v not in allowed_methods:
            raise ValueError(f'Invalid payment method. Allowed: {allowed_methods}')
        return v
    
    @validator('digits')
    def validate_digits(cls, v):
        if not v.isdigit():
            raise ValueError('Digits must be numeric')
        if len(v) not in (4, 6):
            raise ValueError('Digits must be 4 or 6 numbers')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v, values):
        if v and values.get('method') in ('mpesa_lesotho', 'mpesa'):
            # Validate Lesotho phone number format
            import re
            phone = v.replace(' ', '').replace('-', '')
            pattern = r'^(\+266|0)?[5-6]\d{7}$'
            if not re.match(pattern, phone):
                raise ValueError('Invalid Lesotho phone number format. Expected: +2665XXXXXXX or 05XXXXXXX')
        return v

class ManualConfirmRequest(BaseModel):
    payment_id: str
    transaction_id: Optional[str] = Field(None, description="M-Pesa transaction ID")
    notes: Optional[str] = None

class PaymentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = {"PENDING", "CONFIRMED", "FAILED", "REFUNDED"}
        if v not in allowed_statuses:
            raise ValueError(f'Invalid status. Allowed: {allowed_statuses}')
        return v

class PaymentResponse(BaseModel):
    id: str
    verification_request_id: Optional[int]
    payer_user_id: str
    payee_institution_code: Optional[str]
    method: str
    amount: float
    currency: str
    status: str
    digits: Optional[str]
    phone_number: Optional[str]
    reference: Optional[str]
    description: Optional[str]
    mpesa_transaction_id: Optional[str]
    mpesa_checkout_request_id: Optional[str]
    mpesa_merchant_request_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    confirmed_at: Optional[datetime]
    updated_at: datetime

class PaymentStatsResponse(BaseModel):
    total_payments: int
    total_amount: float
    confirmed_payments: int
    confirmed_amount: float
    pending_payments: int
    failed_payments: int
    by_method: Dict[str, int]
    daily_totals: List[Dict[str, Any]]

class PaymentCheckResponse(BaseModel):
    required: bool
    amount: Optional[float] = None
    currency: Optional[str] = None
    message: Optional[str] = None
    pending_payment_id: Optional[str] = None

@router.post("/record", response_model=PaymentResponse)
def record_payment(
    payload: PaymentRecordRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Record a payment (manual entry for cash/offline payments)"""
    
    # Check if verification request exists if provided
    vr = None
    if payload.verification_request_id is not None:
        vr = db.query(VerificationRequest).filter(
            VerificationRequest.id == payload.verification_request_id
        ).first()
        if not vr:
            raise HTTPException(status_code=404, detail="Verification request not found")

    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        verification_request_id=payload.verification_request_id,
        payer_user_id=current_user.id,
        method=payload.method,
        digits=payload.digits,
        reference=payload.reference,
        amount=payload.amount,
        currency="LSL",  # Lesotho Loti
        phone_number=payload.phone_number,
        status="confirmed",  # Manual recording means already confirmed
        confirmed_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Mirror status onto verification request for easy filtering
    if vr is not None:
        vr.payment_method = payload.method
        vr.payment_digits = payload.digits
        vr.payment_reference = payload.reference
        vr.payment_status = payment.status
        vr.payment_confirmed_at = datetime.utcnow()
        db.commit()

    return payment

@router.post("/mpesa/initiate")
def initiate_mpesa_payment(
    verification_request_id: Optional[int] = None,
    amount: float = 5.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate an M-Pesa STK Push payment"""
    
    # Check if user has phone number
    if not current_user.phone_number:
        raise HTTPException(
            status_code=400,
            detail="Please add your phone number to your profile to use M-Pesa"
        )
    
    # Check for existing pending payment
    existing_pending = db.query(Payment).filter(
        Payment.payer_user_id == current_user.id,
        Payment.status == "PENDING",
        Payment.created_at >= datetime.utcnow() - timedelta(minutes=30)
    ).first()
    
    if existing_pending:
        return {
            "message": "You have a pending payment",
            "payment_id": existing_pending.id,
            "status": existing_pending.status,
            "checkout_request_id": existing_pending.mpesa_checkout_request_id
        }
    
    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        verification_request_id=verification_request_id,
        payer_user_id=current_user.id,
        method="mpesa_lesotho",
        digits=current_user.phone_number[-6:],
        amount=amount,
        currency="LSL",
        phone_number=current_user.phone_number,
        status="PENDING",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Here you would integrate with M-Pesa API to send STK push
    # For now, we'll simulate a response
    
    return {
        "payment_id": payment.id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "message": "M-Pesa STK push sent to your phone. Please check and enter PIN.",
        "checkout_request_id": payment.id  # Simulated
    }

@router.post("/mpesa/callback")
async def mpesa_callback(
    callback_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Handle M-Pesa payment callback"""
    
    # Extract callback data
    merchant_request_id = callback_data.get("MerchantRequestID")
    checkout_request_id = callback_data.get("CheckoutRequestID")
    result_code = callback_data.get("ResultCode")
    result_desc = callback_data.get("ResultDesc")
    
    # Find payment by checkout request ID
    payment = db.query(Payment).filter(
        Payment.mpesa_checkout_request_id == checkout_request_id
    ).first()
    
    if not payment:
        # Try to find by merchant request ID
        payment = db.query(Payment).filter(
            Payment.mpesa_merchant_request_id == merchant_request_id
        ).first()
    
    if not payment:
        # Log callback for unknown payment
        callback_log = PaymentCallback(
            id=str(uuid.uuid4()),
            payment_id=None,
            callback_data=callback_data,
            processed_at=datetime.utcnow(),
            result_code=str(result_code),
            result_desc=result_desc
        )
        db.add(callback_log)
        db.commit()
        
        return {"status": "error", "message": "Payment not found"}
    
    # Update payment status
    if result_code == 0:  # Success
        payment.status = "CONFIRMED"
        payment.confirmed_at = datetime.utcnow()
        
        # Extract transaction details from callback metadata
        callback_metadata = callback_data.get("CallbackMetadata", {})
        metadata_items = callback_metadata.get("Item", [])
        
        for item in metadata_items:
            name = item.get("Name")
            value = item.get("Value")
            if name == "MpesaReceiptNumber":
                payment.mpesa_transaction_id = value
            elif name == "PhoneNumber":
                payment.mpesa_phone_number = value
            elif name == "Amount":
                payment.mpesa_amount = value / 100  # Convert from cents
            elif name == "TransactionDate":
                payment.mpesa_transaction_date = str(value)
    else:
        payment.status = "FAILED"
        payment.error_message = result_desc
    
    payment.updated_at = datetime.utcnow()
    
    # Update linked verification request
    if payment.verification_request_id and payment.status == "CONFIRMED":
        vr = db.query(VerificationRequest).filter(
            VerificationRequest.id == payment.verification_request_id
        ).first()
        if vr:
            vr.payment_status = payment.status
            vr.payment_method = payment.method
            vr.payment_reference = payment.mpesa_transaction_id
            vr.payment_confirmed_at = payment.confirmed_at
            db.commit()
    
    # Log callback
    callback_log = PaymentCallback(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        callback_data=callback_data,
        processed_at=datetime.utcnow(),
        result_code=str(result_code),
        result_desc=result_desc
    )
    db.add(callback_log)
    db.commit()
    
    return {
        "status": "success",
        "payment_id": payment.id,
        "result_code": result_code,
        "result_desc": result_desc
    }

@router.post("/manual/confirm", response_model=PaymentResponse)
def manual_confirm_payment(
    req: ManualConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Manually confirm a payment (admin only)"""
    
    payment = db.query(Payment).filter(Payment.id == req.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    old_status = payment.status
    payment.status = "CONFIRMED"
    payment.confirmed_at = datetime.utcnow()
    payment.updated_at = datetime.utcnow()
    
    if req.transaction_id:
        payment.mpesa_transaction_id = req.transaction_id
    
    db.commit()
    db.refresh(payment)

    # Mirror to verification request if linked
    if payment.verification_request_id:
        vr = db.query(VerificationRequest).filter(
            VerificationRequest.id == payment.verification_request_id
        ).first()
        if vr:
            vr.payment_status = payment.status
            vr.payment_confirmed_at = payment.confirmed_at
            db.commit()
    
    return payment

@router.post("/{payment_id}/status")
def update_payment_status(
    payment_id: str,
    status_update: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update payment status (admin only)"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    old_status = payment.status
    payment.status = status_update.status
    payment.updated_at = datetime.utcnow()
    
    if status_update.status == "CONFIRMED" and old_status != "CONFIRMED":
        payment.confirmed_at = datetime.utcnow()
    
    if status_update.notes:
        payment.error_message = status_update.notes
    
    db.commit()
    db.refresh(payment)
    
    # Update verification request if linked
    if payment.verification_request_id:
        vr = db.query(VerificationRequest).filter(
            VerificationRequest.id == payment.verification_request_id
        ).first()
        if vr:
            vr.payment_status = payment.status
            if payment.status == "CONFIRMED":
                vr.payment_confirmed_at = payment.confirmed_at
            db.commit()
    
    return {
        "payment_id": payment.id,
        "old_status": old_status,
        "new_status": payment.status,
        "confirmed_at": payment.confirmed_at
    }

@router.get("/my", response_model=List[PaymentResponse])
def my_payments(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get current user's payment history"""
    
    query = db.query(Payment).filter(Payment.payer_user_id == current_user.id)
    
    if status:
        query = query.filter(Payment.status == status.upper())
    
    payments = query.order_by(Payment.created_at.desc()).limit(limit).all()
    
    return payments

@router.get("/verification/{verification_request_id}")
def get_payments_for_verification(
    verification_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payments for a specific verification request"""
    
    payments = db.query(Payment).filter(
        Payment.verification_request_id == verification_request_id
    ).order_by(Payment.created_at.desc()).all()
    
    return [
        {
            "id": p.id,
            "method": p.method,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "mpesa_transaction_id": p.mpesa_transaction_id,
            "created_at": p.created_at,
            "confirmed_at": p.confirmed_at
        }
        for p in payments
    ]

@router.get("/stats", response_model=PaymentStatsResponse)
def get_payment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    days: int = Query(30, ge=1, le=365)
):
    """Get payment statistics (admin only)"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Overall stats
    stats = db.query(
        func.count(Payment.id).label('total'),
        func.sum(Payment.amount).label('total_amount'),
        func.count(case([(Payment.status == 'CONFIRMED', Payment.id)])).label('confirmed_count'),
        func.sum(case([(Payment.status == 'CONFIRMED', Payment.amount)], else_=0)).label('confirmed_amount'),
        func.count(case([(Payment.status == 'PENDING', Payment.id)])).label('pending_count'),
        func.count(case([(Payment.status == 'FAILED', Payment.id)])).label('failed_count')
    ).filter(Payment.created_at >= cutoff_date).first()
    
    # Stats by payment method
    by_method = db.query(
        Payment.method,
        func.count(Payment.id).label('count')
    ).filter(Payment.created_at >= cutoff_date).group_by(Payment.method).all()
    
    # Daily totals
    daily_totals = db.query(
        func.date(Payment.created_at).label('date'),
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total')
    ).filter(Payment.created_at >= cutoff_date).group_by(
        func.date(Payment.created_at)
    ).order_by(func.date(Payment.created_at)).all()
    
    total = stats[0] or 0
    total_amount = float(stats[1] or 0)
    
    return {
        "total_payments": total,
        "total_amount": total_amount,
        "confirmed_payments": stats[2] or 0,
        "confirmed_amount": float(stats[3] or 0),
        "pending_payments": stats[4] or 0,
        "failed_payments": stats[5] or 0,
        "by_method": {method: count for method, count in by_method},
        "daily_totals": [
            {"date": str(date), "count": count, "amount": float(amount or 0)}
            for date, count, amount in daily_totals
        ]
    }

@router.get("/check-required")
def check_payment_required(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaymentCheckResponse:
    """Check if user needs to make a payment before verification"""
    
    # Check if user has any pending payment
    pending_payment = db.query(Payment).filter(
        Payment.payer_user_id == current_user.id,
        Payment.status == "PENDING"
    ).first()
    
    if pending_payment:
        return PaymentCheckResponse(
            required=True,
            amount=pending_payment.amount,
            currency=pending_payment.currency,
            message="You have a pending payment. Please complete it first.",
            pending_payment_id=pending_payment.id
        )
    
    # Check if user has made a payment today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    payment_today = db.query(Payment).filter(
        Payment.payer_user_id == current_user.id,
        Payment.status == "CONFIRMED",
        Payment.confirmed_at >= today_start,
        Payment.confirmed_at <= today_end
    ).first()
    
    if payment_today:
        return PaymentCheckResponse(
            required=False,
            message="You have already made a payment today"
        )
    
    # Check institution credits for issuers
    if current_user.institution_code and current_user.role == "issuer":
        institution = db.query(Institution).filter(
            Institution.code == current_user.institution_code
        ).first()
        
        if institution and institution.credits and institution.credits > 0:
            return PaymentCheckResponse(
                required=False,
                message="Using institution credits"
            )
    
    # Default: payment required
    return PaymentCheckResponse(
        required=True,
        amount=5.00,
        currency="LSL",
        message="Payment required for certificate verification"
    )

@router.get("/institution/{institution_code}")
def get_institution_payments(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get payments for a specific institution (admin only)"""
    
    query = db.query(Payment).filter(Payment.payee_institution_code == institution_code.upper())
    
    if status:
        query = query.filter(Payment.status == status.upper())
    
    payments = query.order_by(Payment.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "payer_user_id": p.payer_user_id,
            "amount": p.amount,
            "currency": p.currency,
            "method": p.method,
            "status": p.status,
            "mpesa_transaction_id": p.mpesa_transaction_id,
            "created_at": p.created_at,
            "confirmed_at": p.confirmed_at
        }
        for p in payments
    ]

@router.get("/status/{payment_id}")
async def get_payment_status(
    payment_id: str,
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
    
    # Check authorization
    if payment.payer_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this payment")
    
    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment details by ID"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check authorization
    if payment.payer_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this payment")
    
    return payment

@router.get("/{payment_id}/callbacks")
def get_payment_callbacks(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get callback history for a payment (admin only)"""
    
    callbacks = db.query(PaymentCallback).filter(
        PaymentCallback.payment_id == payment_id
    ).order_by(PaymentCallback.processed_at.desc()).all()
    
    return [
        {
            "id": cb.id,
            "processed_at": cb.processed_at,
            "result_code": cb.result_code,
            "result_desc": cb.result_desc,
            "callback_data": cb.callback_data
        }
        for cb in callbacks
    ]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import uuid
from datetime import datetime

from database import get_db
from models import User, Payment, VerificationRequest
from auth import get_current_active_user
from mpesa_client import MpesaB2BClient

router = APIRouter(prefix="/api/mpesa", tags=["mpesa"])

# Initialize M-Pesa client
mpesa_client = MpesaB2BClient()

# Pydantic models
class PaymentRequest(BaseModel):
    university_code: str
    amount: str
    certificate_reference: str
    description: Optional[str] = None

class PaymentResponse(BaseModel):
    success: bool
    transaction_id: Optional[str] = None
    conversation_id: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TransactionStatusRequest(BaseModel):
    transaction_reference: str

@router.post("/b2b-payment", response_model=PaymentResponse)
async def process_b2b_payment(
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process REAL B2B payment from University to ECOL for certificate verification
    Amount: M10.00 (1000 cents) for testing
    """
    try:
        # Validate user permissions
        if current_user.role not in ['issuer', 'admin']:
            raise HTTPException(
                status_code=403, 
                detail="Only issuers and admins can process payments"
            )
        
        # Set real test amount - M10.00 = 1000 cents
        real_amount = "1000"  # M10.00 in cents
        
        # Use provided amount for flexibility, but default to M10.00
        amount_to_use = payment_request.amount if payment_request.amount != "0" else real_amount
        
        # Process REAL payment via M-Pesa
        response = mpesa_client.b2b_payment(
            university_code=payment_request.university_code,
            amount=amount_to_use,  # Use flexible amount
            certificate_reference=payment_request.certificate_reference,
            description=f"Certificate verification - {payment_request.certificate_reference}"
        )
        
        # Check if payment was successful
        is_successful = mpesa_client.is_payment_successful(response)
        response_message = mpesa_client.get_response_message(response)
        
        # Create REAL payment record in database
        payment_record = Payment(
            verification_request_id=None,  # Will be linked later
            payer_user_id=current_user.id,
            method="mpesa_b2b_real",
            reference=payment_request.certificate_reference,
            amount=float(amount_to_use) / 100,  # Convert from cents to LSL
            status="confirmed" if is_successful else "failed",
            mpesa_transaction_id=response.get('output_TransactionID'),
            mpesa_conversation_id=response.get('output_ConversationID'),
            mpesa_response_code=response.get('output_ResponseCode'),
            mpesa_response_description=response_message,
            created_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow() if is_successful else None
        )
        
        db.add(payment_record)
        db.commit()
        db.refresh(payment_record)
        
        # Prepare response with real transaction details
        payment_response = PaymentResponse(
            success=is_successful,
            transaction_id=response.get('output_TransactionID'),
            conversation_id=response.get('output_ConversationID'),
            response_code=response.get('output_ResponseCode'),
            response_message=response_message,
            metadata={
                **response.get('_metadata', {}),
                'amount_maloti': float(amount_to_use) / 100,  # Actual amount in LSL
                'payment_type': 'REAL_TRANSACTION',
                'processed_by': current_user.username,
                'certificate_reference': payment_request.certificate_reference
            }
        )
        
        return payment_response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Real M-Pesa payment processing failed: {str(e)}"
        )

@router.post("/query-transaction")
async def query_transaction_status(
    transaction_request: TransactionStatusRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Query M-Pesa transaction status
    """
    try:
        # Validate user permissions
        if current_user.role not in ['issuer', 'admin']:
            raise HTTPException(
                status_code=403, 
                detail="Only issuers and admins can query transactions"
            )
        
        # Query transaction status
        status = mpesa_client.query_transaction(transaction_request.transaction_reference)
        
        return {
            "success": True,
            "transaction_reference": transaction_request.transaction_reference,
            "status": status,
            "is_successful": mpesa_client.is_payment_successful(status),
            "message": mpesa_client.get_response_message(status)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Transaction query failed: {str(e)}"
        )

@router.get("/payment-history")
async def get_payment_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payment history for current user
    """
    try:
        payments = db.query(Payment).filter(
            Payment.payer_user_id == current_user.id
        ).order_by(Payment.created_at.desc()).limit(limit).all()
        
        history = []
        for payment in payments:
            history.append({
                "id": payment.id,
                "amount": payment.amount,
                "currency": "LSL",
                "method": payment.method,
                "reference": payment.reference,
                "status": payment.status,
                "transaction_id": payment.mpesa_transaction_id,
                "conversation_id": payment.mpesa_conversation_id,
                "response_code": payment.mpesa_response_code,
                "response_message": payment.mpesa_response_description,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None
            })
        
        return {
            "success": True,
            "history": history,
            "total_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get payment history: {str(e)}"
        )

@router.get("/mpesa-status")
async def get_mpesa_status(current_user: User = Depends(get_current_active_user)):
    """
    Get M-Pesa system status and configuration
    """
    try:
        # Test session generation
        try:
            session = mpesa_client.generate_session()
            session_status = "operational"
            session_error = None
        except Exception as e:
            session_status = "failed"
            session_error = str(e)
        
        return {
            "mpesa_available": session_status == "operational",
            "session_status": session_status,
            "session_error": session_error,
            "configuration": {
                "service_provider_code": mpesa_client.service_provider_code,
                "ecol_code": mpesa_client.ecol_code,
                "country": mpesa_client.country,
                "currency": mpesa_client.currency,
                "session_lifetime": mpesa_client.session_lifetime
            },
            "user_permissions": {
                "can_process_payments": current_user.role in ['issuer', 'admin'],
                "can_query_transactions": current_user.role in ['issuer', 'admin'],
                "role": current_user.role
            },
            "supported_operations": {
                "b2b_payment": True,
                "transaction_query": True,
                "payment_history": True
            }
        }
        
    except Exception as e:
        return {
            "mpesa_available": False,
            "error": str(e),
            "user_permissions": {
                "can_process_payments": False,
                "can_query_transactions": False,
                "role": current_user.role
            }
        }

@router.post("/test-payment")
async def test_payment_integration(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Test M-Pesa integration with a small amount
    """
    try:
        # Only allow admins to test payments
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=403, 
                detail="Only admins can test payment integration"
            )
        
        # Use test amount (1 LSL = 100 cents)
        test_response = mpesa_client.b2b_payment(
            university_code="TEST001",
            amount="100",  # 1 LSL
            certificate_reference=f"TEST-{uuid.uuid4().hex[:8]}",
            description="Test payment integration"
        )
        
        return {
            "success": mpesa_client.is_payment_successful(test_response),
            "test_response": test_response,
            "message": mpesa_client.get_response_message(test_response)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Test payment failed: {str(e)}"
        )

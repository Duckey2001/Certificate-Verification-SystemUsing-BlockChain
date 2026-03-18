"""
M-Pesa B2B Payment Routes for CertiVert LGCSE
Handles university-to-ECOL payments for certificate verification
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import json
import uuid
from datetime import datetime
import logging

from auth import get_current_user, require_role
from database import get_db
from models import User, Payment, VerificationRequest, Certificate, University
from mpesa_b2b_client import mpesa_b2b_client

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mpesa-b2b", tags=["M-Pesa B2B Payments"])

# Pydantic models
class B2BPaymentRequest(BaseModel):
    university_code: str = Field(..., description="University code (e.g., NUL001, LEC001)")
    amount: str = Field(..., description="Amount in cents (e.g., 1000 = M10.00)")
    certificate_reference: str = Field(..., description="Certificate reference number")
    description: Optional[str] = Field(None, description="Payment description")
    
    @validator('amount')
    def validate_amount(cls, v):
        try:
            amount_int = int(v)
            if amount_int < 500:
                raise ValueError('Amount must be at least 500 cents (M5.00)')
            if amount_int > 1000000:  # M10,000 maximum
                raise ValueError('Amount exceeds maximum (M10,000.00)')
            return v
        except ValueError:
            raise ValueError('Amount must be a valid integer')
    
    @validator('university_code')
    def validate_university_code(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Invalid university code')
        return v.upper()
    
    @validator('certificate_reference')
    def validate_certificate_reference(cls, v):
        if not v or len(v) < 5:
            raise ValueError('Invalid certificate reference')
        return v

class B2BPaymentResponse(BaseModel):
    success: bool
    payment_id: int
    transaction_id: Optional[str] = None
    conversation_id: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    amount_paid: float
    amount_maloti: float
    currency: str = "LSL"
    certificate_reference: str
    university_code: str
    status: str
    metadata: Optional[Dict[str, Any]] = None

class TransactionQueryRequest(BaseModel):
    transaction_reference: str = Field(..., description="Transaction reference to query")

class TransactionQueryResponse(BaseModel):
    success: bool
    status: str
    amount: Optional[float] = None
    transaction_date: Optional[str] = None
    receiver_party: Optional[str] = None
    response_code: Optional[str] = None
    message: str

class PaymentHistoryItem(BaseModel):
    id: int
    amount: float
    amount_maloti: float
    currency: str
    method: str
    certificate_reference: str
    university_code: str
    university_name: Optional[str]
    status: str
    transaction_id: Optional[str]
    response_code: Optional[str]
    response_message: Optional[str]
    created_at: str
    confirmed_at: Optional[str]
    
    class Config:
        from_attributes = True

class PaymentHistoryResponse(BaseModel):
    success: bool
    payments: List[PaymentHistoryItem]
    total_count: int
    page: int
    per_page: int

class MpesaStatusResponse(BaseModel):
    mpesa_available: bool
    session_status: str
    configuration: Dict[str, Any]
    user_permissions: Dict[str, Any]
    supported_operations: Dict[str, bool]

# Payment status constants
class PaymentStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@router.post("/b2b-payment", response_model=B2BPaymentResponse)
async def process_b2b_payment(
    payment_request: B2BPaymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['issuer', 'admin']))
):
    """
    Process B2B payment from University to ECOL for certificate verification
    - Minimum amount: M5.00 (500 cents)
    - Maximum amount: M10,000.00 (1,000,000 cents)
    - Currency: LSL (Lesotho Loti)
    """
    try:
        logger.info(f"B2B payment request from {current_user.username} for certificate {payment_request.certificate_reference}")
        
        # Validate university exists
        university = db.query(University).filter(
            University.code == payment_request.university_code
        ).first()
        
        if not university:
            logger.error(f"University not found: {payment_request.university_code}")
            raise HTTPException(
                status_code=404, 
                detail=f"University with code {payment_request.university_code} not found"
            )
        
        # Validate certificate exists and is eligible
        certificate = db.query(Certificate).filter(
            Certificate.reference_number == payment_request.certificate_reference
        ).first()
        
        if not certificate:
            logger.error(f"Certificate not found: {payment_request.certificate_reference}")
            raise HTTPException(
                status_code=404, 
                detail=f"Certificate {payment_request.certificate_reference} not found"
            )
        
        # Check if certificate already has a paid/processing payment
        if certificate.payment_status in ['paid', 'processing']:
            existing_payment = db.query(Payment).filter(
                Payment.reference == payment_request.certificate_reference,
                Payment.status.in_(['confirmed', 'processing'])
            ).first()
            
            if existing_payment:
                logger.warning(f"Payment already exists for certificate {payment_request.certificate_reference}")
                return B2BPaymentResponse(
                    success=True,
                    payment_id=existing_payment.id,
                    transaction_id=existing_payment.mpesa_transaction_id,
                    conversation_id=existing_payment.mpesa_conversation_id,
                    response_code=existing_payment.mpesa_response_code,
                    response_message="Payment already processed",
                    amount_paid=float(payment_request.amount) / 100,
                    amount_maloti=float(payment_request.amount) / 100,
                    currency="LSL",
                    certificate_reference=payment_request.certificate_reference,
                    university_code=payment_request.university_code,
                    status=existing_payment.status,
                    metadata={
                        'existing_payment': True,
                        'payment_id': existing_payment.id,
                        'created_at': existing_payment.created_at.isoformat() if existing_payment.created_at else None
                    }
                )
        
        # Calculate amount in Maloti
        amount_maloti = int(payment_request.amount) / 100
        
        # Create payment record
        payment = Payment(
            payer_user_id=current_user.id,
            method="mpesa_b2b",
            reference=payment_request.certificate_reference,
            amount=amount_maloti,
            currency="LSL",
            status=PaymentStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={
                'university_code': payment_request.university_code,
                'university_name': university.name,
                'certificate_reference': payment_request.certificate_reference,
                'requested_by': current_user.username,
                'requested_by_id': current_user.id,
                'requested_at': datetime.utcnow().isoformat(),
                'amount_cents': payment_request.amount
            }
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Process B2B payment via M-Pesa
        logger.info(f"Calling M-Pesa B2B API for payment {payment.id}")
        
        response = mpesa_b2b_client.b2b_payment(
            university_code=payment_request.university_code,
            amount=payment_request.amount,
            certificate_reference=payment_request.certificate_reference,
            description=payment_request.description or f"Certificate verification - {payment_request.certificate_reference}"
        )
        
        # Check payment result
        is_successful = mpesa_b2b_client.is_payment_successful(response)
        response_message = mpesa_b2b_client.get_response_message(response)
        
        # Update payment with M-Pesa response
        payment.mpesa_transaction_id = response.get('output_TransactionID')
        payment.mpesa_conversation_id = response.get('output_ConversationID')
        payment.mpesa_response_code = response.get('output_ResponseCode')
        payment.mpesa_response_description = response_message
        payment.payment_metadata = {
            **(payment.payment_metadata or {}),
            'mpesa_response': response,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        if is_successful:
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_at = datetime.utcnow()
            
            # Update certificate
            certificate.payment_status = "paid"
            certificate.payment_id = payment.id
            certificate.paid_at = datetime.utcnow()
            certificate.verification_status = "pending"
            
            # Create verification request in background
            background_tasks.add_task(
                create_verification_request,
                certificate.id,
                current_user.id,
                payment.id,
                payment_request.university_code
            )
            
            logger.info(f"Payment {payment.id} confirmed successfully")
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = response_message
            logger.warning(f"Payment {payment.id} failed: {response_message}")
        
        db.commit()
        
        # Return response
        return B2BPaymentResponse(
            success=is_successful,
            payment_id=payment.id,
            transaction_id=payment.mpesa_transaction_id,
            conversation_id=payment.mpesa_conversation_id,
            response_code=payment.mpesa_response_code,
            response_message=response_message,
            amount_paid=amount_maloti if is_successful else 0,
            amount_maloti=amount_maloti,
            currency="LSL",
            certificate_reference=payment_request.certificate_reference,
            university_code=payment_request.university_code,
            status=payment.status,
            metadata={
                'payment_created_at': payment.created_at.isoformat(),
                'payment_confirmed_at': payment.confirmed_at.isoformat() if payment.confirmed_at else None,
                'university_name': university.name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"B2B payment error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"M-Pesa B2B payment failed: {str(e)}"
        )

@router.post("/query-transaction", response_model=TransactionQueryResponse)
async def query_transaction(
    query_request: TransactionQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['issuer', 'admin', 'verifier']))
):
    """
    Query M-Pesa transaction status
    """
    try:
        logger.info(f"Transaction query from {current_user.username}: {query_request.transaction_reference}")
        
        # Find payment in database
        payment = db.query(Payment).filter(
            (Payment.mpesa_transaction_id == query_request.transaction_reference) |
            (Payment.reference == query_request.transaction_reference)
        ).first()
        
        if not payment:
            logger.warning(f"Transaction not found: {query_request.transaction_reference}")
            return TransactionQueryResponse(
                success=False,
                status="not_found",
                message="Transaction not found in database"
            )
        
        # Check authorization
        if payment.payer_user_id != current_user.id and current_user.role != 'admin':
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to view this transaction"
            )
        
        # Query M-Pesa for real-time status if transaction ID exists
        mpesa_status = None
        if payment.mpesa_transaction_id:
            try:
                mpesa_status = mpesa_b2b_client.query_transaction(payment.mpesa_transaction_id)
                
                # Update payment status if changed
                if mpesa_b2b_client.is_payment_successful(mpesa_status) and payment.status == PaymentStatus.PENDING:
                    payment.status = PaymentStatus.CONFIRMED
                    payment.confirmed_at = datetime.utcnow()
                    db.commit()
            except Exception as e:
                logger.error(f"M-Pesa query failed: {str(e)}")
        
        return TransactionQueryResponse(
            success=True,
            status=payment.status,
            amount=payment.amount,
            transaction_date=payment.confirmed_at.isoformat() if payment.confirmed_at else payment.created_at.isoformat(),
            receiver_party="ECOL",
            response_code=payment.mpesa_response_code,
            message=payment.mpesa_response_description or f"Transaction {payment.status}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction query error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Transaction query failed: {str(e)}"
        )

@router.get("/payment-history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    university: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get B2B payment history with filters
    """
    try:
        # Build query
        query = db.query(Payment).filter(Payment.method == "mpesa_b2b")
        
        # Filter by user role
        if current_user.role == 'issuer':
            # Issuers see only their payments
            query = query.filter(Payment.payer_user_id == current_user.id)
        elif current_user.role == 'verifier':
            # Verifiers see all payments for certificates they verify
            # This is a simplified example - adjust based on your business logic
            pass
        # Admins see all payments
        
        # Apply filters
        if status:
            query = query.filter(Payment.status == status)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Payment.created_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Payment.created_at <= end)
        
        # Filter by university (from metadata)
        if university:
            # This assumes university is stored in metadata
            # In production, you might want to add a university_id field
            all_payments = query.all()
            filtered_payments = [
                p for p in all_payments 
                if p.payment_metadata and p.payment_metadata.get('university_code') == university
            ]
            total_count = len(filtered_payments)
            
            # Manual pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            payments = filtered_payments[start_idx:end_idx]
        else:
            # Count total
            total_count = query.count()
            
            # Paginate
            payments = query.order_by(Payment.created_at.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
        
        # Build response items
        payment_items = []
        for payment in payments:
            # Get university name from metadata
            university_name = None
            university_code = None
            if payment.payment_metadata:
                university_code = payment.payment_metadata.get('university_code')
                university_name = payment.payment_metadata.get('university_name')
            
            payment_items.append(PaymentHistoryItem(
                id=payment.id,
                amount=payment.amount,
                amount_maloti=payment.amount,
                currency=payment.currency or "LSL",
                method=payment.method,
                certificate_reference=payment.reference,
                university_code=university_code or "UNKNOWN",
                university_name=university_name,
                status=payment.status,
                transaction_id=payment.mpesa_transaction_id,
                response_code=payment.mpesa_response_code,
                response_message=payment.mpesa_response_description,
                created_at=payment.created_at.isoformat() if payment.created_at else None,
                confirmed_at=payment.confirmed_at.isoformat() if payment.confirmed_at else None
            ))
        
        return PaymentHistoryResponse(
            success=True,
            payments=payment_items,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Payment history error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get payment history: {str(e)}"
        )

@router.get("/payment/{payment_id}")
async def get_payment_details(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific payment
    """
    try:
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.method == "mpesa_b2b"
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check authorization
        if payment.payer_user_id != current_user.id and current_user.role not in ['admin', 'verifier']:
            raise HTTPException(status_code=403, detail="Not authorized to view this payment")
        
        # Get certificate details
        certificate = db.query(Certificate).filter(
            Certificate.reference_number == payment.reference
        ).first()
        
        # Get university details from metadata
        university_name = None
        university_code = None
        if payment.payment_metadata:
            university_code = payment.payment_metadata.get('university_code')
            university_name = payment.payment_metadata.get('university_name')
        
        return {
            "payment": {
                "id": payment.id,
                "amount": payment.amount,
                "amount_maloti": payment.amount,
                "currency": payment.currency or "LSL",
                "method": payment.method,
                "reference": payment.reference,
                "certificate_reference": payment.reference,
                "status": payment.status,
                "transaction_id": payment.mpesa_transaction_id,
                "conversation_id": payment.mpesa_conversation_id,
                "response_code": payment.mpesa_response_code,
                "response_message": payment.mpesa_response_description,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None,
                "failure_reason": payment.failure_reason,
                "metadata": payment.payment_metadata
            },
            "certificate": {
                "id": certificate.id if certificate else None,
                "reference": certificate.reference_number if certificate else None,
                "student_name": certificate.student_name if certificate else None,
                "verification_status": certificate.verification_status if certificate else None
            },
            "university": {
                "code": university_code,
                "name": university_name
            },
            "payer": {
                "id": payment.payer_user_id,
                "username": current_user.username if payment.payer_user_id == current_user.id else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment details error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get payment details: {str(e)}"
        )

@router.get("/mpesa-status", response_model=MpesaStatusResponse)
async def get_mpesa_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get M-Pesa B2B system status
    """
    try:
        # Test session generation
        session_status = "operational"
        session_error = None
        
        try:
            session = mpesa_b2b_client.generate_session()
            if not session:
                session_status = "failed"
        except Exception as e:
            session_status = "error"
            session_error = str(e)
        
        return MpesaStatusResponse(
            mpesa_available=session_status == "operational",
            session_status=session_status,
            configuration={
                "service_provider_code": mpesa_b2b_client.service_provider_code,
                "ecol_code": mpesa_b2b_client.ecol_code,
                "country": mpesa_b2b_client.country,
                "currency": mpesa_b2b_client.currency,
                "minimum_amount": "500 cents (M5.00)",
                "maximum_amount": "1,000,000 cents (M10,000.00)",
                "environment": "production"
            },
            user_permissions={
                "can_process_payments": current_user.role in ['issuer', 'admin'],
                "can_query_transactions": current_user.role in ['issuer', 'admin', 'verifier'],
                "role": current_user.role
            },
            supported_operations={
                "b2b_payment": True,
                "transaction_query": True,
                "payment_history": True
            }
        )
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return MpesaStatusResponse(
            mpesa_available=False,
            session_status="error",
            configuration={},
            user_permissions={
                "can_process_payments": False,
                "can_query_transactions": False,
                "role": current_user.role
            },
            supported_operations={}
        )

@router.post("/webhook")
async def mpesa_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for M-Pesa payment notifications
    """
    try:
        logger.info(f"Received M-Pesa webhook")
        
        # Extract transaction details
        transaction_id = payload.get('output_TransactionID')
        response_code = payload.get('output_ResponseCode')
        response_desc = payload.get('output_ResponseDesc')
        
        if not transaction_id:
            logger.warning("Webhook missing transaction ID")
            return JSONResponse(status_code=400, content={"message": "Missing transaction ID"})
        
        # Find payment
        payment = db.query(Payment).filter(
            Payment.mpesa_transaction_id == transaction_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for transaction: {transaction_id}")
            return JSONResponse(status_code=404, content={"message": "Payment not found"})
        
        # Update payment status
        is_successful = mpesa_b2b_client.is_payment_successful(payload)
        
        if is_successful and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_at = datetime.utcnow()
            payment.mpesa_response_description = response_desc or "Confirmed via webhook"
            
            # Update certificate
            certificate = db.query(Certificate).filter(
                Certificate.reference_number == payment.reference
            ).first()
            
            if certificate:
                certificate.payment_status = "paid"
                certificate.payment_id = payment.id
                certificate.paid_at = datetime.utcnow()
                
                # Get university code from payment metadata
                university_code = None
                if payment.payment_metadata:
                    university_code = payment.payment_metadata.get('university_code')
                
                # Create verification request
                background_tasks.add_task(
                    create_verification_request,
                    certificate.id,
                    payment.payer_user_id,
                    payment.id,
                    university_code
                )
        
        elif not is_successful and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = response_desc or "Failed via webhook"
        
        # Update metadata
        payment.payment_metadata = {
            **(payment.payment_metadata or {}),
            'webhook_received_at': datetime.utcnow().isoformat(),
            'webhook_payload': payload
        }
        
        db.commit()
        logger.info(f"Payment {payment.id} updated via webhook: {payment.status}")
        
        return JSONResponse(
            status_code=200, 
            content={
                "message": "Webhook processed successfully",
                "payment_id": payment.id,
                "status": payment.status
            }
        )
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"message": f"Webhook processing failed: {str(e)}"}
        )

@router.post("/test-payment")
async def test_b2b_payment(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['admin']))
):
    """
    Test B2B payment integration (admin only)
    """
    try:
        logger.info(f"Test payment requested by admin: {current_user.username}")
        
        # Generate test data
        test_ref = f"TEST-{uuid.uuid4().hex[:8].upper()}"
        test_amount = "500"  # M5.00 minimum
        
        # Create test payment record
        payment = Payment(
            payer_user_id=current_user.id,
            method="mpesa_b2b_test",
            reference=test_ref,
            amount=5.00,
            currency="LSL",
            status=PaymentStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={
                'test': True,
                'requested_by': current_user.username,
                'test_reference': test_ref
            }
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Process test payment
        response = mpesa_b2b_client.b2b_payment(
            university_code="TEST001",
            amount=test_amount,
            certificate_reference=test_ref,
            description="Test payment"
        )
        
        # Update payment
        payment.mpesa_transaction_id = response.get('output_TransactionID')
        payment.mpesa_conversation_id = response.get('output_ConversationID')
        payment.mpesa_response_code = response.get('output_ResponseCode')
        payment.mpesa_response_description = mpesa_b2b_client.get_response_message(response)
        
        if mpesa_b2b_client.is_payment_successful(response):
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_at = datetime.utcnow()
        else:
            payment.status = PaymentStatus.FAILED
        
        db.commit()
        
        return {
            "success": mpesa_b2b_client.is_payment_successful(response),
            "test_reference": test_ref,
            "payment_id": payment.id,
            "response": {
                "code": response.get('output_ResponseCode'),
                "description": response.get('output_ResponseDesc'),
                "transaction_id": response.get('output_TransactionID'),
                "conversation_id": response.get('output_ConversationID')
            },
            "message": mpesa_b2b_client.get_response_message(response)
        }
        
    except Exception as e:
        logger.error(f"Test payment failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Test payment failed: {str(e)}"
        )

# Background task functions
async def create_verification_request(
    certificate_id: int, 
    user_id: int, 
    payment_id: int,
    university_code: Optional[str] = None
):
    """
    Create verification request after successful payment
    """
    try:
        from sqlalchemy.orm import Session
        from database import SessionLocal
        from models import VerificationRequest
        
        db = SessionLocal()
        try:
            # Check if verification request already exists
            existing = db.query(VerificationRequest).filter(
                VerificationRequest.certificate_id == certificate_id
            ).first()
            
            if existing:
                logger.info(f"Verification request already exists for certificate {certificate_id}")
                return
            
            # Create new verification request
            verification = VerificationRequest(
                certificate_id=certificate_id,
                requester_id=user_id,
                payment_id=payment_id,
                status="pending",
                created_at=datetime.utcnow(),
                metadata={
                    'university_code': university_code,
                    'payment_completed_at': datetime.utcnow().isoformat()
                }
            )
            
            db.add(verification)
            db.commit()
            
            logger.info(f"Verification request {verification.id} created for certificate {certificate_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to create verification request: {str(e)}")

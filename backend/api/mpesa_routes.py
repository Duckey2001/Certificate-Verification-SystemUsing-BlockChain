"""
M-Pesa B2B Payment Routes for Certificate Verification System
Handles real payment processing with database integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import json
import uuid
from datetime import datetime, timedelta
import logging

from database import get_db
from models import User, Payment, VerificationRequest, Certificate, University
from auth import get_current_user, require_admin
from mpesa_client import mpesa_client

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mpesa", tags=["M-Pesa Payments"])

# Pydantic models
class PaymentRequest(BaseModel):
    university_code: str = Field(..., description="University code")
    amount: str = Field(..., description="Amount in cents (e.g., 1000 = M10.00)")
    certificate_reference: str = Field(..., description="Certificate reference number")
    description: Optional[str] = Field(None, description="Payment description")
    
    @validator('amount')
    def validate_amount(cls, v):
        try:
            amount_int = int(v)
            if amount_int < 500:
                raise ValueError('Amount must be at least 500 cents (M5.00)')
            return v
        except ValueError:
            raise ValueError('Amount must be a valid integer')

class PaymentResponse(BaseModel):
    success: bool
    transaction_id: Optional[str] = None
    conversation_id: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    amount_paid: Optional[float] = None
    currency: str = "LSL"
    metadata: Optional[Dict[str, Any]] = None

class TransactionStatusRequest(BaseModel):
    transaction_reference: str = Field(..., description="Transaction reference to query")

class TransactionStatusResponse(BaseModel):
    success: bool
    status: Optional[str] = None
    amount: Optional[str] = None
    transaction_date: Optional[str] = None
    receiver_party: Optional[str] = None
    response_code: Optional[str] = None
    message: str

class PaymentHistoryItem(BaseModel):
    id: int
    amount: float
    currency: str
    method: str
    reference: str
    certificate_reference: str
    status: str
    transaction_id: Optional[str]
    conversation_id: Optional[str]
    response_code: Optional[str]
    response_message: Optional[str]
    created_at: str
    confirmed_at: Optional[str]
    university_name: Optional[str]

class PaymentHistoryResponse(BaseModel):
    success: bool
    payments: List[PaymentHistoryItem]
    total_count: int
    page: int = 1
    per_page: int = 20

class MpesaStatusResponse(BaseModel):
    mpesa_available: bool
    session_status: str
    session_error: Optional[str]
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

@router.post("/b2b-payment", response_model=PaymentResponse)
async def process_b2b_payment(
    payment_request: PaymentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process REAL B2B payment from University to ECOL for certificate verification
    Minimum amount: M5.00 (500 cents)
    """
    try:
        logger.info(f"Payment request from {current_user.username} for certificate {payment_request.certificate_reference}")
        
        # Validate user permissions
        if current_user.role not in ['issuer', 'admin']:
            logger.warning(f"User {current_user.username} with role {current_user.role} attempted payment")
            raise HTTPException(
                status_code=403, 
                detail="Only issuers and admins can process payments"
            )
        
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
        
        # Validate certificate exists and is pending
        certificate = db.query(Certificate).filter(
            Certificate.reference_number == payment_request.certificate_reference
        ).first()
        
        if not certificate:
            logger.error(f"Certificate not found: {payment_request.certificate_reference}")
            raise HTTPException(
                status_code=404, 
                detail=f"Certificate {payment_request.certificate_reference} not found"
            )
        
        # Check if payment already exists for this certificate
        existing_payment = db.query(Payment).filter(
            Payment.reference == payment_request.certificate_reference,
            Payment.status.in_(['confirmed', 'processing'])
        ).first()
        
        if existing_payment:
            logger.warning(f"Payment already exists for certificate {payment_request.certificate_reference}")
            return PaymentResponse(
                success=True,
                transaction_id=existing_payment.mpesa_transaction_id,
                conversation_id=existing_payment.mpesa_conversation_id,
                response_code=existing_payment.mpesa_response_code,
                response_message="Payment already processed",
                amount_paid=existing_payment.amount,
                currency="LSL",
                metadata={
                    'existing_payment': True,
                    'payment_id': existing_payment.id,
                    'status': existing_payment.status
                }
            )
        
        # Create payment record (pending)
        payment_record = Payment(
            verification_request_id=None,
            payer_user_id=current_user.id,
            method="mpesa_b2b",
            reference=payment_request.certificate_reference,
            amount=float(payment_request.amount) / 100,  # Convert from cents to LSL
            currency="LSL",
            status=PaymentStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={
                'university_code': payment_request.university_code,
                'university_name': university.name,
                'certificate_reference': payment_request.certificate_reference,
                'requested_by': current_user.username,
                'requested_at': datetime.utcnow().isoformat()
            }
        )
        
        db.add(payment_record)
        db.commit()
        db.refresh(payment_record)
        
        # Process REAL payment via M-Pesa
        logger.info(f"Calling M-Pesa API for payment {payment_record.id}")
        
        response = mpesa_client.b2b_payment(
            university_code=payment_request.university_code,
            amount=payment_request.amount,
            certificate_reference=payment_request.certificate_reference,
            description=payment_request.description or f"Certificate verification - {payment_request.certificate_reference}"
        )
        
        # Check payment result
        is_successful = mpesa_client.is_payment_successful(response)
        response_message = mpesa_client.get_response_message(response)
        
        # Update payment record with M-Pesa response
        payment_record.mpesa_transaction_id = response.get('output_TransactionID')
        payment_record.mpesa_conversation_id = response.get('output_ConversationID')
        payment_record.mpesa_response_code = response.get('output_ResponseCode')
        payment_record.mpesa_response_description = response_message
        payment_record.payment_metadata = {
            **(payment_record.payment_metadata or {}),
            'mpesa_response': response,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        if is_successful:
            payment_record.status = PaymentStatus.CONFIRMED
            payment_record.confirmed_at = datetime.utcnow()
            
            # Update certificate status
            certificate.payment_status = "paid"
            certificate.verification_status = "processing"
            certificate.paid_at = datetime.utcnow()
            
            # Create verification request in background
            background_tasks.add_task(
                create_verification_request,
                certificate.id,
                current_user.id,
                payment_record.id
            )
            
            logger.info(f"Payment {payment_record.id} confirmed successfully")
        else:
            payment_record.status = PaymentStatus.FAILED
            payment_record.failure_reason = response_message
            logger.warning(f"Payment {payment_record.id} failed: {response_message}")
        
        db.commit()
        
        # Prepare response
        amount_paid = float(payment_request.amount) / 100 if is_successful else None
        
        return PaymentResponse(
            success=is_successful,
            transaction_id=payment_record.mpesa_transaction_id,
            conversation_id=payment_record.mpesa_conversation_id,
            response_code=payment_record.mpesa_response_code,
            response_message=response_message,
            amount_paid=amount_paid,
            currency="LSL",
            metadata={
                'payment_id': payment_record.id,
                'certificate_reference': payment_request.certificate_reference,
                'university': payment_request.university_code,
                'status': payment_record.status,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"M-Pesa payment processing failed: {str(e)}"
        )

@router.post("/query-transaction", response_model=TransactionStatusResponse)
async def query_transaction_status(
    transaction_request: TransactionStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query M-Pesa transaction status
    """
    try:
        logger.info(f"Transaction query from {current_user.username}: {transaction_request.transaction_reference}")
        
        # Validate user permissions
        if current_user.role not in ['issuer', 'admin', 'verifier']:
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions to query transactions"
            )
        
        # Find payment in database
        payment = db.query(Payment).filter(
            (Payment.mpesa_transaction_id == transaction_request.transaction_reference) |
            (Payment.reference == transaction_request.transaction_reference)
        ).first()
        
        if not payment:
            logger.warning(f"Transaction not found: {transaction_request.transaction_reference}")
            return TransactionStatusResponse(
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
        
        # Query M-Pesa for real-time status
        if payment.mpesa_transaction_id:
            try:
                mpesa_status = mpesa_client.query_transaction(payment.mpesa_transaction_id)
                
                # Update payment status if changed
                if mpesa_client.is_payment_successful(mpesa_status) and payment.status == PaymentStatus.PENDING:
                    payment.status = PaymentStatus.CONFIRMED
                    payment.confirmed_at = datetime.utcnow()
                    db.commit()
            except Exception as e:
                logger.error(f"M-Pesa query failed: {str(e)}")
                # Continue with database status if M-Pesa query fails
        
        return TransactionStatusResponse(
            success=True,
            status=payment.status,
            amount=str(int(payment.amount * 100)),  # Convert to cents
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
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment history with filters
    """
    try:
        # Base query
        query = db.query(Payment).filter(Payment.payer_user_id == current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Payment.status == status)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Payment.created_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Payment.created_at <= end)
        
        # Count total
        total_count = query.count()
        
        # Paginate
        payments = query.order_by(Payment.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        # Get university names for certificates
        payment_items = []
        for payment in payments:
            # Get certificate and university info
            certificate = db.query(Certificate).filter(
                Certificate.reference_number == payment.reference
            ).first()
            
            university_name = None
            if certificate and certificate.university_id:
                university = db.query(University).filter(
                    University.id == certificate.university_id
                ).first()
                university_name = university.name if university else None
            
            payment_items.append(PaymentHistoryItem(
                id=payment.id,
                amount=payment.amount,
                currency=payment.currency or "LSL",
                method=payment.method,
                reference=payment.reference,
                certificate_reference=payment.reference,
                status=payment.status,
                transaction_id=payment.mpesa_transaction_id,
                conversation_id=payment.mpesa_conversation_id,
                response_code=payment.mpesa_response_code,
                response_message=payment.mpesa_response_description,
                created_at=payment.created_at.isoformat(),
                confirmed_at=payment.confirmed_at.isoformat() if payment.confirmed_at else None,
                university_name=university_name
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

@router.get("/mpesa-status", response_model=MpesaStatusResponse)
async def get_mpesa_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get M-Pesa system status and configuration
    """
    try:
        # Test session generation
        session_status = "operational"
        session_error = None
        
        try:
            session = mpesa_client.generate_session()
            if not session:
                session_status = "failed"
                session_error = "Failed to generate session"
        except Exception as e:
            session_status = "error"
            session_error = str(e)
        
        return MpesaStatusResponse(
            mpesa_available=session_status == "operational",
            session_status=session_status,
            session_error=session_error,
            configuration={
                "service_provider_code": mpesa_client.service_provider_code,
                "ecol_code": mpesa_client.ecol_code,
                "country": mpesa_client.country,
                "currency": mpesa_client.currency,
                "minimum_amount": "500 cents (M5.00)",
                "environment": "production" if "openapi.m-pesa.com" in mpesa_client.api_url else "sandbox"
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
            session_error=str(e),
            configuration={},
            user_permissions={
                "can_process_payments": False,
                "can_query_transactions": False,
                "role": current_user.role
            },
            supported_operations={}
        )

@router.post("/webhook")
async def payment_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for M-Pesa payment notifications
    """
    try:
        logger.info(f"Received M-Pesa webhook: {json.dumps(payload)[:200]}...")
        
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
        is_successful = mpesa_client.is_payment_successful(payload)
        
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
                certificate.verification_status = "processing"
                certificate.paid_at = datetime.utcnow()
                
                # Create verification request
                background_tasks.add_task(
                    create_verification_request,
                    certificate.id,
                    payment.payer_user_id,
                    payment.id
                )
        
        elif not is_successful:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = response_desc or "Failed via webhook"
        
        payment.payment_metadata = {
            **(payment.payment_metadata or {}),
            'webhook_received_at': datetime.utcnow().isoformat(),
            'webhook_payload': payload
        }
        
        db.commit()
        logger.info(f"Payment {payment.id} updated via webhook: {payment.status}")
        
        return JSONResponse(status_code=200, content={"message": "Webhook processed successfully"})
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"message": f"Webhook processing failed: {str(e)}"})

@router.post("/test-payment")
async def test_payment_integration(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Test M-Pesa integration with a small amount (admin only)
    """
    try:
        logger.info(f"Test payment requested by admin: {current_user.username}")
        
        # Use test amount (M1.00 = 100 cents)
        test_amount = "100"
        test_ref = f"TEST-{uuid.uuid4().hex[:8].upper()}"
        
        # Process test payment
        response = mpesa_client.b2b_payment(
            university_code="TEST001",
            amount=test_amount,
            certificate_reference=test_ref,
            description="Test payment integration"
        )
        
        # Log test result
        background_tasks.add_task(
            log_test_result,
            test_ref,
            response,
            current_user.id
        )
        
        return {
            "success": mpesa_client.is_payment_successful(response),
            "test_reference": test_ref,
            "response": {
                "code": response.get('output_ResponseCode'),
                "description": response.get('output_ResponseDesc'),
                "transaction_id": response.get('output_TransactionID'),
                "conversation_id": response.get('output_ConversationID')
            },
            "message": mpesa_client.get_response_message(response)
        }
        
    except Exception as e:
        logger.error(f"Test payment failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Test payment failed: {str(e)}"
        )

# Background task functions
async def create_verification_request(certificate_id: int, user_id: int, payment_id: int):
    """
    Create verification request after successful payment
    """
    try:
        # Import here to avoid circular imports
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
                created_at=datetime.utcnow()
            )
            
            db.add(verification)
            db.commit()
            
            logger.info(f"Verification request created for certificate {certificate_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to create verification request: {str(e)}")

async def log_test_result(reference: str, response: Dict[str, Any], user_id: int):
    """
    Log test payment results
    """
    try:
        # Implement test logging (to file or database)
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'reference': reference,
            'response_code': response.get('output_ResponseCode'),
            'response_desc': response.get('output_ResponseDesc'),
            'transaction_id': response.get('output_TransactionID'),
            'user_id': user_id,
            'success': mpesa_client.is_payment_successful(response)
        }
        
        # Log to file
        with open('test_payments.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    except Exception as e:
        logger.error(f"Failed to log test result: {str(e)}")

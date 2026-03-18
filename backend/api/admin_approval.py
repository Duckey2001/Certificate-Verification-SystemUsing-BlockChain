#!/usr/bin/env python3
"""
Admin approval endpoints for managing institution users, payments, and network access
Integrated with user management, payment tracking, and M-Pesa transactions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

from models import User, Payment, LoginActivity, Institution, VerificationLog, Certificate
from database import get_db
from auth import get_current_user, require_admin
import uuid

router = APIRouter(prefix="/api/admin", tags=["admin-approval"])

# Pydantic models for request/response validation
class UserApprovalRequest(BaseModel):
    user_id: str
    approve: bool
    role: Optional[str] = None  # Can override role during approval
    institution_code: Optional[str] = None
    rejection_reason: Optional[str] = None

class UserUpdateRequest(BaseModel):
    user_id: str
    role: Optional[str] = None
    institution_code: Optional[str] = None
    is_active: Optional[bool] = None

class DateRangeRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class PendingUserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    institution_code: Optional[str]
    institution_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    login_count: Optional[int] = 0
    google_id: Optional[str]
    github_id: Optional[str]

class PaymentSummaryResponse(BaseModel):
    id: str
    amount: float
    currency: str
    status: str
    method: str
    created_at: datetime
    confirmed_at: Optional[datetime]
    user_email: Optional[str]
    user_name: Optional[str]
    institution_code: Optional[str]
    mpesa_transaction_id: Optional[str]
    phone_number: Optional[str]

class PaymentStatsResponse(BaseModel):
    total_payments: int
    total_amount: float
    confirmed_payments: int
    confirmed_amount: float
    pending_payments: int
    failed_payments: int
    average_payment: float
    by_method: Dict[str, int]
    by_status: Dict[str, int]
    daily_totals: List[Dict[str, Any]]

class InstitutionStatsResponse(BaseModel):
    code: str
    name: str
    role: str
    total_users: int
    active_users: int
    pending_users: int
    total_payments: int
    total_payment_amount: float
    confirmed_payments: int
    confirmed_amount: float
    total_verifications: int
    successful_verifications: int

class LoginActivityResponse(BaseModel):
    id: str
    user_id: str
    username: str
    institution_code: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    location: Optional[str]
    status: str
    login_method: str
    created_at: datetime

class DashboardStatsResponse(BaseModel):
    total_users: int
    active_users_today: int
    pending_approvals: int
    total_institutions: int
    total_payments_today: float
    total_verifications_today: int
    recent_activities: List[Dict[str, Any]]
    system_health: Dict[str, Any]

# Helper functions
def is_admin(current_user: User) -> bool:
    """Check if current user is admin"""
    return current_user.role == "admin"

def get_user_stats(db: Session, user_id: str) -> Dict[str, Any]:
    """Get detailed stats for a specific user"""
    # Get login count
    login_count = db.query(func.count(LoginActivity.id)).filter(
        LoginActivity.user_id == user_id,
        LoginActivity.status == "success"
    ).scalar() or 0
    
    # Get payment stats
    payments = db.query(
        func.count(Payment.id).label('total_payments'),
        func.sum(Payment.amount).label('total_amount'),
        func.count(case([(Payment.status == 'CONFIRMED', Payment.id)])).label('confirmed_count'),
        func.sum(case([(Payment.status == 'CONFIRMED', Payment.amount)], else_=0)).label('confirmed_amount')
    ).filter(Payment.payer_user_id == user_id).first()
    
    # Get verification stats
    verification_count = db.query(func.count(VerificationLog.id)).filter(
        VerificationLog.verifier_code == db.query(User.institution_code).filter(User.id == user_id).scalar()
    ).scalar() or 0
    
    return {
        "login_count": login_count,
        "total_payments": payments[0] or 0,
        "total_payment_amount": float(payments[1] or 0),
        "confirmed_payments": payments[2] or 0,
        "confirmed_amount": float(payments[3] or 0),
        "verification_count": verification_count
    }

# Admin endpoints
@router.get("/system-stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get real system statistics from database"""
    try:
        # Get real user stats
        total_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        pending_users = db.query(func.count(User.id)).filter(User.role == "pending").scalar()
        
        # Get real certificate stats
        total_certificates = db.query(func.count(Certificate.id)).scalar()
        pending_certificates = db.query(func.count(Certificate.id)).filter(Certificate.status == "pending").scalar()
        
        # Get real verification stats
        total_verifications = db.query(func.count(VerificationLog.id)).scalar()
        valid_verifications = db.query(func.count(VerificationLog.id)).filter(VerificationLog.result == "valid").scalar()
        invalid_verifications = db.query(func.count(VerificationLog.id)).filter(VerificationLog.result == "invalid").scalar()
        
        # Get real payment stats
        total_payments = db.query(func.count(Payment.id)).scalar()
        confirmed_payments = db.query(func.count(Payment.id)).filter(Payment.status == "CONFIRMED").scalar()
        total_payment_amount = db.query(func.sum(Payment.amount)).filter(Payment.status == "CONFIRMED").scalar() or 0
        
        return {
            "total_users": total_users or 0,
            "total_certificates": total_certificates or 0,
            "total_verifications": total_verifications or 0,
            "total_payments": total_payments or 0,
            "total_payment_amount": float(total_payment_amount),
            "valid_verifications": valid_verifications or 0,
            "invalid_verifications": invalid_verifications or 0,
            "pending_users": pending_users or 0,
            "pending_certificates": pending_certificates or 0,
            "confirmed_payments": confirmed_payments or 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch system stats: {str(e)}"
        )

@router.get("/users")
def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    institution: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all users with filtering and pagination"""
    try:
        query = db.query(User).filter(User.is_active == True)
        
        if role and role != "all":
            query = query.filter(User.role == role)
        
        if institution:
            query = query.filter(User.institution_code == institution)
        
        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    User.username.ilike(search),
                    User.email.ilike(search),
                    User.institution_code.ilike(search)
                )
            )
        
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "institution_code": user.institution_code,
                    "is_active": user.is_active,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/certificates")
def get_all_certificates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all certificates with filtering and pagination"""
    try:
        query = db.query(Certificate)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Certificate.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Certificate.created_at <= end_dt)
        
        total = query.count()
        certificates = query.order_by(Certificate.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return {
            "certificates": [
                {
                    "id": cert.id,
                    "certificate_hash": cert.certificate_hash,
                    "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                    "student_id": cert.student_id,
                    "institution": cert.institution,
                    "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                    "status": cert.status,
                    "blockchain_tx_id": cert.blockchain_tx_id,
                    "blockchain_network": cert.blockchain_network,
                    "created_at": cert.created_at.isoformat()
                }
                for cert in certificates
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch certificates: {str(e)}"
        )

@router.get("/verifications")
def get_all_verifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all verification requests with filtering and pagination"""
    try:
        query = db.query(VerificationLog)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(VerificationLog.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(VerificationLog.created_at <= end_dt)
        
        total = query.count()
        verifications = query.order_by(VerificationLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return {
            "verifications": [
                {
                    "id": ver.id,
                    "verification_date": ver.created_at.isoformat(),
                    "certificate_hash": ver.certificate_hash,
                    "verifier_name": ver.verifier_name or "Unknown",
                    "verifier_id": ver.verifier_user_id,
                    "result": ver.result,
                    "blockchain_match": ver.blockchain_verified,
                    "payment_method": ver.payment_method,
                    "verification_fee": ver.verification_fee
                }
                for ver in verifications
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch verifications: {str(e)}"
        )

@router.get("/payments")
def get_all_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all payments with filtering and pagination"""
    try:
        query = db.query(Payment)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Payment.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Payment.created_at <= end_dt)
        
        total = query.count()
        payments = query.order_by(Payment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return {
            "payments": [
                {
                    "id": payment.id,
                    "created_at": payment.created_at.isoformat(),
                    "user_name": payment.payer_name or "Unknown",
                    "amount": float(payment.amount),
                    "method": payment.payment_method,
                    "reference": payment.transaction_reference,
                    "status": payment.status,
                    "mpesa_transaction_id": payment.mpesa_transaction_id
                }
                for payment in payments
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch payments: {str(e)}"
        )

@router.get("/system-logs")
def get_system_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system audit logs with pagination"""
    try:
        # Import AuditEvent model
        from models import AuditEvent
        
        query = db.query(AuditEvent)
        
        total = query.count()
        logs = query.order_by(AuditEvent.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "created_at": log.created_at.isoformat(),
                    "event_type": log.event_type,
                    "actor_user_id": log.actor_user_id,
                    "actor_role": log.actor_role,
                    "target_user_id": log.target_user_id,
                    "certificate_hash": log.certificate_hash,
                    "payload": log.payload
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch system logs: {str(e)}"
        )

@router.get("/pending-users", response_model=List[PendingUserResponse])
def get_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    institution: Optional[str] = Query(None, description="Filter by institution")
):
    """Get all users pending admin approval"""
    query = db.query(User).filter(User.role == "pending")
    
    if institution:
        query = query.filter(User.institution_code == institution)
    
    pending_users = query.order_by(User.created_at.desc()).all()
    
    result = []
    for user in pending_users:
        # Get institution name
        institution_name = None
        if user.institution_code:
            inst = db.query(Institution).filter(Institution.code == user.institution_code).first()
            institution_name = inst.name if inst else None
        
        # Get login count
        login_count = db.query(func.count(LoginActivity.id)).filter(
            LoginActivity.user_id == user.id,
            LoginActivity.status == "success"
        ).scalar() or 0
        
        result.append(PendingUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            institution_code=user.institution_code,
            institution_name=institution_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            login_count=login_count,
            google_id=user.google_id,
            github_id=user.github_id
        ))
    
    return result

@router.post("/approve-user")
def approve_user(
    request: UserApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Approve or reject a pending user"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user.role != "pending":
        raise HTTPException(
            status_code=400,
            detail="User is not pending approval"
        )
    
    old_role = user.role
    old_institution = user.institution_code
    
    if request.approve:
        # Approve the user
        new_role = request.role or "verifier"  # Default to verifier if not specified
        user.role = new_role
        if request.institution_code:
            user.institution_code = request.institution_code
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        # Create audit event
        audit = AuditEvent(
            id=str(uuid.uuid4()),
            event_type="user_approved",
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            target_user_id=user.id,
            payload={
                "old_role": old_role,
                "new_role": new_role,
                "old_institution": old_institution,
                "new_institution": user.institution_code,
                "email": user.email,
                "username": user.username
            },
            created_at=datetime.utcnow()
        )
        
        message = f"User {user.email} approved as {new_role}"
    else:
        # Reject the user (soft delete - mark as inactive)
        user.is_active = False
        user.role = "rejected"
        user.updated_at = datetime.utcnow()
        
        audit = AuditEvent(
            id=str(uuid.uuid4()),
            event_type="user_rejected",
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            target_user_id=user.id,
            payload={
                "old_role": old_role,
                "old_institution": old_institution,
                "email": user.email,
                "username": user.username,
                "reason": request.rejection_reason
            },
            created_at=datetime.utcnow()
        )
        
        message = f"User {user.email} rejected"
    
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": message,
        "user_id": user.id,
        "email": user.email,
        "approved": request.approve,
        "role": user.role,
        "institution_code": user.institution_code
    }

@router.post("/update-user")
def update_user(
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user details (role, institution, active status)"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user.role == "admin" and request.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot change admin role"
        )
    
    changes = {}
    
    if request.role and request.role != user.role:
        changes["old_role"] = user.role
        user.role = request.role
        changes["new_role"] = request.role
    
    if request.institution_code is not None and request.institution_code != user.institution_code:
        changes["old_institution"] = user.institution_code
        user.institution_code = request.institution_code
        changes["new_institution"] = request.institution_code
    
    if request.is_active is not None and request.is_active != user.is_active:
        changes["old_active"] = user.is_active
        user.is_active = request.is_active
        changes["new_active"] = request.is_active
    
    if changes:
        user.updated_at = datetime.utcnow()
        
        audit = AuditEvent(
            id=str(uuid.uuid4()),
            event_type="user_updated",
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            target_user_id=user.id,
            payload={
                **changes,
                "email": user.email,
                "username": user.username
            },
            created_at=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
    
    return {
        "success": True,
        "message": "User updated successfully",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "institution_code": user.institution_code,
        "is_active": user.is_active
    }

@router.get("/payments", response_model=List[PaymentSummaryResponse])
def get_all_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    status: Optional[str] = Query(None, description="Filter by payment status"),
    institution: Optional[str] = Query(None, description="Filter by institution"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all payments with filtering"""
    query = db.query(Payment)
    
    if status:
        query = query.filter(Payment.status == status.upper())
    
    if institution:
        query = query.filter(Payment.payee_institution_code == institution)
    
    if start_date:
        query = query.filter(Payment.created_at >= start_date)
    
    if end_date:
        query = query.filter(Payment.created_at <= end_date)
    
    payments = query.order_by(desc(Payment.created_at)).limit(limit).all()
    
    result = []
    for payment in payments:
        # Get user details
        user = db.query(User).filter(User.id == payment.payer_user_id).first()
        
        result.append(PaymentSummaryResponse(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            method=payment.method,
            created_at=payment.created_at,
            confirmed_at=payment.confirmed_at,
            user_email=user.email if user else None,
            user_name=user.username if user else None,
            institution_code=payment.payee_institution_code,
            mpesa_transaction_id=payment.mpesa_transaction_id,
            phone_number=payment.phone_number
        ))
    
    return result

@router.get("/payments/stats", response_model=PaymentStatsResponse)
def get_payment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    days: int = Query(30, ge=1, le=365)
):
    """Get payment statistics"""
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
    
    # Stats by status
    by_status = db.query(
        Payment.status,
        func.count(Payment.id).label('count')
    ).filter(Payment.created_at >= cutoff_date).group_by(Payment.status).all()
    
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
    confirmed_count = stats[2] or 0
    
    return PaymentStatsResponse(
        total_payments=total,
        total_amount=total_amount,
        confirmed_payments=confirmed_count,
        confirmed_amount=float(stats[3] or 0),
        pending_payments=stats[4] or 0,
        failed_payments=stats[5] or 0,
        average_payment=total_amount / total if total > 0 else 0,
        by_method={method: count for method, count in by_method},
        by_status={status: count for status, count in by_status},
        daily_totals=[
            {"date": date, "count": count, "amount": float(amount or 0)}
            for date, count, amount in daily_totals
        ]
    )

@router.get("/institutions/stats", response_model=List[InstitutionStatsResponse])
def get_institution_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get detailed statistics for all institutions"""
    institutions = db.query(Institution).all()
    
    result = []
    for inst in institutions:
        # User stats
        user_stats = db.query(
            func.count(User.id).label('total'),
            func.count(case([(User.is_active == True, User.id)])).label('active'),
            func.count(case([(User.role == 'pending', User.id)])).label('pending')
        ).filter(User.institution_code == inst.code).first()
        
        # Payment stats
        payment_stats = db.query(
            func.count(Payment.id).label('total'),
            func.sum(Payment.amount).label('total_amount'),
            func.count(case([(Payment.status == 'CONFIRMED', Payment.id)])).label('confirmed_count'),
            func.sum(case([(Payment.status == 'CONFIRMED', Payment.amount)], else_=0)).label('confirmed_amount')
        ).filter(Payment.payee_institution_code == inst.code).first()
        
        # Verification stats
        verification_stats = db.query(
            func.count(VerificationLog.id).label('total'),
            func.count(case([(VerificationLog.verified == True, VerificationLog.id)])).label('successful')
        ).filter(VerificationLog.verifier_code == inst.code).first()
        
        result.append(InstitutionStatsResponse(
            code=inst.code,
            name=inst.name,
            role=inst.role,
            total_users=user_stats[0] or 0,
            active_users=user_stats[1] or 0,
            pending_users=user_stats[2] or 0,
            total_payments=payment_stats[0] or 0,
            total_payment_amount=float(payment_stats[1] or 0),
            confirmed_payments=payment_stats[2] or 0,
            confirmed_amount=float(payment_stats[3] or 0),
            total_verifications=verification_stats[0] or 0,
            successful_verifications=verification_stats[1] or 0
        ))
    
    return result

@router.get("/login-activity", response_model=List[LoginActivityResponse])
def get_login_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status (success/failed)")
):
    """Get recent login activity"""
    query = db.query(
        LoginActivity,
        User.username
    ).join(User, LoginActivity.user_id == User.id)
    
    if status:
        query = query.filter(LoginActivity.status == status)
    
    activities = query.order_by(desc(LoginActivity.created_at)).limit(limit).all()
    
    return [
        LoginActivityResponse(
            id=activity[0].id,
            user_id=activity[0].user_id,
            username=activity[1],
            institution_code=activity[0].institution_code,
            ip_address=activity[0].ip_address,
            user_agent=activity[0].user_agent,
            location=activity[0].location,
            status=activity[0].status,
            login_method=activity[0].login_method,
            created_at=activity[0].created_at
        )
        for activity in activities
    ]

@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive dashboard statistics"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # User stats
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    active_users_today = db.query(func.count(func.distinct(LoginActivity.user_id))).filter(
        LoginActivity.created_at >= today_start,
        LoginActivity.created_at <= today_end,
        LoginActivity.status == "success"
    ).scalar() or 0
    
    pending_approvals = db.query(func.count(User.id)).filter(
        User.role == "pending"
    ).scalar() or 0
    
    # Institution stats
    total_institutions = db.query(func.count(Institution.id)).scalar() or 0
    
    # Payment stats today
    payments_today = db.query(func.sum(Payment.amount)).filter(
        Payment.created_at >= today_start,
        Payment.created_at <= today_end,
        Payment.status == "CONFIRMED"
    ).scalar() or 0
    
    # Verification stats today
    verifications_today = db.query(func.count(VerificationLog.id)).filter(
        VerificationLog.created_at >= today_start,
        VerificationLog.created_at <= today_end
    ).scalar() or 0
    
    # Recent activities
    recent_activities = []
    
    # Recent user registrations
    new_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
    for user in new_users:
        recent_activities.append({
            "type": "user_registered",
            "description": f"New user registered: {user.username}",
            "user": user.username,
            "timestamp": user.created_at
        })
    
    # Recent payments
    recent_payments = db.query(Payment).order_by(desc(Payment.created_at)).limit(5).all()
    for payment in recent_payments:
        user = db.query(User).filter(User.id == payment.payer_user_id).first()
        recent_activities.append({
            "type": "payment",
            "description": f"Payment of M{payment.amount} from {user.username if user else 'Unknown'}",
            "amount": payment.amount,
            "status": payment.status,
            "timestamp": payment.created_at
        })
    
    # Recent verifications
    recent_verifications = db.query(VerificationLog).order_by(desc(VerificationLog.created_at)).limit(5).all()
    for verif in recent_verifications:
        recent_activities.append({
            "type": "verification",
            "description": f"Certificate verification by {verif.verifier_code}",
            "result": "Success" if verif.verified else "Failed",
            "timestamp": verif.created_at
        })
    
    # Sort recent activities by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activities = recent_activities[:10]
    
    # System health
    system_health = {
        "database": "connected",
        "payment_gateway": "operational" if self._check_payment_gateway() else "degraded",
        "ocr_service": "operational" if self._check_ocr_service() else "degraded",
        "last_backup": None,  # Would be fetched from backup system
        "error_rate": self._calculate_error_rate(db)
    }
    
    return DashboardStatsResponse(
        total_users=total_users,
        active_users_today=active_users_today,
        pending_approvals=pending_approvals,
        total_institutions=total_institutions,
        total_payments_today=float(payments_today),
        total_verifications_today=verifications_today,
        recent_activities=recent_activities,
        system_health=system_health
    )

@router.post("/revoke-user-access")
def revoke_user_access(
    user_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Revoke access from a user (deactivate account)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke admin access"
        )
    
    old_role = user.role
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    # Invalidate all user sessions
    db.query(Session).filter(Session.user_id == user.id).delete()
    
    # Create audit event
    audit = AuditEvent(
        id=str(uuid.uuid4()),
        event_type="user_access_revoked",
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        target_user_id=user.id,
        payload={
            "old_role": old_role,
            "institution": user.institution_code,
            "email": user.email,
            "username": user.username,
            "reason": reason
        },
        created_at=datetime.utcnow()
    )
    
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": f"Access revoked for user {user.email}",
        "user_id": user.id,
        "old_role": old_role,
        "is_active": user.is_active
    }

@router.get("/export/payments")
def export_payments_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Export payments data as CSV"""
    query = db.query(Payment)
    
    if start_date:
        query = query.filter(Payment.created_at >= start_date)
    if end_date:
        query = query.filter(Payment.created_at <= end_date)
    
    payments = query.order_by(Payment.created_at).all()
    
    # Generate CSV
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Payment ID", "Date", "Amount", "Currency", "Status", "Method",
        "User ID", "Institution", "M-Pesa Transaction ID", "Phone Number",
        "Confirmed At"
    ])
    
    # Write data
    for payment in payments:
        user = db.query(User).filter(User.id == payment.payer_user_id).first()
        writer.writerow([
            payment.id,
            payment.created_at.isoformat(),
            payment.amount,
            payment.currency,
            payment.status,
            payment.method,
            user.username if user else "Unknown",
            payment.payee_institution_code or "N/A",
            payment.mpesa_transaction_id or "N/A",
            payment.phone_number or "N/A",
            payment.confirmed_at.isoformat() if payment.confirmed_at else "N/A"
        ])
    
    # Return CSV
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=payments_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# Helper methods for system health checks
def _check_payment_gateway(self) -> bool:
    """Check if payment gateway is operational"""
    try:
        # Implement actual payment gateway health check
        return True
    except:
        return False

def _check_ocr_service(self) -> bool:
    """Check if OCR service is operational"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except:
        return False

def _calculate_error_rate(self, db: Session, minutes: int = 60) -> float:
    """Calculate error rate for last X minutes"""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    
    total = db.query(func.count(LoginActivity.id)).filter(
        LoginActivity.created_at >= cutoff
    ).scalar() or 0
    
    errors = db.query(func.count(LoginActivity.id)).filter(
        LoginActivity.created_at >= cutoff,
        LoginActivity.status == "failed"
    ).scalar() or 0
    
    if total == 0:
        return 0.0
    
    return (errors / total) * 100
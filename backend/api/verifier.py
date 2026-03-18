from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from jose import jwt, JWTError
import os

from database import get_db
from models import User, Certificate, VerificationRequest, Payment, Institution
from fastapi.security import OAuth2PasswordBearer
from auth import get_current_user

router = APIRouter(prefix="/api/verifier", tags=["verifier"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Helper function to get current user
async def get_current_verifier(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current verifier user from token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "certivert-dev-secret")
        ALGORITHM = "HS256"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        
        # Check if user has verifier role
        if user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        return user
    except JWTError:
        raise credentials_exception

# Pydantic models
class VerificationStatsResponse(BaseModel):
    total_verifications: int
    pending_verifications: int
    completed_today: int
    success_rate: float
    average_time: float

class PendingVerificationResponse(BaseModel):
    id: int
    certificate_hash: str
    student_name: str
    student_surname: str
    examination_year: int
    institution: Optional[str] = None
    requested_at: str
    status: str

class VerificationDetailResponse(BaseModel):
    id: int
    certificate_id: int
    certificate_hash: str
    student_name: str
    student_surname: str
    examination_year: int
    subjects: List[Dict[str, Any]]
    issuer_name: str
    issuer_institution: Optional[str] = None
    requested_at: str
    status: str
    payment_status: str
    payment_amount: float

class VerificationActionRequest(BaseModel):
    action: str  # approve, reject, flag
    notes: Optional[str] = None

# API Endpoints with authentication
@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Verifier endpoint working", "status": "ok"}

@router.get("/stats")
async def get_verifier_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verification statistics for verifier dashboard"""
    try:
        # Check if user is verifier
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Return mock data for now to avoid database issues
        return {
            "total_verifications": 0,
            "pending_verifications": 0,
            "completed_today": 0,
            "success_rate": 0.0,
            "average_time": 0.0
        }
    except Exception as e:
        print(f"Error fetching verifier stats: {e}")
        return {
            "total_verifications": 0,
            "pending_verifications": 0,
            "completed_today": 0,
            "success_rate": 0,
            "average_time": 0
        }

@router.get("/verifier-stats", response_model=VerificationStatsResponse)
async def get_verifier_stats_alt(
    current_user: User = Depends(get_current_verifier),
    db: Session = Depends(get_db)
):
    """Alternative route for verification statistics (for frontend compatibility)"""
    return await get_verifier_stats(current_user, db)

@router.get("/my-verifications")
async def get_my_verifications(
    current_user: User = Depends(get_current_verifier),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get verifications for the current verifier"""
    try:
        # If user is admin, show all verifications
        # If user is verifier, show only their assigned or unassigned ones
        query = db.query(VerificationRequest)
        
        if current_user.role == "verifier":
            query = query.filter(
                (VerificationRequest.verifier_id == current_user.id) | 
                (VerificationRequest.verifier_id.is_(None))
            )
        
        verifications = query.order_by(
            desc(VerificationRequest.created_at)
        ).offset(offset).limit(limit).all()
        
        result = []
        for v in verifications:
            certificate = db.query(Certificate).filter(
                Certificate.id == v.certificate_id
            ).first() if v.certificate_id else None
            
            result.append({
                "id": v.id,
                "certificate_hash": v.certificate_hash or (certificate.certificate_hash if certificate else "N/A"),
                "student_name": certificate.student_name if certificate else "Unknown",
                "student_surname": certificate.student_surname if certificate else "Unknown",
                "status": v.status,
                "result": v.result,
                "requested_at": v.created_at.isoformat() if v.created_at else None,
                "verified_at": v.verification_date.isoformat() if v.verification_date else None
            })
        
        return result
    except Exception as e:
        print(f"Error fetching verifications: {e}")
        return []

@router.get("/pending", response_model=List[PendingVerificationResponse])
async def get_pending_verifications(
    current_user: User = Depends(get_current_verifier),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get pending verifications"""
    try:
        pending = db.query(VerificationRequest).filter(
            VerificationRequest.status == "pending"
        ).order_by(desc(VerificationRequest.created_at)).limit(limit).all()
        
        result = []
        for req in pending:
            certificate = db.query(Certificate).filter(
                Certificate.id == req.certificate_id
            ).first() if req.certificate_id else None
            
            # Get institution name
            institution_name = None
            if certificate and certificate.institution_code:
                institution = db.query(Institution).filter(
                    Institution.code == certificate.institution_code
                ).first()
                institution_name = institution.name if institution else None
            
            result.append({
                "id": req.id,
                "certificate_hash": req.certificate_hash or (certificate.certificate_hash if certificate else "N/A"),
                "student_name": certificate.student_name if certificate else "Unknown",
                "student_surname": certificate.student_surname if certificate else "Unknown",
                "examination_year": certificate.examination_year if certificate else 0,
                "institution": institution_name,
                "requested_at": req.created_at.isoformat() if req.created_at else None,
                "status": req.status
            })
        
        return result
    except Exception as e:
        print(f"Error fetching pending verifications: {e}")
        return []

@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_verifications(
    current_user: User = Depends(get_current_verifier),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get recent verifications"""
    try:
        recent = db.query(VerificationRequest).filter(
            VerificationRequest.status == "completed"
        ).order_by(desc(VerificationRequest.verification_date)).limit(limit).all()
        
        result = []
        for req in recent:
            certificate = db.query(Certificate).filter(
                Certificate.id == req.certificate_id
            ).first() if req.certificate_id else None
            
            result.append({
                "id": req.id,
                "certificate_hash": req.certificate_hash or (certificate.certificate_hash if certificate else "N/A"),
                "student_name": certificate.student_name if certificate else "Unknown",
                "result": req.result,
                "verified_at": req.verification_date.isoformat() if req.verification_date else None
            })
        
        return result
    except Exception as e:
        print(f"Error fetching recent verifications: {e}")
        return []

@router.get("/details/{verification_id}", response_model=VerificationDetailResponse)
async def get_verification_details(
    verification_id: int,
    current_user: User = Depends(get_current_verifier),
    db: Session = Depends(get_db)
):
    """Get detailed information about a verification request"""
    try:
        req = db.query(VerificationRequest).filter(
            VerificationRequest.id == verification_id
        ).first()
        
        if not req:
            raise HTTPException(status_code=404, detail="Verification request not found")
        
        certificate = db.query(Certificate).filter(
            Certificate.id == req.certificate_id
        ).first() if req.certificate_id else None
        
        issuer = db.query(User).filter(
            User.id == certificate.issuer_id
        ).first() if certificate else None
        
        payment = db.query(Payment).filter(
            Payment.id == req.payment_id
        ).first() if req.payment_id else None
        
        # Get institution name
        institution_name = None
        if certificate and certificate.institution_code:
            institution = db.query(Institution).filter(
                Institution.code == certificate.institution_code
            ).first()
            institution_name = institution.name if institution else None
        
        return {
            "id": req.id,
            "certificate_id": certificate.id if certificate else 0,
            "certificate_hash": req.certificate_hash or (certificate.certificate_hash if certificate else "N/A"),
            "student_name": certificate.student_name if certificate else "Unknown",
            "student_surname": certificate.student_surname if certificate else "Unknown",
            "examination_year": certificate.examination_year if certificate else 0,
            "subjects": certificate.subjects if certificate else [],
            "issuer_name": issuer.username if issuer else "Unknown",
            "issuer_institution": issuer.institution if issuer else None,
            "requested_at": req.created_at.isoformat() if req.created_at else None,
            "status": req.status,
            "payment_status": payment.status if payment else "unknown",
            "payment_amount": float(payment.amount) if payment else 0.0
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching verification details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch verification details")

@router.post("/verify/{verification_id}")
async def process_verification(
    verification_id: int,
    action: VerificationActionRequest,
    current_user: User = Depends(get_current_verifier),
    db: Session = Depends(get_db)
):
    """Process a verification (approve/reject/flag)"""
    try:
        req = db.query(VerificationRequest).filter(
            VerificationRequest.id == verification_id
        ).first()
        
        if not req:
            raise HTTPException(status_code=404, detail="Verification request not found")
        
        # Update the request
        if action.action == "approve":
            req.status = "completed"
            req.result = "valid"
        elif action.action == "reject":
            req.status = "completed"
            req.result = "invalid"
        elif action.action == "flag":
            req.status = "flagged"
            req.result = "pending"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        req.verifier_id = current_user.id
        req.verification_date = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Verification {action.action}ed successfully",
            "verification_id": req.id,
            "result": req.result
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to process verification")

@router.get("/activity")
async def get_verifier_activity(
    current_user: User = Depends(get_current_verifier),
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get verifier activity for charts"""
    try:
        # Generate last N days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        labels = []
        verified_data = []
        flagged_data = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            start_dt = datetime.combine(current_date, datetime.min.time())
            end_dt = datetime.combine(next_date, datetime.min.time())
            
            verified = db.query(VerificationRequest).filter(
                VerificationRequest.verification_date >= start_dt,
                VerificationRequest.verification_date < end_dt,
                VerificationRequest.status == "completed",
                VerificationRequest.result == "valid"
            ).count()
            
            flagged = db.query(VerificationRequest).filter(
                VerificationRequest.verification_date >= start_dt,
                VerificationRequest.verification_date < end_dt,
                VerificationRequest.status == "flagged"
            ).count()
            
            labels.append(current_date.strftime("%b %d"))
            verified_data.append(verified)
            flagged_data.append(flagged)
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Verified",
                    "data": verified_data,
                    "backgroundColor": "rgba(16, 185, 129, 0.2)",
                    "borderColor": "rgb(16, 185, 129)"
                },
                {
                    "label": "Flagged",
                    "data": flagged_data,
                    "backgroundColor": "rgba(245, 158, 11, 0.2)",
                    "borderColor": "rgb(245, 158, 11)"
                }
            ]
        }
    except Exception as e:
        print(f"Error fetching verifier activity: {e}")
        return {"labels": [], "datasets": []}
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import json
import os

from database import get_db
from models import User, Certificate, VerificationRequest, Payment, Institution
from api.enhanced_auth import get_current_user_enhanced

router = APIRouter(prefix="/api/issuer", tags=["issuer"])

# Pydantic models
class IssuerStatsResponse(BaseModel):
    total_certificates: int
    issued_today: int
    issued_this_month: int
    pending_verifications: int
    verified_count: int
    revoked_count: int

class CertificateIssueRequest(BaseModel):
    student_id: str
    student_name: str
    student_surname: str
    examination_year: int
    subjects: List[Dict[str, Any]]
    credits: Optional[int] = None
    issue_date: str
    institution_code: Optional[str] = None

class CertificateResponse(BaseModel):
    id: int
    certificate_hash: str
    student_name: str
    student_surname: str
    examination_year: int
    issue_date: str
    status: str
    verification_status: str
    created_at: str

class CertificateDetailResponse(BaseModel):
    id: int
    certificate_hash: str
    student_id: str
    student_name: str
    student_surname: str
    examination_year: int
    subjects: List[Dict[str, Any]]
    credits: Optional[int]
    issue_date: str
    issuer_name: str
    issuer_institution: Optional[str]
    status: str
    verification_status: str
    blockchain_tx_id: Optional[str]
    created_at: str
    verification_requests: List[Dict[str, Any]]

# Helper function to generate certificate hash
def generate_certificate_hash(student_id, student_name, examination_year, issue_date):
    """Generate a unique hash for the certificate"""
    data = f"{student_id}:{student_name}:{examination_year}:{issue_date}:{uuid.uuid4()}"
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()

# API Endpoints
@router.get("/stats", response_model=IssuerStatsResponse)
async def get_issuer_stats(
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Get issuer statistics"""
    try:
        # Total certificates issued by this issuer
        total_certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).count()
        
        # Issued today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        issued_today = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id,
            Certificate.created_at >= today_start
        ).count()
        
        # Issued this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        issued_this_month = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id,
            Certificate.created_at >= month_start
        ).count()
        
        # Pending verifications for certificates issued by this issuer
        pending_verifications = db.query(VerificationRequest).join(
            Certificate, Certificate.id == VerificationRequest.certificate_id
        ).filter(
            Certificate.issuer_id == current_user.id,
            VerificationRequest.status == "pending"
        ).count()
        
        # Verified certificates
        verified_count = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id,
            Certificate.verification_status == "verified"
        ).count()
        
        # Revoked certificates
        revoked_count = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id,
            Certificate.status == "revoked"
        ).count()
        
        return {
            "total_certificates": total_certificates,
            "issued_today": issued_today,
            "issued_this_month": issued_this_month,
            "pending_verifications": pending_verifications,
            "verified_count": verified_count,
            "revoked_count": revoked_count
        }
    except Exception as e:
        print(f"Error fetching issuer stats: {e}")
        return {
            "total_certificates": 0,
            "issued_today": 0,
            "issued_this_month": 0,
            "pending_verifications": 0,
            "verified_count": 0,
            "revoked_count": 0
        }

@router.post("/certificates/issue", response_model=CertificateResponse)
async def issue_certificate(
    request: Request,
    certificate_data: CertificateIssueRequest,
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Issue a new certificate"""
    try:
        # Generate unique certificate hash
        certificate_hash = generate_certificate_hash(
            certificate_data.student_id,
            certificate_data.student_name,
            certificate_data.examination_year,
            certificate_data.issue_date
        )
        
        # Create certificate
        certificate = Certificate(
            certificate_hash=certificate_hash,
            student_id=certificate_data.student_id,
            student_name=certificate_data.student_name,
            student_surname=certificate_data.student_surname,
            examination_year=certificate_data.examination_year,
            subjects=certificate_data.subjects,
            credits=certificate_data.credits,
            issue_date=certificate_data.issue_date,
            issuer_id=current_user.id,
            status="active",
            verification_status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        
        # TODO: Add to blockchain
        # blockchain_tx_id = await add_to_blockchain(certificate)
        
        return {
            "id": certificate.id,
            "certificate_hash": certificate.certificate_hash,
            "student_name": certificate.student_name,
            "student_surname": certificate.student_surname,
            "examination_year": certificate.examination_year,
            "issue_date": certificate.issue_date,
            "status": certificate.status,
            "verification_status": certificate.verification_status,
            "created_at": certificate.created_at.isoformat()
        }
    except Exception as e:
        print(f"Error issuing certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to issue certificate")

@router.get("/certificates", response_model=List[CertificateResponse])
async def get_my_certificates(
    current_user: User = Depends(get_current_user_enhanced),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get certificates issued by this issuer"""
    try:
        certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).order_by(desc(Certificate.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for cert in certificates:
            result.append({
                "id": cert.id,
                "certificate_hash": cert.certificate_hash,
                "student_name": cert.student_name,
                "student_surname": cert.student_surname,
                "examination_year": cert.examination_year,
                "issue_date": cert.issue_date,
                "status": cert.status,
                "verification_status": cert.verification_status,
                "created_at": cert.created_at.isoformat() if cert.created_at else None
            })
        
        return result
    except Exception as e:
        print(f"Error fetching certificates: {e}")
        return []

@router.get("/certificates/{certificate_id}", response_model=CertificateDetailResponse)
async def get_certificate_detail(
    certificate_id: int,
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Get detailed certificate information"""
    try:
        certificate = db.query(Certificate).filter(
            Certificate.id == certificate_id,
            Certificate.issuer_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Get verification requests for this certificate
        verification_requests = db.query(VerificationRequest).filter(
            VerificationRequest.certificate_id == certificate.id
        ).order_by(desc(VerificationRequest.created_at)).all()
        
        verification_data = []
        for req in verification_requests:
            verification_data.append({
                "id": req.id,
                "status": req.status,
                "result": req.result,
                "requested_at": req.created_at.isoformat() if req.created_at else None,
                "verified_at": req.verification_date.isoformat() if req.verification_date else None
            })
        
        return {
            "id": certificate.id,
            "certificate_hash": certificate.certificate_hash,
            "student_id": certificate.student_id,
            "student_name": certificate.student_name,
            "student_surname": certificate.student_surname,
            "examination_year": certificate.examination_year,
            "subjects": certificate.subjects,
            "credits": certificate.credits,
            "issue_date": certificate.issue_date,
            "issuer_name": current_user.username,
            "issuer_institution": current_user.institution,
            "status": certificate.status,
            "verification_status": certificate.verification_status,
            "blockchain_tx_id": certificate.blockchain_tx_id,
            "created_at": certificate.created_at.isoformat() if certificate.created_at else None,
            "verification_requests": verification_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching certificate detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificate details")

@router.post("/certificates/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Revoke a certificate"""
    try:
        certificate = db.query(Certificate).filter(
            Certificate.id == certificate_id,
            Certificate.issuer_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        certificate.status = "revoked"
        certificate.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"status": "success", "message": "Certificate revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error revoking certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke certificate")

@router.get("/activity")
async def get_issuer_activity(
    current_user: User = Depends(get_current_user_enhanced),
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get issuer activity for charts"""
    try:
        # Generate last N days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        labels = []
        issued_data = []
        verified_data = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            start_dt = datetime.combine(current_date, datetime.min.time())
            end_dt = datetime.combine(next_date, datetime.min.time())
            
            issued = db.query(Certificate).filter(
                Certificate.issuer_id == current_user.id,
                Certificate.created_at >= start_dt,
                Certificate.created_at < end_dt
            ).count()
            
            verified = db.query(VerificationRequest).join(
                Certificate, Certificate.id == VerificationRequest.certificate_id
            ).filter(
                Certificate.issuer_id == current_user.id,
                VerificationRequest.verification_date >= start_dt,
                VerificationRequest.verification_date < end_dt
            ).count()
            
            labels.append(current_date.strftime("%b %d"))
            issued_data.append(issued)
            verified_data.append(verified)
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Certificates Issued",
                    "data": issued_data,
                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                    "borderColor": "rgb(59, 130, 246)"
                },
                {
                    "label": "Verifications",
                    "data": verified_data,
                    "backgroundColor": "rgba(16, 185, 129, 0.2)",
                    "borderColor": "rgb(16, 185, 129)"
                }
            ]
        }
    except Exception as e:
        print(f"Error fetching issuer activity: {e}")
        return {"labels": [], "datasets": []}

@router.get("/recent")
async def get_recent_activity(
    current_user: User = Depends(get_current_user_enhanced),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent issuer activity"""
    try:
        # Recent certificates issued
        recent_certs = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).order_by(desc(Certificate.created_at)).limit(limit).all()
        
        activity = []
        for cert in recent_certs:
            activity.append({
                "id": cert.id,
                "type": "certificate_issued",
                "title": f"Certificate issued to {cert.student_name} {cert.student_surname}",
                "description": f"Hash: {cert.certificate_hash[:16]}...",
                "timestamp": cert.created_at.isoformat() if cert.created_at else None,
                "status": cert.status
            })
        
        return activity
    except Exception as e:
        print(f"Error fetching recent activity: {e}")
        return []
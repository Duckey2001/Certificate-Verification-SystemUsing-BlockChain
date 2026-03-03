from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import re

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user, require_role, get_optional_user
from database import get_db
from models import AuditEvent, Certificate, Invitation, Payment, User, VerificationRequest, Institution
from certificate_processor import CertificateProcessor

router = APIRouter(prefix="/api", tags=["dashboards"])

# Pydantic models for request/response
class CertificateScanResponse(BaseModel):
    certificate_data: Dict[str, Any]
    certificate_hash: str
    validation: Dict[str, Any]
    display_html: Optional[str] = None

class CertificateDisplayResponse(BaseModel):
    id: str
    certificate_hash: str
    student_name: str
    student_id: str
    institution: str
    issue_date: str
    examination_year: str
    examination_session: str
    subjects: List[Dict[str, Any]]
    certificate_numbers: List[str]
    issuer_code: str
    display_html: str

# Helper function to generate LGCSE certificate HTML display
def generate_certificate_display(certificate_data: Dict[str, Any], certificate_hash: str) -> str:
    """Generate HTML display of LGCSE certificate for the sidebar"""
    
    # Format subjects table
    subjects_html = ""
    for subject_data in certificate_data.get("full_results", []):
        subject = subject_data.get("subject", "")
        grade = subject_data.get("grade", "")
        level = subject_data.get("level", "")
        subjects_html += f"""
        <tr>
            <td style="padding: 4px 8px; border-bottom: 1px solid #ddd;">{subject}</td>
            <td style="padding: 4px 8px; border-bottom: 1px solid #ddd; text-align: center;">{grade}</td>
            <td style="padding: 4px 8px; border-bottom: 1px solid #ddd; text-align: center;">{level}</td>
        </tr>
        """
    
    if not subjects_html:
        subjects_html = "<tr><td colspan='3' style='padding: 8px; text-align: center;'>No subjects found</td></tr>"
    
    # Format certificate numbers
    cert_numbers = certificate_data.get("certificate_numbers", [])
    cert_numbers_html = "<br>".join(cert_numbers) if cert_numbers else "N/A"
    
    # Generate HTML
    html = f"""
    <div style="font-family: 'Times New Roman', serif; background: #f9f5e9; border: 2px solid #8b4513; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="text-align: center; border-bottom: 2px solid #8b4513; padding-bottom: 10px; margin-bottom: 15px;">
            <h2 style="color: #8b4513; margin: 0; font-size: 24px;">LESOTHO GENERAL CERTIFICATE OF SECONDARY EDUCATION</h2>
            <h3 style="color: #666; margin: 5px 0 0; font-size: 18px;">(LGCSE)</h3>
            <div style="margin-top: 10px;">
                <img src="/static/ecol_logo.png" alt="ECOL Logo" style="max-width: 80px; height: auto;" onerror="this.style.display='none'">
            </div>
            <p style="margin: 5px 0 0; font-size: 14px; color: #555;">Examination Council of Lesotho</p>
        </div>
        
        <!-- Certificate Number Badge -->
        <div style="background: #8b4513; color: white; padding: 5px 10px; border-radius: 4px; display: inline-block; margin-bottom: 15px;">
            <strong>Certificate Number:</strong> {cert_numbers_html}
        </div>
        
        <!-- Student Details -->
        <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 15px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 30%; font-weight: bold;">Student Name:</td>
                    <td style="width: 70%;">{certificate_data.get('student_name', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Student/Candidate Number:</td>
                    <td>{certificate_data.get('student_number', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Date of Birth:</td>
                    <td>{certificate_data.get('date_of_birth', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Institution/School:</td>
                    <td>{certificate_data.get('institution', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Examination Session:</td>
                    <td>{certificate_data.get('examination_session', certificate_data.get('examination_year', 'N/A'))}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Date of Issue:</td>
                    <td>{certificate_data.get('date_of_issue', 'N/A')}</td>
                </tr>
            </table>
        </div>
        
        <!-- Results Table -->
        <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 15px;">
            <h4 style="margin-top: 0; color: #8b4513; border-bottom: 1px solid #8b4513; padding-bottom: 5px;">Subjects and Grades</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f0e6d2;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #8b4513;">Subject</th>
                        <th style="padding: 8px; text-align: center; border-bottom: 2px solid #8b4513;">Grade</th>
                        <th style="padding: 8px; text-align: center; border-bottom: 2px solid #8b4513;">Level</th>
                    </tr>
                </thead>
                <tbody>
                    {subjects_html}
                </tbody>
            </table>
            <p style="margin-top: 10px; font-size: 12px; color: #666;">
                <strong>Subjects Reported:</strong> {certificate_data.get('subjects_reported', len(certificate_data.get('grades', {})))}
            </p>
        </div>
        
        <!-- Verification Hash (Small) -->
        <div style="margin-top: 15px; font-size: 10px; color: #999; text-align: right; border-top: 1px dotted #ccc; padding-top: 5px;">
            Hash: {certificate_hash[:20]}...
        </div>
    </div>
    """
    
    return html

@router.post("/certificates/scan", response_model=CertificateScanResponse)
async def scan_certificate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Scan a certificate using OCR and auto-fill the form
    Returns extracted data and HTML display for the sidebar
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Initialize processor
    processor = CertificateProcessor(db, current_user)
    
    try:
        # Process the certificate
        result = await processor.process_certificate(file, current_user, db)
        
        # Generate HTML display for sidebar
        display_html = generate_certificate_display(
            result["certificate_data"], 
            result["certificate_hash"]
        )
        
        # Add display HTML to response
        result["display_html"] = display_html
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing certificate: {str(e)}"
        )

@router.post("/certificates/verify-and-fill")
async def verify_and_fill_certificate(
    file: UploadFile = File(...),
    form_data: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Scan certificate and return data ready to fill the certificate issuance form
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Initialize processor
    processor = CertificateProcessor(db, current_user)
    
    try:
        # Save uploaded file temporarily
        file_path, file_extension = await processor.process_uploaded_file(file)
        
        try:
            # Process for form filling
            form_data = processor.process_certificate_file(file_path, current_user)
            
            # Generate HTML display
            certificate_data = {
                "student_name": form_data["student_name"],
                "student_number": form_data["student_id"],
                "institution": form_data["institution"],
                "date_of_issue": form_data["issue_date"],
                "examination_session": form_data["examination_session"],
                "examination_year": form_data["examination_year"],
                "grades": {subject: {"grade": "N/A"} for subject in form_data["subjects"]},
                "full_results": form_data["full_results"],
                "certificate_numbers": form_data["certificate_numbers"]
            }
            
            # Generate hash
            certificate_hash = processor.generate_certificate_hash(certificate_data)
            
            display_html = generate_certificate_display(certificate_data, certificate_hash)
            
            return {
                "success": True,
                "form_data": form_data,
                "display_html": display_html,
                "certificate_hash": certificate_hash,
                "message": "Certificate scanned successfully. Please review the extracted information."
            }
            
        finally:
            # Clean up
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing certificate: {str(e)}"
        )

@router.get("/certificates/display/{certificate_id}", response_model=CertificateDisplayResponse)
def get_certificate_display(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get certificate data with HTML display for sidebar"""
    
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Parse results JSON
    results = certificate.results_json if hasattr(certificate, 'results_json') else []
    if isinstance(results, str):
        try:
            results = json.loads(results)
        except:
            results = []
    
    # Format for display
    certificate_data = {
        "student_name": certificate.full_name,
        "student_number": certificate.candidate_number,
        "date_of_birth": certificate.date_of_birth,
        "institution": certificate.issuer_code,  # You might want to get institution name
        "examination_session": certificate.exam_session,
        "examination_year": re.search(r'\d{4}', certificate.exam_session).group(0) if re.search(r'\d{4}', certificate.exam_session) else "",
        "date_of_issue": certificate.date_of_issue,
        "grades": {item.get("subject", ""): {"grade": item.get("grade", "")} for item in results},
        "full_results": results,
        "certificate_numbers": [certificate.certificate_number]
    }
    
    # Generate HTML display
    display_html = generate_certificate_display(certificate_data, certificate.hash)
    
    return CertificateDisplayResponse(
        id=certificate.id,
        certificate_hash=certificate.hash,
        student_name=certificate.full_name,
        student_id=certificate.candidate_number,
        institution=certificate.issuer_code,
        issue_date=certificate.date_of_issue,
        examination_year=re.search(r'\d{4}', certificate.exam_session).group(0) if re.search(r'\d{4}', certificate.exam_session) else "",
        examination_session=certificate.exam_session,
        subjects=results,
        certificate_numbers=[certificate.certificate_number],
        issuer_code=certificate.issuer_code,
        display_html=display_html
    )

# Existing admin stats endpoints (updated with proper typing)
@router.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["admin"]))
):
    """Get admin dashboard statistics"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_certificates = db.query(func.count(Certificate.id)).scalar() or 0
    total_verifications = db.query(func.count(VerificationRequest.id)).scalar() or 0
    valid_verifications = db.query(func.count(VerificationRequest.id)).filter(
        VerificationRequest.result == "verified"
    ).scalar() or 0
    invalid_verifications = total_verifications - valid_verifications
    total_payments = db.query(func.count(Payment.id)).scalar() or 0
    total_payment_amount = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "CONFIRMED"
    ).scalar() or 0

    recent = (
        db.query(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "stats": {
            "total_users": total_users,
            "total_certificates": total_certificates,
            "total_verifications": total_verifications,
            "valid_verifications": valid_verifications,
            "invalid_verifications": invalid_verifications,
            "total_payments": total_payments,
            "total_payment_amount": float(total_payment_amount),
        },
        "recent_activity": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "actor_user_id": ev.actor_user_id,
                "actor_role": ev.actor_role,
                "certificate_hash": ev.certificate_hash,
                "verification_request_id": ev.verification_request_id,
                "payload": ev.payload,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
            }
            for ev in recent
        ],
    }

@router.get("/admin/audit-events")
def admin_audit_events(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["admin"])), 
    limit: int = 50
):
    """Get audit events for admin"""
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(min(limit, 200)).all()
    return [
        {
            "id": ev.id,
            "event_type": ev.event_type,
            "actor_user_id": ev.actor_user_id,
            "actor_role": ev.actor_role,
            "certificate_hash": ev.certificate_hash,
            "verification_request_id": ev.verification_request_id,
            "payload": ev.payload,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in events
    ]

@router.get("/admin/users")
def admin_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
    page: int = 1,
    limit: int = 20,
    role: Optional[str] = Query(None, description="Optional role filter: admin, issuer, verifier, pending"),
    institution: Optional[str] = Query(None, description="Optional institution filter (contains match)"),
    q: Optional[str] = Query(None, description="Free text search on username or email"),
):
    """Get users with filtering for admin"""
    offset = (page - 1) * limit
    limit = min(limit, 100)
    
    query = db.query(User)
    
    if role in ("admin", "issuer", "verifier", "pending"):
        query = query.filter(User.role == role)
    
    if institution:
        like_inst = f"%{institution}%"
        query = query.filter(User.institution_code.ilike(like_inst))
    
    if q:
        like_q = f"%{q}%"
        query = query.filter(
            (User.username.ilike(like_q)) | (User.email.ilike(like_q))
        )
    
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    total = query.with_entities(func.count(User.id)).scalar() or 0
    
    # Get institution names
    institutions = {inst.code: inst.name for inst in db.query(Institution).all()}
    
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "institution_code": u.institution_code,
                "institution_name": institutions.get(u.institution_code),
                "is_active": u.is_active,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }

class UpdateRoleRequest(BaseModel):
    role: str

@router.put("/admin/users/{user_id}/role")
def admin_update_user_role(
    user_id: str,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Update user role"""
    role = payload.role
    if role not in ("admin", "issuer", "verifier", "pending"):
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"id": user.id, "role": user.role}

@router.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Delete a user (soft delete by setting inactive)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"deleted": user_id, "message": "User deactivated"}

# Issuer endpoints
@router.get("/issuer/stats")
def issuer_stats(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["issuer", "admin"]))
):
    """Get issuer dashboard statistics"""
    q = db.query(Certificate).filter(Certificate.issuer_code == current_user.institution_code)
    total = q.count()
    verified = q.filter(Certificate.status == "verified").count()
    pending = q.filter(Certificate.status == "pending").count()

    return {"total": total, "verified": verified, "pending": pending}

@router.get("/issuer/certificates")
def issuer_certificates(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["issuer", "admin"])), 
    limit: int = 50
):
    """Get certificates issued by current issuer"""
    certs = (
        db.query(Certificate)
        .filter(Certificate.issuer_code == current_user.institution_code)
        .order_by(Certificate.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    
    return [
        {
            "id": c.id,
            "certificate_hash": c.hash,
            "student_name": c.full_name,
            "student_id": c.candidate_number,
            "certificate_number": c.certificate_number,
            "issue_date": c.date_of_issue,
            "exam_session": c.exam_session,
            "status": "verified" if c.verification_logs else "pending",
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in certs
    ]

# Verifier endpoints
@router.get("/verifier/stats")
def verifier_stats(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["verifier", "issuer", "admin"]))
):
    """Get verifier dashboard statistics"""
    q = db.query(VerificationRequest).filter(
        VerificationRequest.verifier_id == current_user.id
    )
    total = q.count()
    valid = q.filter(VerificationRequest.result == "verified").count()
    invalid = q.filter(VerificationRequest.result != "verified").count()
    
    total_fees = db.query(func.coalesce(func.sum(VerificationRequest.verification_fee), 0.0)).filter(
        VerificationRequest.verifier_id == current_user.id
    ).scalar()
    
    return {
        "total": total, 
        "valid": valid, 
        "invalid": invalid, 
        "total_fees": float(total_fees or 0.0)
    }

@router.get("/verifier/verifications")
def verifier_verifications(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["verifier", "issuer", "admin"])), 
    limit: int = 50
):
    """Get verification history for current verifier"""
    verifs = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.verifier_id == current_user.id)
        .order_by(VerificationRequest.verification_date.desc())
        .limit(min(limit, 200))
        .all()
    )
    
    return [
        {
            "id": v.id,
            "certificate_hash": v.certificate_hash,
            "result": v.result,
            "blockchain_match": v.blockchain_match,
            "payment_method": v.payment_method,
            "payment_status": v.payment_status,
            "verification_fee": v.verification_fee,
            "verification_date": v.verification_date.isoformat() if v.verification_date else None,
        }
        for v in verifs
    ]

# Compatibility endpoints for existing frontend
@router.get("/certificates/stats/{issuer_code}")
def certificates_stats_for_issuer(
    issuer_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "issuer"]))
):
    """Stats for a specific issuer by code"""
    if current_user.role != "admin" and current_user.institution_code != issuer_code:
        raise HTTPException(status_code=403, detail="Access denied")

    q = db.query(Certificate).filter(Certificate.issuer_code == issuer_code)
    total = q.count()
    verified = q.filter(Certificate.status == "verified").count()
    pending = q.filter(Certificate.status == "pending").count()

    return {"total": total, "verified": verified, "pending": pending}

@router.get("/issuers/{issuer_code}/certificates")
def issuer_certificates_by_code(
    issuer_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "issuer"])),
    page: int = 1,
    limit: int = 20,
):
    """Certificates for a specific issuer code"""
    if current_user.role != "admin" and current_user.institution_code != issuer_code:
        raise HTTPException(status_code=403, detail="Access denied")

    offset = (page - 1) * limit
    limit = min(limit, 100)

    q = (
        db.query(Certificate)
        .filter(Certificate.issuer_code == issuer_code)
        .order_by(Certificate.created_at.desc())
    )
    total = q.count()
    certs = q.offset(offset).limit(limit).all()

    return {
        "certificates": [
            {
                "id": c.id,
                "certificate_hash": c.hash,
                "student_name": c.full_name,
                "student_id": c.candidate_number,
                "certificate_number": c.certificate_number,
                "issue_date": c.date_of_issue,
                "exam_session": c.exam_session,
                "status": "verified" if c.verification_logs else "pending",
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in certs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }

@router.get("/verifiers/{verifier_id}/history")
def verifier_history_by_id(
    verifier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "verifier"])),
    page: int = 1,
    limit: int = 20,
):
    """Verification history for a specific verifier"""
    if current_user.role != "admin" and current_user.id != verifier_id:
        raise HTTPException(status_code=403, detail="Access denied")

    offset = (page - 1) * limit
    limit = min(limit, 100)

    q = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.verifier_id == verifier_id)
        .order_by(VerificationRequest.verification_date.desc())
    )
    total = q.count()
    verifs = q.offset(offset).limit(limit).all()

    return {
        "history": [
            {
                "id": v.id,
                "certificate_hash": v.certificate_hash,
                "result": v.result,
                "blockchain_match": v.blockchain_match,
                "payment_method": v.payment_method,
                "payment_status": v.payment_status,
                "verification_fee": v.verification_fee,
                "verification_date": v.verification_date.isoformat() if v.verification_date else None,
            }
            for v in verifs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }

# Admin Control Endpoints
@router.get("/admin/pending-users")
def admin_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get all users pending approval"""
    pending = db.query(User).filter(User.role == "pending").all()
    return {
        "pending_users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "institution": u.institution,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in pending
        ]
    }


@router.post("/admin/users/approve")
def admin_approve_user(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Approve or reject a pending user"""
    user_id = payload.get("user_id")
    approve = payload.get("approve", False)
    role = payload.get("role", "verifier")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if approve:
        user.role = role
        user.is_active = True
    else:
        db.delete(user)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"User {'approved' if approve else 'rejected'}",
        "user_id": user_id
    }


@router.post("/admin/certificates/{certificate_id}/revoke")
def admin_revoke_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Revoke a certificate"""
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    cert.revoked = True
    db.commit()
    
    audit = AuditEvent(
        event_type="certificate_revoked",
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        certificate_hash=cert.hash if hasattr(cert, 'hash') else str(certificate_id),
        payload={"reason": "Revoked by admin"},
        created_at=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "Certificate revoked",
        "certificate_id": certificate_id
    }


@router.get("/admin/logs")
def admin_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Get system audit logs"""
    offset = (page - 1) * limit
    
    total = db.query(func.count(AuditEvent.id)).scalar() or 0
    logs = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "actor_user_id": log.actor_user_id,
                "actor_role": log.actor_role,
                "certificate_hash": log.certificate_hash,
                "payload": log.payload,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit
    }

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from typing import List, Dict, Any, Optional
import os
import shutil
import uuid
from datetime import datetime, timedelta
from jose import jwt, JWTError

from models import Certificate, User, VerificationRequest, AuditEvent, Payment
from schemas import CertificateResponse
from certificate_processor import CertificateProcessor, OCRDependencyError
from enhanced_lgcse_processor import EnhancedLGCSEProcessor
from utils.blockchain_service import BlockchainService
from utils.enhanced_blockchain import store_certificate_on_blockchain, store_user_profile_on_blockchain
from utils.realtime_notifications import notification_service
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/certificates", tags=["certificates"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Helper function to get current user from token with debug logging
async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Debug: Print the token (first 20 chars only for security)
    print(f"🔑 Token received: {token[:20] if token else 'None'}...")
    print(f"🔑 Token length: {len(token) if token else 0}")
    
    if not token:
        print("❌ No token provided")
        raise credentials_exception
    
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "certivert-dev-secret")
        ALGORITHM = "HS256"
        print(f"🔐 Using SECRET_KEY: {SECRET_KEY[:10]}...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"📦 Payload: {payload}")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            print("❌ No user_id in payload")
            raise credentials_exception
            
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            print(f"❌ User not found for id: {user_id}")
            raise credentials_exception
            
        print(f"✅ User found: {user.username} (role: {user.role})")
        return user
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise credentials_exception

# ===== TEST AUTH ENDPOINT =====
@router.get("/test-auth")
async def test_auth(current_user: User = Depends(get_current_user_from_token)):
    """Test endpoint to verify authentication is working"""
    return {
        "message": "Authentication successful",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role
        }
    }

# ===== VERIFIER ENDPOINTS =====
@router.get("/verifier-stats")
async def get_verifier_stats(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get verifier statistics"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"📊 Fetching verifier stats for user: {current_user.username}")
        
        # Total verifications
        total_verifications = db.query(VerificationRequest).count()
        
        # Pending verifications
        pending_verifications = db.query(VerificationRequest).filter(
            VerificationRequest.status == "pending"
        ).count()
        
        # Completed today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        completed_today = db.query(VerificationRequest).filter(
            VerificationRequest.status == "completed",
            VerificationRequest.verification_date >= today_start
        ).count()
        
        # Success rate
        completed = db.query(VerificationRequest).filter(
            VerificationRequest.status == "completed"
        ).count()
        valid = db.query(VerificationRequest).filter(
            VerificationRequest.status == "completed",
            VerificationRequest.result == "valid"
        ).count()
        success_rate = (valid / completed * 100) if completed > 0 else 0
        
        # Average verification time (mock data for now)
        average_time = 2.5  # minutes
        
        return {
            "total_verifications": total_verifications,
            "pending_verifications": pending_verifications,
            "completed_today": completed_today,
            "success_rate": round(success_rate, 2),
            "average_time": average_time
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching verifier stats: {e}")
        return {
            "total_verifications": 0,
            "pending_verifications": 0,
            "completed_today": 0,
            "success_rate": 0,
            "average_time": 0
        }

@router.get("/my-verifications")
async def get_my_verifications(
    current_user: User = Depends(get_current_user_from_token),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get verifications assigned to current user"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"📋 Fetching verifications for user: {current_user.username}")
        
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
                Certificate.certificate_hash == v.certificate_hash
            ).first() if v.certificate_hash else None
            
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching verifications: {e}")
        return []

@router.get("/pending-verifications")
async def get_pending_verifications(
    current_user: User = Depends(get_current_user_from_token),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get pending verifications"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"⏳ Fetching pending verifications for user: {current_user.username}")
        
        pending = db.query(VerificationRequest).filter(
            VerificationRequest.status == "pending"
        ).order_by(desc(VerificationRequest.created_at)).limit(limit).all()
        
        result = []
        for req in pending:
            certificate = db.query(Certificate).filter(
                Certificate.certificate_hash == req.certificate_hash
            ).first() if req.certificate_hash else None
            
            result.append({
                "id": req.id,
                "certificate_hash": req.certificate_hash or (certificate.certificate_hash if certificate else "N/A"),
                "student_name": certificate.student_name if certificate else "Unknown",
                "student_surname": certificate.student_surname if certificate else "Unknown",
                "examination_year": certificate.examination_year if certificate else 0,
                "institution": certificate.institution if certificate else None,
                "requested_at": req.created_at.isoformat() if req.created_at else None,
                "status": req.status
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching pending verifications: {e}")
        return []

@router.get("/recent-verifications")
async def get_recent_verifications(
    current_user: User = Depends(get_current_user_from_token),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get recent verifications"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"🕒 Fetching recent verifications for user: {current_user.username}")
        
        recent = db.query(VerificationRequest).filter(
            VerificationRequest.status == "completed"
        ).order_by(desc(VerificationRequest.verification_date)).limit(limit).all()
        
        result = []
        for req in recent:
            certificate = db.query(Certificate).filter(
                Certificate.certificate_hash == req.certificate_hash
            ).first() if req.certificate_hash else None
            
            result.append({
                "id": req.id,
                "certificate_hash": req.certificate_hash or (certificate.certificate_hash if certificate else "N/A"),
                "student_name": certificate.student_name if certificate else "Unknown",
                "result": req.result,
                "verified_at": req.verification_date.isoformat() if req.verification_date else None
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching recent verifications: {e}")
        return []

@router.get("/verification-details/{verification_id}")
async def get_verification_details(
    verification_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get detailed information about a verification request"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"🔍 Fetching verification details for ID: {verification_id}")
        
        req = db.query(VerificationRequest).filter(
            VerificationRequest.id == verification_id
        ).first()
        
        if not req:
            raise HTTPException(status_code=404, detail="Verification request not found")
        
        certificate = db.query(Certificate).filter(
            Certificate.certificate_hash == req.certificate_hash
        ).first() if req.certificate_hash else None
        
        issuer = db.query(User).filter(
            User.id == certificate.issuer_id
        ).first() if certificate else None
        
        payment = db.query(Payment).filter(
            Payment.id == req.payment_id
        ).first() if req.payment_id else None
        
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
            "result": req.result,
            "payment_status": payment.status if payment else "unknown",
            "payment_amount": payment.amount if payment else 0.0
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching verification details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch verification details")

@router.post("/process-verification/{verification_id}")
async def process_verification(
    verification_id: int,
    action: str = Form(...),
    notes: str = Form(""),
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Process a verification (approve/reject/flag)"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"⚙️ Processing verification {verification_id} with action: {action}")
        
        req = db.query(VerificationRequest).filter(
            VerificationRequest.id == verification_id
        ).first()
        
        if not req:
            raise HTTPException(status_code=404, detail="Verification request not found")
        
        if action == "approve":
            req.status = "completed"
            req.result = "valid"
        elif action == "reject":
            req.status = "completed"
            req.result = "invalid"
        elif action == "flag":
            req.status = "flagged"
            req.result = "pending"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        req.verifier_id = current_user.id
        req.verification_date = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"status": "success", "message": f"Verification {action}ed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to process verification")

@router.get("/verifier-activity")
async def get_verifier_activity(
    current_user: User = Depends(get_current_user_from_token),
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get verifier activity for charts"""
    try:
        # Check if user has verifier role
        if current_user.role not in ["verifier", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions. Verifier role required."
            )
        
        print(f"📈 Fetching verifier activity for last {days} days")
        
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching verifier activity: {e}")
        return {"labels": [], "datasets": []}

# ===== OCR EXTRACTION ENDPOINT =====
@router.post("/extract-data")
async def extract_certificate_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extract data from certificate file using OCR"""
    if current_user.role not in {"issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only issuers can extract certificate data"
        )
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and image files (JPEG, PNG) are supported"
        )
    
    # Save temporary file
    temp_dir = "temp/ocr"
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Use Enhanced LGCSE Processor for better OCR accuracy
        try:
            enhanced_processor = EnhancedLGCSEProcessor()
            extracted_data = enhanced_processor.process_certificate_file_enhanced(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return {
                "success": True,
                "data": extracted_data
            }
        except Exception as enhanced_error:
            # Fallback to regular processor if enhanced fails
            try:
                processor = CertificateProcessor()
                extracted_data = processor.process_certificate_file(temp_path)
                
                # Clean up temp file
                os.remove(temp_path)
                
                return {
                    "success": True,
                    "data": extracted_data,
                    "warning": "Enhanced OCR failed, used fallback processor"
                }
            except Exception as fallback_error:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise HTTPException(
                    status_code=500,
                    detail=f"Both enhanced and fallback OCR failed: Enhanced - {str(enhanced_error)}, Fallback - {str(fallback_error)}"
                )
            
        except OCRDependencyError as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=400,
                detail=f"{e}. {e.hint}" if e.hint else str(e),
            )
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=500,
                detail=f"OCR processing failed: {str(e)}"
            )
            
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {str(e)}"
        )

# ===== CERTIFICATE ISSUANCE ENDPOINT =====
@router.post("/issue")
async def issue_certificate(
    student_name: str = Form(...),
    student_id: str = Form(...),
    institution: str = Form(...),
    issue_date: str = Form(...),
    expiry_date: str = Form(""),
    grade: str = Form(""),
    subjects: str = Form(""),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue a new certificate"""
    if current_user.role not in {"issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only issuers can issue certificates"
        )
    
    try:
        # Parse subjects
        subjects_list = []
        if subjects:
            try:
                subjects_list = [s.strip() for s in subjects.split(",") if s.strip()]
            except:
                subjects_list = []
        
        # Parse expiry date
        expiry_date_obj = None
        if expiry_date:
            try:
                expiry_date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Parse issue date
        try:
            issue_date_obj = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
        except:
            raise HTTPException(
                status_code=400,
                detail="Invalid issue date format"
            )
        
        # Create certificate record
        certificate = Certificate(
            student_name=student_name,
            student_surname="",  # Can be extracted from full name if needed
            student_id=student_id,
            institution=institution,
            issue_date=issue_date_obj,
            expiry_date=expiry_date_obj,
            grade=grade,
            subjects=subjects_list,
            issuer_id=current_user.id,
            status="issued",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        
        # Process file if provided
        if file:
            upload_dir = "uploads/certificates"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            certificate.file_path = file_path
            db.commit()
        
        # Generate blockchain hash and store on blockchain
        try:
            blockchain_service = BlockchainService()
            hash_result = blockchain_service.create_certificate_hash(certificate)
            certificate.certificate_hash = hash_result["hash"]
            db.commit()
            
            # Store certificate on blockchain
            blockchain_tx_hash = await store_certificate_on_blockchain(certificate.certificate_hash)
            if blockchain_tx_hash:
                certificate.blockchain_tx_id = blockchain_tx_hash
                certificate.blockchain_network = "hardhat"
                db.commit()
        except Exception as e:
            # Log error but don't fail the issuance
            print(f"Blockchain hash generation failed: {e}")
        
        # Update user statistics
        current_user.certificates_issued += 1
        current_user.last_activity_at = datetime.utcnow()
        db.commit()
        
        # Create audit event
        db.add(
            AuditEvent(
                event_type="certificate_issued",
                actor_user_id=current_user.id,
                actor_role=current_user.role,
                certificate_hash=certificate.certificate_hash,
                payload={
                    "student_name": student_name,
                    "student_id": student_id,
                    "institution": institution,
                    "blockchain_tx_hash": blockchain_tx_hash
                }
            )
        )
        db.commit()
        
        return {
            "success": True,
            "certificate_id": certificate.id,
            "certificate_hash": certificate.certificate_hash,
            "student_name": student_name,
            "student_id": student_id,
            "institution": institution,
            "issue_date": issue_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Certificate issuance failed: {str(e)}"
        )

# ===== ISSUER ENDPOINTS =====
@router.get("/issuer/stats")
async def get_issuer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for the current issuer"""
    if current_user.role not in {"issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only issuers can view stats"
        )
    
    try:
        # Get certificate counts
        total_certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).count()
        
        pending_certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id,
            Certificate.status == "pending"
        ).count()
        
        verified_certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id,
            Certificate.status == "verified"
        ).count()
        
        return {
            "total": total_certificates,
            "pending": pending_certificates,
            "verified": verified_certificates
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )

@router.get("/issuer/certificates")
async def get_issuer_certificates(
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get certificates for the current issuer"""
    if current_user.role not in {"issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only issuers can view certificates"
        )
    
    try:
        certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).order_by(Certificate.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": cert.id,
                "certificate_hash": cert.certificate_hash,
                "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                "student_id": cert.student_id,
                "institution": cert.institution,
                "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                "status": cert.status,
                "created_at": cert.created_at.isoformat()
            }
            for cert in certificates
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch certificates: {str(e)}"
        )

# ===== DEBUG ENDPOINTS =====
@router.get("/debug")
def debug_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check certificate data"""
    from database import engine
    from sqlalchemy import text
    
    try:
        # Try a raw SQL query to bypass any ORM issues
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM certificates"))
            count = result.scalar()
            
            certs = conn.execute(
                text("SELECT id, certificate_hash, student_name, student_surname, student_id FROM certificates LIMIT 5")
            ).fetchall()
            
            certificates = [
                {
                    "id": row[0],
                    "certificate_hash": row[1],
                    "student_name": f"{row[2]} {row[3]}",
                    "student_id": row[4]
                }
                for row in certs
            ]
            
            return {
                "total_count": count,
                "certificates": certificates,
                "message": "Using raw SQL query"
            }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Error accessing certificates table"
        }

@router.get("/debug-search")
def debug_search(
    q: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug version of search to see what's happening"""
    from database import engine
    from sqlalchemy import text
    
    try:
        # Try raw SQL search
        with engine.connect() as conn:
            if q:
                like = f"%{q}%"
                result = conn.execute(
                    text("""
                        SELECT id, certificate_hash, student_name, student_surname, student_id 
                        FROM certificates 
                        WHERE student_name ILIKE :like 
                           OR student_surname ILIKE :like 
                           OR student_id ILIKE :like
                           OR certificate_hash ILIKE :like
                    """),
                    {"like": like}
                ).fetchall()
                
                certificates = [
                    {
                        "id": row[0],
                        "certificate_hash": row[1],
                        "student_name": f"{row[2]} {row[3]}",
                        "student_id": row[4]
                    }
                    for row in result
                ]
                
                return {
                    "search_term": q,
                    "results_count": len(certificates),
                    "certificates": certificates,
                    "message": "Using raw SQL search"
                }
            else:
                # Return all certificates if no search term
                result = conn.execute(
                    text("SELECT id, certificate_hash, student_name, student_surname, student_id FROM certificates LIMIT 100")
                ).fetchall()
                
                certificates = [
                    {
                        "id": row[0],
                        "certificate_hash": row[1],
                        "student_name": f"{row[2]} {row[3]}",
                        "student_id": row[4]
                    }
                    for row in result
                ]
                
                return {
                    "search_term": q,
                    "results_count": len(certificates),
                    "certificates": certificates,
                    "message": "All certificates (no search term)"
                }
    except Exception as e:
        return {"error": str(e), "message": "Error in debug search"}

@router.get("/debug-search-raw")
def debug_search_raw(
    q: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug search that returns raw ORM results"""
    try:
        query = db.query(Certificate)
        
        if q:
            like = f"%{q}%"
            query = query.filter(
                (Certificate.certificate_hash.ilike(like)) |
                (Certificate.student_id.ilike(like)) |
                ((Certificate.student_name + ' ' + Certificate.student_surname).ilike(like))
            )
        
        results = query.limit(100).all()
        
        # Return raw data without any serialization
        return {
            "search_term": q,
            "count": len(results),
            "raw_results": [
                {
                    "id": r.id,
                    "certificate_hash": r.certificate_hash,
                    "student_name": r.student_name,
                    "student_surname": r.student_surname,
                    "student_id": r.student_id,
                    "examination_year": r.examination_year,
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e), "trace": str(e.__traceback__)}
# ==========================

def _allowed_certificate_extensions() -> set[str]:
    return {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'}

def _save_upload_to_disk(upload: UploadFile, upload_dir: str) -> tuple[str, str]:
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(upload.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return file_path, file_ext

def _create_certificate_from_enhanced_extracted(
    *,
    db: Session,
    current_user: User,
    file_path: str,
    certificate_data: Dict[str, Any],
    certificate_hash: str,
    validation_info: Dict[str, Any]
) -> Certificate:
    # Parse student name from enhanced extracted data
    student_name = certificate_data.get("student_name", "")
    name_parts = student_name.split()
    first_name = name_parts[0] if name_parts else ""
    surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    # Parse examination year
    examination_year = certificate_data.get("examination_year", "")
    if not examination_year:
        # Try to extract from examination session
        session = certificate_data.get("examination_session", "")
        if session:
            import re
            year_match = re.search(r'\b(20\d{2})\b', session)
            if year_match:
                examination_year = year_match.group(1)
    
    # Convert to integer if possible
    try:
        year = int(examination_year) if examination_year else 2023
    except:
        year = 2023

    # Parse subjects from enhanced data
    subjects = certificate_data.get("subjects", [])
    if isinstance(subjects, list):
        subjects_dict = {}
        for subject in subjects:
            if isinstance(subject, dict):
                subject_name = subject.get("subject_name", subject.get("subject", ""))
                grade = subject.get("grade", "")
                if subject_name and grade:
                    subjects_dict[subject_name] = {
                        "grade": grade,
                        "syllabus_code": subject.get("syllabus_code", ""),
                        "points": subject.get("points", 0),
                        "passed": subject.get("passed", True)
                    }
    else:
        subjects_dict = subjects if isinstance(subjects, dict) else {}
    
    # Calculate credits based on subjects
    credits = len(subjects_dict) * 5  # 5 credits per subject

    certificate = Certificate(
        certificate_hash=certificate_hash,
        student_id=certificate_data.get("student_id", ""),
        student_name=first_name,
        student_surname=surname,
        examination_year=year,
        subjects=subjects_dict,
        credits=credits,
        institution=certificate_data.get("institution", ""),
        issue_date=certificate_data.get("date_of_issue", ""),
        issuer_id=current_user.id,
        original_image_path=file_path,
        extracted_data={
            "enhanced_data": certificate_data,
            "validation": validation_info,
            "processing_method": "enhanced_ocr"
        },
        status="verified",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate

def _create_certificate_from_extracted(
    *,
    db: Session,
    current_user: User,
    file_path: str,
    certificate_data: Dict[str, Any],
) -> Certificate:
    # Parse student name into first name and surname
    student_name = certificate_data.get("student_name", "")
    name_parts = student_name.split()
    first_name = name_parts[0] if name_parts else ""
    surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    # Parse issue year
    issue_date = certificate_data.get("date_of_issue", "")
    year = 2023  # default
    if issue_date:
        import re
        year_match = re.search(r'\b(20\d{2})\b', issue_date)
        if year_match:
            year = int(year_match.group(1))

    certificate = Certificate(
        certificate_hash=certificate_data["certificate_hash"],
        student_id=certificate_data.get("student_number", ""),
        student_name=first_name,
        student_surname=surname,
        examination_year=year,
        subjects=certificate_data.get("grades", {}),
        credits=certificate_data.get("subjects_reported", 0) * 5,
        issue_date=issue_date,
        issuer_id=current_user.id,
        original_image_path=file_path,
        extracted_data=certificate_data,
        status="verified",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate

@router.post("/upload", response_model=CertificateResponse)
async def upload_certificate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process an LGCSE certificate (PDF or image)"""
    # Allow any authenticated user to upload for OCR processing
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Validate file type
    allowed_extensions = _allowed_certificate_extensions()
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    upload_dir = "uploads/certificates"
    file_path = None

    try:
        file_path, _ = _save_upload_to_disk(file, upload_dir)

        try:
            processor = CertificateProcessor()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize certificate processor: {str(e)}"
            )

        # Process certificate with Enhanced LGCSE Processor
        try:
            enhanced_processor = EnhancedLGCSEProcessor()
            enhanced_result = enhanced_processor.process_certificate_file_enhanced(file_path)
            
            # Extract data from enhanced result
            certificate_data = enhanced_result["extracted_fields"]
            certificate_hash = enhanced_result["certificate_hash"]
            validation_info = enhanced_result["validation"]
            
            # Check if certificate already exists
            existing_cert = db.query(Certificate).filter(
                Certificate.certificate_hash == certificate_hash
            ).first()
            
            if existing_cert:
                # Return existing certificate data instead of error
                return {
                    "id": existing_cert.id,
                    "certificate_hash": existing_cert.certificate_hash,
                    "student_id": existing_cert.student_id,
                    "student_name": existing_cert.student_name,
                    "student_surname": existing_cert.student_surname,
                    "examination_year": existing_cert.examination_year,
                    "subjects": existing_cert.subjects,
                    "credits": existing_cert.credits,
                    "issue_date": existing_cert.issue_date,
                    "issuer_id": existing_cert.issuer_id,
                    "status": existing_cert.status,
                    "created_at": existing_cert.created_at,
                    "updated_at": existing_cert.updated_at,
                    "blockchain_tx_id": existing_cert.blockchain_tx_id,
                    "blockchain_network": existing_cert.blockchain_network,
                    "blockchain_block_number": existing_cert.blockchain_block_number,
                    "extracted_data": existing_cert.extracted_data,
                    "validation": validation_info,
                    "message": "Certificate already exists in the system"
                }
            
            # Only store on blockchain if user is issuer or admin
            blockchain_result = None
            if current_user.role in ["admin", "issuer"]:
                try:
                    blockchain_service = BlockchainService()
                    blockchain_result = blockchain_service.store_hash_on_blockchain({
                        "certificate_hash": certificate_hash,
                        "certificate_data": certificate_data
                    })
                except Exception as e:
                    # Continue without blockchain if it fails
                    blockchain_result = {"success": False, "error": str(e)}
            
            # Create certificate from enhanced extracted data
            certificate = _create_certificate_from_enhanced_extracted(
                db=db,
                current_user=current_user,
                file_path=file_path,
                certificate_data=certificate_data,
                certificate_hash=certificate_hash,
                validation_info=validation_info
            )

            # Persist blockchain metadata if available
            if blockchain_result and blockchain_result.get("success"):
                certificate.blockchain_tx_id = blockchain_result.get("transaction_id")
                certificate.blockchain_network = blockchain_result.get("network")
                certificate.blockchain_block_number = blockchain_result.get("block_number")
            
            db.commit()

            db.add(
                AuditEvent(
                    event_type="certificate_uploaded",
                    actor_user_id=current_user.id,
                    actor_role=current_user.role,
                    certificate_hash=certificate.certificate_hash,
                    payload={
                        "tx_id": certificate.blockchain_tx_id,
                        "network": certificate.blockchain_network,
                        "validation": validation_info
                    },
                )
            )
            db.commit()
            
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
                "issuer_id": certificate.issuer_id,
                "status": certificate.status,
                "created_at": certificate.created_at,
                "updated_at": certificate.updated_at,
                "blockchain_tx_id": certificate.blockchain_tx_id,
                "blockchain_network": certificate.blockchain_network,
                "blockchain_block_number": certificate.blockchain_block_number,
                "extracted_data": certificate.extracted_data,
                "validation": validation_info,
                "message": "Certificate processed successfully with enhanced OCR"
            }
            
        except Exception as enhanced_error:
            # Fallback to regular processor if enhanced fails
            try:
                processor = CertificateProcessor()
                result = processor.process_certificate(file_path)
                certificate_data = result["certificate_data"]
                certificate_hash = result["certificate_hash"]
                validation_info = result["validation"]
                
                # Check if certificate already exists
                existing_cert = db.query(Certificate).filter(
                    Certificate.certificate_hash == certificate_hash
                ).first()
                
                if existing_cert:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return {
                        "id": existing_cert.id,
                        "certificate_hash": existing_cert.certificate_hash,
                        "student_id": existing_cert.student_id,
                        "student_name": existing_cert.student_name,
                        "student_surname": existing_cert.student_surname,
                        "examination_year": existing_cert.examination_year,
                        "subjects": existing_cert.subjects,
                        "credits": existing_cert.credits,
                        "issue_date": existing_cert.issue_date,
                        "issuer_id": existing_cert.issuer_id,
                        "status": existing_cert.status,
                        "created_at": existing_cert.created_at,
                        "updated_at": existing_cert.updated_at,
                        "blockchain_tx_id": existing_cert.blockchain_tx_id,
                        "blockchain_network": existing_cert.blockchain_network,
                        "blockchain_block_number": existing_cert.blockchain_block_number,
                        "extracted_data": existing_cert.extracted_data,
                        "validation": validation_info,
                        "message": "Certificate already exists in the system"
                    }
                
                # Only store on blockchain if user is issuer or admin
                blockchain_result = None
                if current_user.role in ["admin", "issuer"]:
                    try:
                        blockchain_service = BlockchainService()
                        blockchain_result = blockchain_service.store_hash_on_blockchain({
                            "certificate_hash": certificate_hash,
                            "certificate_data": certificate_data
                        })
                    except Exception as e:
                        # Continue without blockchain if it fails
                        blockchain_result = {"success": False, "error": str(e)}
                
                certificate = _create_certificate_from_extracted(
                    db=db,
                    current_user=current_user,
                    file_path=file_path,
                    certificate_data={
                        "certificate_hash": certificate_hash,
                        "certificate_data": certificate_data,
                        "validation": validation_info
                    },
                )

                # Persist blockchain metadata if available
                if blockchain_result and blockchain_result.get("success"):
                    certificate.blockchain_tx_id = blockchain_result.get("transaction_id")
                    certificate.blockchain_network = blockchain_result.get("network")
                    certificate.blockchain_block_number = blockchain_result.get("block_number")
                
                db.commit()

                db.add(
                    AuditEvent(
                        event_type="certificate_uploaded",
                        actor_user_id=current_user.id,
                        actor_role=current_user.role,
                        certificate_hash=certificate.certificate_hash,
                        payload={
                            "tx_id": certificate.blockchain_tx_id,
                            "network": certificate.blockchain_network,
                            "validation": validation_info
                        },
                    )
                )
                db.commit()
                
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
                    "issuer_id": certificate.issuer_id,
                    "status": certificate.status,
                    "created_at": certificate.created_at,
                    "updated_at": certificate.updated_at,
                    "blockchain_tx_id": certificate.blockchain_tx_id,
                    "blockchain_network": certificate.blockchain_network,
                    "blockchain_block_number": certificate.blockchain_block_number,
                    "extracted_data": certificate.extracted_data,
                    "validation": validation_info,
                    "message": "Certificate processed successfully with fallback OCR"
                }
                
            except HTTPException as e:
                # Re-raise HTTP exceptions from validation
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                raise e
            except Exception as fallback_error:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=500,
                    detail=f"Both enhanced and fallback OCR failed: Enhanced - {str(enhanced_error)}, Fallback - {str(fallback_error)}"
                )

    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/upload-bulk")
async def upload_certificates_bulk(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk upload and process certificates (PDF or image).

    Returns per-file results; one bad file won't fail the whole batch.
    """
    if current_user.role != "issuer":
        raise HTTPException(status_code=403, detail="Only issuers can upload certificates")

    allowed_extensions = _allowed_certificate_extensions()
    upload_dir = "uploads/certificates"

    try:
        enhanced_processor = EnhancedLGCSEProcessor()
    except OCRDependencyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"{e}. {e.hint}" if e.hint else str(e),
        )

    blockchain_service = BlockchainService()
    results: List[Dict[str, Any]] = []
    processing_stats = {
        "total_files": len(files),
        "enhanced_processed": 0,
        "fallback_processed": 0,
        "failed": 0,
        "duplicates": 0
    }

    for f in files:
        file_path = None
        try:
            file_ext = os.path.splitext(f.filename)[1].lower()
            if file_ext not in allowed_extensions:
                results.append({
                    "filename": f.filename,
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "failure_reason": "Unsupported file type",
                })
                processing_stats["failed"] += 1
                continue

            file_path, _ = _save_upload_to_disk(f, upload_dir)
            
            # Try Enhanced LGCSE Processor first
            try:
                enhanced_result = enhanced_processor.process_certificate_file_enhanced(file_path)
                certificate_data = enhanced_result["extracted_fields"]
                certificate_hash = enhanced_result["certificate_hash"]
                validation_info = enhanced_result["validation"]
                
                processing_stats["enhanced_processed"] += 1
                
                # Check for duplicate
                existing_cert = db.query(Certificate).filter(
                    Certificate.certificate_hash == certificate_hash
                ).first()
                if existing_cert:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": f.filename,
                        "success": False,
                        "error": "Certificate already exists",
                        "failure_reason": "Duplicate certificate",
                        "certificate_hash": certificate_hash,
                    })
                    processing_stats["duplicates"] += 1
                    continue

                # Store on blockchain
                blockchain_result = blockchain_service.store_hash_on_blockchain({
                    "certificate_hash": certificate_hash,
                    "certificate_data": certificate_data
                })
                if not blockchain_result.get("success"):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": f.filename,
                        "success": False,
                        "error": f"Blockchain store failed: {blockchain_result.get('error')}",
                        "failure_reason": "Blockchain store failed",
                    })
                    processing_stats["failed"] += 1
                    continue

                # Create certificate from enhanced data
                cert = _create_certificate_from_enhanced_extracted(
                    db=db,
                    current_user=current_user,
                    file_path=file_path,
                    certificate_data=certificate_data,
                    certificate_hash=certificate_hash,
                    validation_info=validation_info
                )

                cert.blockchain_tx_id = blockchain_result.get("transaction_id")
                cert.blockchain_network = blockchain_result.get("network")
                cert.blockchain_block_number = blockchain_result.get("block_number")
                db.commit()

                db.add(
                    AuditEvent(
                        event_type="certificate_uploaded",
                        actor_user_id=current_user.id,
                        actor_role=current_user.role,
                        certificate_hash=cert.certificate_hash,
                        payload={
                            "tx_id": cert.blockchain_tx_id,
                            "network": cert.blockchain_network,
                            "validation": validation_info,
                            "processing_method": "enhanced_bulk"
                        },
                    )
                )
                db.commit()

                results.append({
                    "filename": f.filename,
                    "success": True,
                    "confidence": validation_info.get("confidence", 0.0),
                    "certificate_id": cert.id,
                    "certificate_hash": certificate_hash,
                    "transaction_id": blockchain_result.get("transaction_id"),
                    "processing_method": "enhanced_ocr",
                    "extracted": {
                        "student_name": certificate_data.get("student_name", ""),
                        "student_id": certificate_data.get("student_id", ""),
                        "institution": certificate_data.get("institution", ""),
                        "examination_year": certificate_data.get("examination_year", ""),
                        "subjects_count": len(certificate_data.get("subjects", [])),
                    },
                })
                
            except Exception as enhanced_error:
                # Fallback to regular processor
                try:
                    processor = CertificateProcessor()
                    fallback_result = processor.process_certificate_file(file_path)
                    certificate_hash = fallback_result.get("certificate_hash")
                    
                    processing_stats["fallback_processed"] += 1
                    
                    # Check for duplicate
                    existing_cert = db.query(Certificate).filter(
                        Certificate.certificate_hash == certificate_hash
                    ).first()
                    if existing_cert:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        results.append({
                            "filename": f.filename,
                            "success": False,
                            "error": "Certificate already exists",
                            "failure_reason": "Duplicate certificate",
                            "certificate_hash": certificate_hash,
                        })
                        processing_stats["duplicates"] += 1
                        continue

                    blockchain_result = blockchain_service.store_hash_on_blockchain(fallback_result)
                    if not blockchain_result.get("success"):
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        results.append({
                            "filename": f.filename,
                            "success": False,
                            "error": f"Blockchain store failed: {blockchain_result.get('error')}",
                            "failure_reason": "Blockchain store failed",
                        })
                        processing_stats["failed"] += 1
                        continue

                    cert = _create_certificate_from_extracted(
                        db=db,
                        current_user=current_user,
                        file_path=file_path,
                        certificate_data=fallback_result,
                    )

                    cert.blockchain_tx_id = blockchain_result.get("transaction_id")
                    cert.blockchain_network = blockchain_result.get("network")
                    cert.blockchain_block_number = blockchain_result.get("block_number")
                    db.commit()

                    db.add(
                        AuditEvent(
                            event_type="certificate_uploaded",
                            actor_user_id=current_user.id,
                            actor_role=current_user.role,
                            certificate_hash=cert.certificate_hash,
                            payload={
                                "tx_id": cert.blockchain_tx_id,
                                "network": cert.blockchain_network,
                                "processing_method": "fallback_bulk"
                            },
                        )
                    )
                    db.commit()

                    results.append({
                        "filename": f.filename,
                        "success": True,
                        "confidence": fallback_result.get("extraction_confidence", 0.0),
                        "certificate_id": cert.id,
                        "certificate_hash": certificate_hash,
                        "transaction_id": blockchain_result.get("transaction_id"),
                        "processing_method": "fallback_ocr",
                        "extracted": {
                            "student_name": fallback_result.get("student_name", ""),
                            "student_number": fallback_result.get("student_number", ""),
                            "institution": fallback_result.get("institution", ""),
                            "date_of_issue": fallback_result.get("date_of_issue", ""),
                        },
                    })
                    
                except Exception as fallback_error:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": f.filename,
                        "success": False,
                        "error": f"Both processors failed: Enhanced - {str(enhanced_error)}, Fallback - {str(fallback_error)}",
                        "failure_reason": "Processing failed",
                    })
                    processing_stats["failed"] += 1

        except OCRDependencyError as e:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            results.append({
                "filename": getattr(f, "filename", "unknown"),
                "success": False,
                "error": str(e),
                "failure_reason": f"OCR dependency missing: {e}",
            })
            processing_stats["failed"] += 1
        except Exception as e:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            results.append({
                "filename": getattr(f, "filename", "unknown"),
                "success": False,
                "error": str(e),
                "failure_reason": str(e),
            })
            processing_stats["failed"] += 1

    return {
        "count": len(files),
        "success_count": sum(1 for r in results if r.get("success")),
        "failure_count": sum(1 for r in results if not r.get("success")),
        "processing_stats": processing_stats,
        "results": results
    }

@router.get("/{certificate_hash}")
async def get_certificate_by_hash(
    certificate_hash: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get certificate by hash"""
    certificate = db.query(Certificate).filter(
        Certificate.certificate_hash == certificate_hash
    ).first()
    
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return certificate

@router.get("/", response_model=List[CertificateResponse])
def list_certificates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all certificates (with pagination)"""
    certificates = db.query(Certificate).offset(skip).limit(limit).all()
    return certificates

@router.get("/search")
def search_certificates(
    q: Optional[str] = Query(None, description="Free text search on student name, id or hash"),
    student_id: Optional[str] = None,
    student_name: Optional[str] = None,
    certificate_hash: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search certificates by hash, student id or name.
    Returns list of matching certificates.
    """
    query = db.query(Certificate)

    if certificate_hash:
        query = query.filter(Certificate.certificate_hash == certificate_hash)
    if student_id:
        query = query.filter(Certificate.student_id.ilike(f"%{student_id}%"))
    if student_name:
        query = query.filter(
            (Certificate.student_name + ' ' + Certificate.student_surname).ilike(f"%{student_name}%")
        )
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Certificate.certificate_hash.ilike(like),
                Certificate.student_id.ilike(like),
                Certificate.student_name.ilike(like),
                Certificate.student_surname.ilike(like)
            )
        )

    results = query.order_by(Certificate.id.desc()).limit(100).all()
    
    return [
        {
            "id": c.id,
            "certificate_hash": c.certificate_hash,
            "student_id": c.student_id,
            "student_name": f"{c.student_name} {c.student_surname}",
            "examination_year": c.examination_year,
            "subjects": c.subjects,
            "credits": c.credits,
            "issue_date": c.issue_date,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in results
    ]

@router.post("/verify")
async def verify_certificate(
    certificate_hash: str = Form(""),
    verification_file: Optional[UploadFile] = File(None),
    verification_mode: str = Form("both"),
    payment_method: str = Form("mpesa"),
    payment_digits: str = Form(...),
    payment_reference: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify a certificate by hash, file, or both"""
    if current_user.role not in {"verifier", "issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only verifiers/issuers can verify certificates"
        )
    
    # Validate verification mode
    allowed_modes = {"hash", "file", "both"}
    if verification_mode not in allowed_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Verification mode must be one of: {', '.join(sorted(allowed_modes))}"
        )
    
    # Validate inputs based on mode
    if verification_mode == "hash" and not certificate_hash:
        raise HTTPException(
            status_code=400,
            detail="Certificate hash is required for hash-only verification"
        )
    
    if verification_mode == "file" and not verification_file:
        raise HTTPException(
            status_code=400,
            detail="Verification file is required for file-only verification"
        )
    
    if verification_mode == "both" and (not certificate_hash or not verification_file):
        raise HTTPException(
            status_code=400,
            detail="Both certificate hash and verification file are required for dual verification"
        )
    
    # Validate payment method
    allowed_methods = {"mpesa", "ecocash", "bank"}
    if payment_method not in allowed_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Payment method must be one of: {', '.join(sorted(allowed_methods))}"
        )

    # Validate payment digits
    if len(payment_digits) != 6 or not payment_digits.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Payment digits must be 6 numbers"
        )
    
    # Find certificate in database (only if hash is provided)
    certificate = None
    if certificate_hash:
        certificate = db.query(Certificate).filter(
            Certificate.certificate_hash == certificate_hash
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Save verification file (if provided)
    file_path = None
    verification_data = None
    computed_hash = None
    
    try:
        if verification_file:
            upload_dir = "uploads/verifications"
            os.makedirs(upload_dir, exist_ok=True)
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(verification_file.filename)[1]}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(verification_file.file, buffer)

            try:
                processor = CertificateProcessor()
            except OCRDependencyError as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"{e}. {e.hint}" if e.hint else str(e),
                )

            # Process verification file
            verification_data = processor.process_certificate_file(file_path)
            computed_hash = verification_data["certificate_hash"]
        
        # Hash verification logic
        hash_match = None
        blockchain_verification = None
        
        if verification_mode == "hash":
            # Hash-only: verify against blockchain
            blockchain_service = BlockchainService()
            blockchain_verification = blockchain_service.verify_hash_on_blockchain(certificate_hash)
            hash_match = blockchain_verification.get("verified", False)
            
        elif verification_mode == "file":
            # File-only: compute hash and check if exists in database
            if computed_hash:
                cert_from_hash = db.query(Certificate).filter(
                    Certificate.certificate_hash == computed_hash
                ).first()
                hash_match = cert_from_hash is not None
                
                if hash_match:
                    # Also verify on blockchain
                    blockchain_service = BlockchainService()
                    blockchain_verification = blockchain_service.verify_hash_on_blockchain(computed_hash)
            
        else:  # verification_mode == "both"
            # Both: compare provided hash with computed hash and verify on blockchain
            hash_match = computed_hash == certificate_hash
            blockchain_service = BlockchainService()
            blockchain_verification = blockchain_service.verify_hash_on_blockchain(certificate_hash)
            
            # Notify network if tampering suspected
            if not hash_match:
                try:
                    blockchain_service.report_tamper(certificate_hash, computed_hash)
                except Exception:
                    pass
        
        # Create verification record
        verification = VerificationRequest(
            certificate_hash=certificate_hash or computed_hash,
            verifier_id=current_user.id,
            uploaded_image_path=file_path,
            extracted_info=verification_data,
            computed_hash=computed_hash,
            blockchain_match=blockchain_verification.get("verified", False) if blockchain_verification else False,
            payment_method=payment_method,
            payment_digits=payment_digits,
            payment_status="confirmed",
            payment_reference=payment_reference or None,
            verification_fee=5.00,
            result="verified" if hash_match else "failed",
            verification_date=datetime.now()
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)

        # Persist a payment record
        payment = Payment(
            verification_request_id=verification.id,
            payer_user_id=current_user.id,
            method=payment_method,
            digits=payment_digits,
            reference=payment_reference or None,
            amount=5.00,
            status="confirmed",
            confirmed_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()

        db.add(
            AuditEvent(
                event_type="certificate_verified" if hash_match else "certificate_tampered",
                actor_user_id=current_user.id,
                actor_role=current_user.role,
                certificate_hash=certificate_hash or computed_hash,
                verification_request_id=verification.id,
                payload={
                    "verification_mode": verification_mode,
                    "hash_match": hash_match,
                    "blockchain_verified": blockchain_verification.get("verified", False) if blockchain_verification else False,
                },
            )
        )
        db.commit()
        
        # Prepare response data
        response_data = {
            "match": hash_match,
            "verification_mode": verification_mode,
            "verified_by": {
                "id": current_user.id,
                "username": current_user.username,
                "role": current_user.role,
            },
            "blockchain_verified": blockchain_verification.get("verified", False) if blockchain_verification else False,
            "payment": {
                "method": payment_method,
                "amount": 5.00,
                "status": "confirmed"
            }
        }
        
        # Add certificate data if available
        if certificate:
            response_data["certificate_data"] = {
                "student_name": f"{certificate.student_name} {certificate.student_surname}",
                "student_id": certificate.student_id,
                "institution": certificate.extracted_data.get("institution", "") if certificate.extracted_data else "",
                "issue_date": certificate.issue_date,
                "subjects": certificate.subjects
            }
        elif verification_mode == "file" and hash_match and computed_hash:
            # For file-only mode, find certificate by computed hash
            cert_from_hash = db.query(Certificate).filter(
                Certificate.certificate_hash == computed_hash
            ).first()
            if cert_from_hash:
                response_data["certificate_data"] = {
                    "student_name": f"{cert_from_hash.student_name} {cert_from_hash.student_surname}",
                    "student_id": cert_from_hash.student_id,
                    "institution": cert_from_hash.extracted_data.get("institution", "") if cert_from_hash.extracted_data else "",
                    "issue_date": cert_from_hash.issue_date,
                    "subjects": cert_from_hash.subjects
                }
        
        return response_data

    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verify/result/{verification_id}")
def get_verification_result(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a verification result by id.
    Matches the shape expected by certificateApi.getVerificationResult.
    """
    v = db.query(VerificationRequest).filter(VerificationRequest.id == verification_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    cert = None
    if v.certificate_hash:
        cert = (
            db.query(Certificate)
            .filter(Certificate.certificate_hash == v.certificate_hash)
            .first()
        )

    return {
        "id": v.id,
        "certificate_hash": v.certificate_hash,
        "result": v.result,
        "blockchain_match": v.blockchain_match,
        "payment_method": v.payment_method,
        "payment_digits": v.payment_digits,
        "payment_status": v.payment_status,
        "verification_fee": v.verification_fee,
        "verification_date": v.verification_date.isoformat() if v.verification_date else None,
        "certificate_data": {
            "student_name": f"{cert.student_name} {cert.student_surname}" if cert else "",
            "student_id": cert.student_id if cert else "",
            "institution": cert.extracted_data.get("institution", "") if (cert and cert.extracted_data) else "",
            "issue_date": cert.issue_date if cert else "",
        } if cert else None,
    }
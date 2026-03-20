from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from auth import get_current_user, require_admin, require_role
from database import get_db
from models import Institution, User, Payment, VerificationLog, Certificate

router = APIRouter(prefix="/api/institutions", tags=["institutions"])

# Pydantic models for request/response
class InstitutionBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=20, description="Institution code (unique)")
    name: str = Field(..., min_length=2, max_length=200, description="Full institution name")
    role: str = Field(..., description="Role: ISSUER or VERIFIER")

    @validator('role')
    def validate_role(cls, v):
        if v not in ("ISSUER", "VERIFIER"):
            raise ValueError('Role must be either ISSUER or VERIFIER')
        return v
    
    @validator('code')
    def validate_code(cls, v):
        # Ensure code is uppercase and alphanumeric
        if not v.isalnum():
            raise ValueError('Institution code must be alphanumeric')
        return v.upper()

class InstitutionCreate(InstitutionBase):
    domain: Optional[str] = Field(None, description="Email domain for automatic association")
    address: Optional[str] = Field(None, description="Physical address")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")

class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    role: Optional[str] = None
    domain: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ("ISSUER", "VERIFIER"):
            raise ValueError('Role must be either ISSUER or VERIFIER')
        return v

class InstitutionResponse(BaseModel):
    id: str
    code: str
    name: str
    role: str
    domain: Optional[str]
    address: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    stats: Optional[Dict[str, Any]] = None

class InstitutionStats(BaseModel):
    total_users: int
    active_users: int
    pending_users: int
    total_certificates: int
    total_verifications: int
    total_payments: int
    total_payment_amount: float
    recent_activity: List[Dict[str, Any]]

class InstitutionListResponse(BaseModel):
    institutions: List[InstitutionResponse]
    total: int
    page: int
    limit: int

@router.get("", response_model=InstitutionListResponse)
def list_institutions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role (ISSUER/VERIFIER)"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    include_stats: bool = Query(False, description="Include institution statistics")
):
    """List all institutions with pagination and filtering"""
    
    # Build query
    query = db.query(Institution)
    
    if role:
        query = query.filter(Institution.role == role)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Institution.name.ilike(search_term)) | 
            (Institution.code.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    institutions = query.order_by(Institution.name.asc()).offset(offset).limit(limit).all()
    
    # Prepare response
    result = []
    for inst in institutions:
        inst_data = {
            "id": inst.id,
            "code": inst.code,
            "name": inst.name,
            "role": inst.role,
            "domain": inst.domain,
            "address": inst.address,
            "contact_email": inst.contact_email,
            "contact_phone": inst.contact_phone,
            "is_active": inst.is_active,
            "created_at": inst.created_at,
            "updated_at": inst.updated_at
        }
        
        if include_stats:
            inst_data["stats"] = get_institution_stats(db, inst.code)
        
        result.append(inst_data)
    
    return {
        "institutions": result,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/all")
def list_all_institutions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all institutions (simplified) - accessible to all authenticated users"""
    institutions = db.query(Institution).filter(
        Institution.is_active == True
    ).order_by(Institution.name.asc()).all()
    
    return [
        {
            "code": inst.code,
            "name": inst.name,
            "role": inst.role,
        }
        for inst in institutions
    ]

@router.post("", response_model=InstitutionResponse)
def create_institution(
    payload: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new institution"""
    
    # Check if institution code already exists
    existing = db.query(Institution).filter(Institution.code == payload.code).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Institution with code '{payload.code}' already exists"
        )
    
    # Check if domain is already used
    if payload.domain:
        existing_domain = db.query(Institution).filter(
            Institution.domain == payload.domain
        ).first()
        if existing_domain:
            raise HTTPException(
                status_code=400,
                detail=f"Domain '{payload.domain}' is already associated with another institution"
            )
    
    # Create new institution
    inst = Institution(
        id=str(uuid.uuid4()),
        code=payload.code,
        name=payload.name,
        role=payload.role,
        domain=payload.domain,
        address=payload.address,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(inst)
    db.commit()
    db.refresh(inst)
    
    return {
        "id": inst.id,
        "code": inst.code,
        "name": inst.name,
        "role": inst.role,
        "domain": inst.domain,
        "address": inst.address,
        "contact_email": inst.contact_email,
        "contact_phone": inst.contact_phone,
        "is_active": inst.is_active,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at
    }

@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(
    institution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get institution by ID"""
    
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    return {
        "id": inst.id,
        "code": inst.code,
        "name": inst.name,
        "role": inst.role,
        "domain": inst.domain,
        "address": inst.address,
        "contact_email": inst.contact_email,
        "contact_phone": inst.contact_phone,
        "is_active": inst.is_active,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at
    }

@router.get("/code/{institution_code}", response_model=InstitutionResponse)
def get_institution_by_code(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get institution by code - accessible to all authenticated users"""
    
    inst = db.query(Institution).filter(Institution.code == institution_code.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    return {
        "id": inst.id,
        "code": inst.code,
        "name": inst.name,
        "role": inst.role,
        "domain": inst.domain,
        "address": inst.address,
        "contact_email": inst.contact_email,
        "contact_phone": inst.contact_phone,
        "is_active": inst.is_active,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at
    }

@router.put("/{institution_id}", response_model=InstitutionResponse)
def update_institution(
    institution_id: str,
    payload: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update institution details"""
    
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Update fields if provided
    if payload.name is not None:
        inst.name = payload.name
    if payload.role is not None:
        inst.role = payload.role
    if payload.domain is not None:
        # Check if domain is already used by another institution
        if payload.domain != inst.domain:
            existing_domain = db.query(Institution).filter(
                Institution.domain == payload.domain,
                Institution.id != institution_id
            ).first()
            if existing_domain:
                raise HTTPException(
                    status_code=400,
                    detail=f"Domain '{payload.domain}' is already associated with another institution"
                )
        inst.domain = payload.domain
    if payload.address is not None:
        inst.address = payload.address
    if payload.contact_email is not None:
        inst.contact_email = payload.contact_email
    if payload.contact_phone is not None:
        inst.contact_phone = payload.contact_phone
    if payload.is_active is not None:
        inst.is_active = payload.is_active
    
    inst.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inst)
    
    return {
        "id": inst.id,
        "code": inst.code,
        "name": inst.name,
        "role": inst.role,
        "domain": inst.domain,
        "address": inst.address,
        "contact_email": inst.contact_email,
        "contact_phone": inst.contact_phone,
        "is_active": inst.is_active,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at
    }

@router.delete("/{institution_id}")
def delete_institution(
    institution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete an institution (soft delete by setting inactive)"""
    
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Check if institution has users
    user_count = db.query(User).filter(User.institution_code == inst.code).count()
    if user_count > 0:
        # Soft delete instead of hard delete
        inst.is_active = False
        inst.updated_at = datetime.utcnow()
        db.commit()
        return {
            "message": f"Institution deactivated. It has {user_count} associated users.",
            "deactivated": True
        }
    
    # Hard delete if no users
    db.delete(inst)
    db.commit()
    
    return {"message": "Institution deleted successfully"}

@router.get("/{institution_code}/stats", response_model=InstitutionStats)
def get_institution_stats_endpoint(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get detailed statistics for an institution"""
    
    stats = get_institution_stats(db, institution_code.upper())
    return stats

def get_institution_stats(db: Session, institution_code: str) -> Dict[str, Any]:
    """Helper function to get institution statistics"""
    
    # User stats
    user_stats = db.query(
        func.count(User.id).label('total'),
        func.count(case([(User.is_active == True, User.id)])).label('active'),
        func.count(case([(User.role == 'pending', User.id)])).label('pending')
    ).filter(User.institution_code == institution_code).first()
    
    # Certificate stats (for issuers)
    certificate_count = db.query(func.count(Certificate.id)).filter(
        Certificate.issuer_code == institution_code
    ).scalar() or 0
    
    # Verification stats (for verifiers)
    verification_count = db.query(func.count(VerificationLog.id)).filter(
        VerificationLog.verifier_code == institution_code
    ).scalar() or 0
    
    # Payment stats
    payment_stats = db.query(
        func.count(Payment.id).label('total_payments'),
        func.sum(Payment.amount).label('total_amount'),
        func.count(case([(Payment.status == 'CONFIRMED', Payment.id)])).label('confirmed_payments')
    ).filter(Payment.payee_institution_code == institution_code).first()
    
    # Recent activity
    recent_activity = []
    
    # Recent users
    recent_users = db.query(User).filter(
        User.institution_code == institution_code
    ).order_by(User.created_at.desc()).limit(5).all()
    
    for user in recent_users:
        recent_activity.append({
            "type": "user_registered",
            "description": f"New user registered: {user.username}",
            "timestamp": user.created_at
        })
    
    # Recent verifications
    recent_verifications = db.query(VerificationLog).filter(
        VerificationLog.verifier_code == institution_code
    ).order_by(VerificationLog.created_at.desc()).limit(5).all()
    
    for verif in recent_verifications:
        recent_activity.append({
            "type": "verification",
            "description": f"Certificate verified: {verif.hash[:16]}...",
            "result": "Success" if verif.verified else "Failed",
            "timestamp": verif.created_at
        })
    
    # Sort by timestamp
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activity = recent_activity[:10]
    
    return {
        "total_users": user_stats[0] or 0,
        "active_users": user_stats[1] or 0,
        "pending_users": user_stats[2] or 0,
        "total_certificates": certificate_count,
        "total_verifications": verification_count,
        "total_payments": payment_stats[0] or 0,
        "total_payment_amount": float(payment_stats[1] or 0),
        "confirmed_payments": payment_stats[2] or 0,
        "recent_activity": recent_activity
    }

@router.get("/{institution_code}/users")
def get_institution_users(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all users belonging to an institution"""
    
    offset = (page - 1) * limit
    
    users = db.query(User).filter(
        User.institution_code == institution_code.upper()
    ).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    
    total = db.query(User).filter(
        User.institution_code == institution_code.upper()
    ).count()
    
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "last_login_at": u.last_login_at,
                "created_at": u.created_at
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/{institution_code}/payments")
def get_institution_payments(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all payments received by an institution"""
    
    offset = (page - 1) * limit
    
    payments = db.query(Payment).filter(
        Payment.payee_institution_code == institution_code.upper()
    ).order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    
    total = db.query(Payment).filter(
        Payment.payee_institution_code == institution_code.upper()
    ).count()
    
    return {
        "payments": [
            {
                "id": p.id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "method": p.method,
                "created_at": p.created_at,
                "confirmed_at": p.confirmed_at,
                "mpesa_transaction_id": p.mpesa_transaction_id
            }
            for p in payments
        ],
        "total": total,
        "page": page,
        "limit": limit
    }

@router.post("/{institution_code}/verify-domain")
def verify_institution_domain(
    institution_code: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Verify and associate a domain with an institution"""
    
    inst = db.query(Institution).filter(Institution.code == institution_code.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Check if domain is already used
    existing = db.query(Institution).filter(
        Institution.domain == domain,
        Institution.code != institution_code.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Domain '{domain}' is already associated with {existing.name}"
        )
    
    inst.domain = domain
    inst.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": f"Domain '{domain}' verified and associated with {inst.name}",
        "institution": inst.code,
        "domain": inst.domain
    }

@router.get("/my")
def get_my_institution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's institution information"""
    try:
        # Get institution from user's institution field
        if not current_user.institution:
            return {
                "id": None,
                "code": None,
                "name": "No Institution",
                "role": current_user.role,
                "domain": None,
                "address": None,
                "contact_email": None,
                "contact_phone": None,
                "is_active": True,
                "created_at": current_user.created_at.isoformat(),
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
            }
        
        # Try to find institution record
        institution = db.query(Institution).filter(
            Institution.code == current_user.institution
        ).first()
        
        if institution:
            return {
                "id": institution.id,
                "code": institution.code,
                "name": institution.name,
                "role": institution.role,
                "domain": institution.domain,
                "address": institution.address,
                "contact_email": institution.contact_email,
                "contact_phone": institution.contact_phone,
                "is_active": institution.is_active,
                "created_at": institution.created_at.isoformat(),
                "updated_at": institution.updated_at.isoformat()
            }
        else:
            # Return basic info from user record
            return {
                "id": None,
                "code": current_user.institution,
                "name": current_user.institution,
                "role": current_user.role,
                "domain": None,
                "address": None,
                "contact_email": None,
                "contact_phone": None,
                "is_active": True,
                "created_at": current_user.created_at.isoformat(),
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
            }
            
    except Exception as e:
        print(f"Error fetching user institution: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch institution information")
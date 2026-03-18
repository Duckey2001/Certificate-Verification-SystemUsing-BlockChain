from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import uuid
import os
from dotenv import load_dotenv

from database import get_db
from models import User
from verifier_models import VerifierCredential, VerifierAttestation, VerifierAuditLog
from auth import get_current_user, get_password_hash, create_access_token

load_dotenv()

router = APIRouter(prefix="/api/verifier", tags=["verifier"])

# Pydantic models
class VerifierRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    qualification_level: Optional[str] = None
    institution_affiliation: Optional[str] = None
    years_experience: Optional[int] = 0
    professional_certificates: Optional[List[Dict[str, Any]]] = []

class VerifierLogin(BaseModel):
    username: str
    password: str

class VerifierCredentialUpdate(BaseModel):
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    qualification_level: Optional[str] = None
    institution_affiliation: Optional[str] = None
    years_experience: Optional[int] = None
    professional_certificates: Optional[List[Dict[str, Any]]] = None

class VerifierResponse(BaseModel):
    id: str
    username: str
    email: str
    credential_id: str
    license_number: Optional[str]
    specialization: Optional[str]
    qualification_level: Optional[str]
    institution_affiliation: Optional[str]
    years_experience: int
    accreditation_status: str
    reputation_score: float
    verification_count: int
    blockchain_registered: bool
    is_active: bool
    created_at: datetime

# Helper functions
def generate_credential_id():
    """Generate unique verifier credential ID"""
    return f"VER-{uuid.uuid4().hex[:12].upper()}"

def hash_credential_data(data: dict) -> str:
    """Create hash of credential data for blockchain storage"""
    data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(data_string.encode()).hexdigest()

def log_verifier_activity(
    db: Session,
    verifier_credential_id: int,
    user_id: int,
    activity_type: str,
    action: str,
    description: str = None,
    status: str = "success",
    request: Request = None,
    **kwargs
):
    """Log verifier activity for audit trail"""
    audit_log = VerifierAuditLog(
        verifier_credential_id=verifier_credential_id,
        user_id=user_id,
        activity_type=activity_type,
        action=action,
        description=description,
        status=status,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        created_at=datetime.utcnow(),
        metadata_json=kwargs
    )
    db.add(audit_log)
    db.commit()

# Routes
@router.post("/register", response_model=Dict[str, Any])
async def register_verifier(
    request: Request,
    verifier_data: VerifierRegistration,
    db: Session = Depends(get_db)
):
    """Register a new verifier with enhanced credentials"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == verifier_data.username) | 
            (User.email == verifier_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this username or email already exists"
            )
        
        # Create user with verifier role
        hashed_password = get_password_hash(verifier_data.password)
        user = User(
            username=verifier_data.username,
            email=verifier_data.email,
            password_hash=hashed_password,
            role="verifier",
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create verifier credentials
        credential_id = generate_credential_id()
        credential_data = {
            "credential_id": credential_id,
            "username": verifier_data.username,
            "email": verifier_data.email,
            "license_number": verifier_data.license_number,
            "specialization": verifier_data.specialization,
            "qualification_level": verifier_data.qualification_level,
            "institution_affiliation": verifier_data.institution_affiliation,
            "years_experience": verifier_data.years_experience,
            "professional_certificates": verifier_data.professional_certificates
        }
        
        credential_hash = hash_credential_data(credential_data)
        
        verifier_credential = VerifierCredential(
            user_id=user.id,
            credential_id=credential_id,
            license_number=verifier_data.license_number,
            specialization=verifier_data.specialization,
            qualification_level=verifier_data.qualification_level,
            institution_affiliation=verifier_data.institution_affiliation,
            years_experience=verifier_data.years_experience,
            professional_certificates=verifier_data.professional_certificates,
            credential_hash=credential_hash,
            accreditation_status="pending",
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow()
        )
        
        db.add(verifier_credential)
        db.commit()
        db.refresh(verifier_credential)
        
        # Log registration
        log_verifier_activity(
            db, verifier_credential.id, user.id,
            "registration", "verifier_registered",
            f"Verifier {verifier_data.username} registered with credential ID {credential_id}",
            "success", request
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
            "verifier_credential": {
                "credential_id": credential_id,
                "accreditation_status": "pending",
                "blockchain_registered": False
            },
            "message": "Verifier registration successful. Awaiting accreditation approval."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Verifier registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register verifier")

@router.post("/login", response_model=Dict[str, Any])
async def login_verifier(
    request: Request,
    login_data: VerifierLogin,
    db: Session = Depends(get_db)
):
    """Login for verifier users"""
    try:
        # Find user by username or email
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user:
            user = db.query(User).filter(User.email == login_data.username).first()
        
        if not user or user.role != "verifier":
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        from auth import verify_password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # Get verifier credentials
        verifier_credential = db.query(VerifierCredential).filter(
            VerifierCredential.user_id == user.id
        ).first()
        
        if not verifier_credential:
            raise HTTPException(status_code=404, detail="Verifier credentials not found")
        
        # Log login activity
        log_verifier_activity(
            db, verifier_credential.id, user.id,
            "login", "verifier_login",
            f"Verifier {user.username} logged in",
            "success", request
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
            "verifier_credential": {
                "credential_id": verifier_credential.credential_id,
                "accreditation_status": verifier_credential.accreditation_status,
                "reputation_score": verifier_credential.reputation_score,
                "verification_count": verifier_credential.verification_count,
                "blockchain_registered": verifier_credential.blockchain_registered,
                "is_active": verifier_credential.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Verifier login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to login")

@router.get("/profile", response_model=VerifierResponse)
async def get_verifier_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current verifier's profile"""
    if current_user.role != "verifier":
        raise HTTPException(status_code=403, detail="Access denied. Verifier role required.")
    
    verifier_credential = db.query(VerifierCredential).filter(
        VerifierCredential.user_id == current_user.id
    ).first()
    
    if not verifier_credential:
        raise HTTPException(status_code=404, detail="Verifier credentials not found")
    
    return VerifierResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        credential_id=verifier_credential.credential_id,
        license_number=verifier_credential.license_number,
        specialization=verifier_credential.specialization,
        qualification_level=verifier_credential.qualification_level,
        institution_affiliation=verifier_credential.institution_affiliation,
        years_experience=verifier_credential.years_experience,
        accreditation_status=verifier_credential.accreditation_status,
        reputation_score=verifier_credential.reputation_score,
        verification_count=verifier_credential.verification_count,
        blockchain_registered=verifier_credential.blockchain_registered,
        is_active=verifier_credential.is_active,
        created_at=verifier_credential.created_at
    )

@router.put("/profile", response_model=Dict[str, Any])
async def update_verifier_profile(
    update_data: VerifierCredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update verifier profile credentials"""
    if current_user.role != "verifier":
        raise HTTPException(status_code=403, detail="Access denied. Verifier role required.")
    
    verifier_credential = db.query(VerifierCredential).filter(
        VerifierCredential.user_id == current_user.id
    ).first()
    
    if not verifier_credential:
        raise HTTPException(status_code=404, detail="Verifier credentials not found")
    
    # Store old values for audit
    old_values = {
        "license_number": verifier_credential.license_number,
        "specialization": verifier_credential.specialization,
        "qualification_level": verifier_credential.qualification_level,
        "institution_affiliation": verifier_credential.institution_affiliation,
        "years_experience": verifier_credential.years_experience,
        "professional_certificates": verifier_credential.professional_certificates
    }
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(verifier_credential, field):
            setattr(verifier_credential, field, value)
    
    verifier_credential.updated_at = datetime.utcnow()
    
    # Recreate credential hash if data changed
    credential_data = {
        "credential_id": verifier_credential.credential_id,
        "username": current_user.username,
        "email": current_user.email,
        "license_number": verifier_credential.license_number,
        "specialization": verifier_credential.specialization,
        "qualification_level": verifier_credential.qualification_level,
        "institution_affiliation": verifier_credential.institution_affiliation,
        "years_experience": verifier_credential.years_experience,
        "professional_certificates": verifier_credential.professional_certificates
    }
    
    verifier_credential.credential_hash = hash_credential_data(credential_data)
    
    db.commit()
    
    # Log update
    log_verifier_activity(
        db, verifier_credential.id, current_user.id,
        "profile_update", "verifier_profile_updated",
        "Verifier profile updated successfully",
        "success",
        old_values=old_values,
        new_values=update_dict
    )
    
    return {
        "message": "Profile updated successfully",
        "credential_id": verifier_credential.credential_id,
        "credential_hash": verifier_credential.credential_hash
    }

@router.post("/blockchain/register", response_model=Dict[str, Any])
async def register_on_blockchain(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register verifier credentials on blockchain"""
    if current_user.role != "verifier":
        raise HTTPException(status_code=403, detail="Access denied. Verifier role required.")
    
    verifier_credential = db.query(VerifierCredential).filter(
        VerifierCredential.user_id == current_user.id
    ).first()
    
    if not verifier_credential:
        raise HTTPException(status_code=404, detail="Verifier credentials not found")
    
    if verifier_credential.blockchain_registered:
        raise HTTPException(status_code=400, detail="Already registered on blockchain")
    
    try:
        # Mock blockchain registration - in real implementation, this would interact with smart contract
        mock_tx_id = f"0x{uuid.uuid4().hex[2:]}"
        mock_block_number = 12345
        mock_network = "hardhat"
        
        # Update blockchain info
        verifier_credential.blockchain_registered = True
        verifier_credential.blockchain_tx_id = mock_tx_id
        verifier_credential.blockchain_network = mock_network
        verifier_credential.blockchain_verifier_id = f"verifier_{current_user.id}"
        verifier_credential.updated_at = datetime.utcnow()
        
        # Create attestation record
        attestation = VerifierAttestation(
            verifier_credential_id=verifier_credential.id,
            attestation_type="identity",
            attestation_hash=hashlib.sha256(f"{verifier_credential.credential_id}_identity".encode()).hexdigest(),
            blockchain_tx_id=mock_tx_id,
            blockchain_network=mock_network,
            block_number=mock_block_number,
            block_timestamp=datetime.utcnow(),
            issuer="CertiVert Authority",
            metadata={"registration_type": "blockchain_verifier"}
        )
        
        db.add(attestation)
        db.commit()
        
        # Log blockchain registration
        log_verifier_activity(
            db, verifier_credential.id, current_user.id,
            "blockchain", "blockchain_registration",
            f"Verifier registered on blockchain with TX: {mock_tx_id}",
            "success",
            blockchain_tx_id=mock_tx_id,
            blockchain_network=mock_network
        )
        
        return {
            "message": "Successfully registered on blockchain",
            "blockchain_tx_id": mock_tx_id,
            "blockchain_network": mock_network,
            "blockchain_verifier_id": verifier_credential.blockchain_verifier_id,
            "attestation_id": attestation.id
        }
        
    except Exception as e:
        print(f"Blockchain registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register on blockchain")

@router.get("/audit-log", response_model=List[Dict[str, Any]])
async def get_verifier_audit_log(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get verifier's audit log"""
    if current_user.role != "verifier":
        raise HTTPException(status_code=403, detail="Access denied. Verifier role required.")
    
    verifier_credential = db.query(VerifierCredential).filter(
        VerifierCredential.user_id == current_user.id
    ).first()
    
    if not verifier_credential:
        raise HTTPException(status_code=404, detail="Verifier credentials not found")
    
    audit_logs = db.query(VerifierAuditLog).filter(
        VerifierAuditLog.verifier_credential_id == verifier_credential.id
    ).order_by(VerifierAuditLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "activity_type": log.activity_type,
            "action": log.action,
            "description": log.description,
            "status": log.status,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
            "metadata": log.metadata_json
        }
        for log in audit_logs
    ]

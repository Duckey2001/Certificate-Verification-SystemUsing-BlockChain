"""
Hyperledger Fabric Integration API for LGCSE Certificate Verification System

This module provides REST API endpoints for interacting with the Hyperledger Fabric
blockchain network, including certificate management, verification, and monitoring.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin, require_role
from database import get_db
from models import (
    Institution, BlockchainNode, Certificate, VerificationRequest,
    User, NodeActivityLog
)
from utils.fabric_sdk import fabric_sdk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fabric", tags=["fabric"])

# Pydantic models for request/response
class CertificateIssueRequest(BaseModel):
    certificate_hash: str = Field(..., min_length=1, max_length=100, description="Unique certificate hash")
    student_id: str = Field(..., min_length=1, max_length=50, description="Student ID")
    student_name: str = Field(..., min_length=1, max_length=100, description="Student first name")
    student_surname: str = Field(..., min_length=1, max_length=100, description="Student last name")
    examination_year: int = Field(..., ge=2000, le=2030, description="Examination year")
    subjects: List[Dict[str, Any]] = Field(..., min_items=1, description="List of subjects with grades")
    credits: int = Field(..., ge=0, description="Total credits")
    issue_date: str = Field(..., description="Issue date (YYYY-MM-DD)")
    issuer: str = Field(..., min_length=1, max_length=200, description="Issuer name")
    institution_code: str = Field(..., min_length=2, max_length=20, description="Institution code")
    private_data: Optional[str] = Field(None, description="Encrypted private data")

    @validator('subjects')
    def validate_subjects(cls, v):
        for subject in v:
            if 'name' not in subject or 'grade' not in subject:
                raise ValueError('Each subject must have name and grade')
        return v

class CertificateVerificationRequest(BaseModel):
    certificate_hash: str = Field(..., min_length=1, max_length=100, description="Certificate hash to verify")
    verifier_id: str = Field(..., min_length=1, max_length=50, description="Verifier ID")
    verifier_name: str = Field(..., min_length=1, max_length=200, description="Verifier name")
    institution_code: str = Field(..., min_length=2, max_length=20, description="Institution code")
    verification_method: str = Field(..., description="Verification method: hash, file, qr_code, digital")
    ip_address: str = Field(..., description="IP address of verifier")
    user_agent: str = Field(..., description="User agent string")
    verification_data: Optional[str] = Field(None, description="Additional verification data")

    @validator('verification_method')
    def validate_verification_method(cls, v):
        if v not in ('hash', 'file', 'qr_code', 'digital'):
            raise ValueError('Verification method must be one of: hash, file, qr_code, digital')
        return v

class CertificateRevocationRequest(BaseModel):
    certificate_hash: str = Field(..., min_length=1, max_length=100, description="Certificate hash to revoke")
    reason: str = Field(..., min_length=1, max_length=500, description="Revocation reason")
    revoked_by: str = Field(..., min_length=1, max_length=200, description="Who revoked the certificate")
    institution_code: str = Field(..., min_length=2, max_length=20, description="Institution code")

class InstitutionUpdateRequest(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=100, description="Node ID")
    institution_name: str = Field(..., min_length=1, max_length=200, description="Institution name")
    node_type: str = Field(..., description="Node type: issuer, verifier, both")
    msp_id: str = Field(..., min_length=1, max_length=100, description="MSP ID")
    peer_id: str = Field(..., min_length=1, max_length=100, description="Peer ID")
    channel_name: str = Field(..., min_length=1, max_length=100, description="Channel name")
    status: str = Field(..., description="Node status: active, inactive, maintenance")
    public_key: str = Field(..., min_length=1, description="Public key")
    node_config: Optional[Dict[str, str]] = Field(None, description="Node configuration")

    @validator('node_type')
    def validate_node_type(cls, v):
        if v not in ('issuer', 'verifier', 'both'):
            raise ValueError('Node type must be one of: issuer, verifier, both')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v not in ('active', 'inactive', 'maintenance'):
            raise ValueError('Status must be one of: active, inactive, maintenance')
        return v

class FabricResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

# Certificate Management Endpoints
@router.post("/certificates/issue", response_model=FabricResponse)
def issue_certificate(
    request: CertificateIssueRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role)
):
    """Issue a new certificate on the blockchain"""
    try:
        # Verify institution exists and is authorized to issue
        institution = db.query(Institution).filter(
            Institution.code == request.institution_code.upper()
        ).first()
        
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        if institution.role != "ISSUER":
            raise HTTPException(status_code=403, detail="Institution not authorized to issue certificates")
        
        # Check if certificate already exists
        existing_cert = db.query(Certificate).filter(
            Certificate.certificate_hash == request.certificate_hash
        ).first()
        
        if existing_cert:
            raise HTTPException(status_code=400, detail="Certificate already exists")
        
        # Prepare certificate data for blockchain
        certificate_data = {
            "certificateHash": request.certificate_hash,
            "studentId": request.student_id,
            "studentName": request.student_name,
            "studentSurname": request.student_surname,
            "examinationYear": request.examination_year,
            "subjects": request.subjects,
            "credits": request.credits,
            "issueDate": request.issue_date,
            "issuer": request.issuer,
            "institutionCode": request.institution_code.upper(),
            "privateData": request.private_data or ""
        }
        
        # Issue certificate on blockchain
        blockchain_result = fabric_sdk.issue_certificate(certificate_data)
        
        if not blockchain_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Blockchain operation failed: {blockchain_result.get('error')}")
        
        # Create certificate record in database
        db_certificate = Certificate(
            certificate_hash=request.certificate_hash,
            student_id=request.student_id,
            student_name=request.student_name,
            student_surname=request.student_surname,
            examination_year=request.examination_year,
            subjects=request.subjects,
            credits=request.credits,
            issue_date=request.issue_date,
            issuer_id=current_user.id,
            original_image_path=None,  # Will be set by upload endpoint
            extracted_data=certificate_data,
            status="active",
            verification_status="pending",
            university_id=institution.id,
            blockchain_tx_id=blockchain_result.get("transaction_id"),
            blockchain_network="fabric",
            blockchain_block_number=blockchain_result.get("block_number")
        )
        
        db.add(db_certificate)
        db.commit()
        
        # Log activity
        log_activity(
            db, 
            "issue_certificate", 
            f"Certificate {request.certificate_hash} issued on blockchain",
            {
                "certificate_hash": request.certificate_hash,
                "student_id": request.student_id,
                "institution_code": request.institution_code,
                "transaction_id": blockchain_result.get("transaction_id"),
                "block_number": blockchain_result.get("block_number")
            },
            current_user.id
        )
        
        return FabricResponse(
            success=True,
            message="Certificate issued successfully",
            data={
                "certificate_hash": request.certificate_hash,
                "transaction_id": blockchain_result.get("transaction_id"),
                "block_number": blockchain_result.get("block_number"),
                "status": "issued"
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to issue certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/certificates/verify", response_model=FabricResponse)
def verify_certificate(
    request: CertificateVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role)
):
    """Verify a certificate on the blockchain"""
    try:
        # Verify institution exists and is authorized to verify
        institution = db.query(Institution).filter(
            Institution.code == request.institution_code.upper()
        ).first()
        
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        if institution.role != "VERIFIER":
            raise HTTPException(status_code=403, detail="Institution not authorized to verify certificates")
        
        # Check if certificate exists
        certificate = db.query(Certificate).filter(
            Certificate.certificate_hash == request.certificate_hash
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Prepare verification data for blockchain
        verification_data = {
            "certificateHash": request.certificate_hash,
            "verifierId": request.verifier_id,
            "verifierName": request.verifier_name,
            "institutionCode": request.institution_code.upper(),
            "verificationMethod": request.verification_method,
            "ipAddress": request.ip_address,
            "userAgent": request.user_agent,
            "verificationData": request.verification_data or ""
        }
        
        # Verify certificate on blockchain
        blockchain_result = fabric_sdk.verify_certificate(verification_data)
        
        if not blockchain_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Blockchain operation failed: {blockchain_result.get('error')}")
        
        # Create verification request record
        verification_request = VerificationRequest(
            certificate_id=certificate.id,
            certificate_hash=request.certificate_hash,
            requester_id=current_user.id,
            verifier_id=current_user.id,
            verification_method=request.verification_method,
            verification_result="valid",  # Will be updated based on blockchain result
            verification_date=datetime.utcnow(),
            uploaded_image_path=None,
            extracted_info=verification_data,
            blockchain_match=True,
            blockchain_tx_id=blockchain_result.get("transaction_id")
        )
        
        db.add(verification_request)
        db.commit()
        
        # Update certificate verification count
        certificate.verification_count = (certificate.verification_count or 0) + 1
        certificate.last_verified_at = datetime.utcnow()
        db.commit()
        
        # Log activity
        log_activity(
            db,
            "verify_certificate",
            f"Certificate {request.certificate_hash} verified on blockchain",
            {
                "certificate_hash": request.certificate_hash,
                "verifier_id": request.verifier_id,
                "institution_code": request.institution_code,
                "verification_method": request.verification_method,
                "transaction_id": blockchain_result.get("transaction_id")
            },
            current_user.id
        )
        
        return FabricResponse(
            success=True,
            message="Certificate verified successfully",
            data={
                "certificate_hash": request.certificate_hash,
                "verification_result": "valid",
                "transaction_id": blockchain_result.get("transaction_id"),
                "block_number": blockchain_result.get("block_number"),
                "verified_at": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/certificates/{certificate_hash}", response_model=FabricResponse)
def get_certificate(
    certificate_hash: str,
    include_private: bool = Query(False, description="Include private data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get certificate details from blockchain"""
    try:
        # Get certificate from blockchain
        blockchain_result = fabric_sdk.get_certificate(certificate_hash)
        
        if not blockchain_result.get("success"):
            raise HTTPException(status_code=404, detail="Certificate not found on blockchain")
        
        certificate_data = blockchain_result.get("certificate")
        
        # Get private data if requested and authorized
        private_data = None
        if include_private:
            # Check if user is authorized to view private data
            if current_user.role in ["admin", "issuer"]:
                private_result = fabric_sdk.get_certificate_private_data(certificate_hash)
                if private_result.get("success"):
                    private_data = private_result.get("private_data")
        
        # Get verification history
        history_result = fabric_sdk.get_verification_history(certificate_hash)
        verification_history = history_result.get("verification_history", []) if history_result.get("success") else []
        
        return FabricResponse(
            success=True,
            message="Certificate retrieved successfully",
            data={
                "certificate": certificate_data,
                "private_data": private_data,
                "verification_history": verification_history,
                "verification_count": len(verification_history)
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/certificates/revoke", response_model=FabricResponse)
def revoke_certificate(
    request: CertificateRevocationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Revoke a certificate on the blockchain"""
    try:
        # Check if certificate exists
        certificate = db.query(Certificate).filter(
            Certificate.certificate_hash == request.certificate_hash
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Verify institution exists and is authorized
        institution = db.query(Institution).filter(
            Institution.code == request.institution_code.upper()
        ).first()
        
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        # Only issuing institution can revoke
        if certificate.university_id != institution.id:
            raise HTTPException(status_code=403, detail="Only the issuing institution can revoke this certificate")
        
        # Prepare revocation data for blockchain
        revocation_data = {
            "certificateHash": request.certificate_hash,
            "reason": request.reason,
            "revokedBy": request.revoked_by,
            "institutionCode": request.institution_code.upper()
        }
        
        # Revoke certificate on blockchain
        blockchain_result = fabric_sdk.revoke_certificate(revocation_data)
        
        if not blockchain_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Blockchain operation failed: {blockchain_result.get('error')}")
        
        # Update certificate status in database
        certificate.status = "revoked"
        certificate.verification_status = "revoked"
        certificate.updated_at = datetime.utcnow()
        db.commit()
        
        # Log activity
        log_activity(
            db,
            "revoke_certificate",
            f"Certificate {request.certificate_hash} revoked on blockchain",
            {
                "certificate_hash": request.certificate_hash,
                "reason": request.reason,
                "revoked_by": request.revoked_by,
                "institution_code": request.institution_code,
                "transaction_id": blockchain_result.get("transaction_id")
            },
            current_user.id
        )
        
        return FabricResponse(
            success=True,
            message="Certificate revoked successfully",
            data={
                "certificate_hash": request.certificate_hash,
                "revocation_reason": request.reason,
                "transaction_id": blockchain_result.get("transaction_id"),
                "block_number": blockchain_result.get("block_number"),
                "revoked_at": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/certificates", response_model=FabricResponse)
def get_all_certificates(
    institution_code: Optional[str] = Query(None, description="Filter by institution code"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all certificates from blockchain"""
    try:
        # Get certificates from blockchain
        blockchain_result = fabric_sdk.get_all_certificates()
        
        if not blockchain_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to retrieve certificates from blockchain")
        
        certificates = blockchain_result.get("certificates", [])
        
        # Filter by institution if specified
        if institution_code:
            certificates = [cert for cert in certificates if cert.get("institutionCode") == institution_code.upper()]
        
        # Apply pagination
        total = len(certificates)
        start = (page - 1) * limit
        end = start + limit
        paginated_certificates = certificates[start:end]
        
        return FabricResponse(
            success=True,
            message="Certificates retrieved successfully",
            data={
                "certificates": paginated_certificates,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Institution Management Endpoints
@router.get("/institutions/{institution_code}", response_model=FabricResponse)
def get_institution(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get institution details from blockchain"""
    try:
        # Get institution from blockchain
        blockchain_result = fabric_sdk.get_institution(institution_code.upper())
        
        if not blockchain_result.get("success"):
            raise HTTPException(status_code=404, detail="Institution not found on blockchain")
        
        return FabricResponse(
            success=True,
            message="Institution retrieved successfully",
            data={
                "institution": blockchain_result.get("institution")
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get institution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/institutions/{institution_code}", response_model=FabricResponse)
def update_institution(
    institution_code: str,
    request: InstitutionUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update institution configuration on blockchain"""
    try:
        # Verify institution exists
        institution = db.query(Institution).filter(
            Institution.code == institution_code.upper()
        ).first()
        
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        # Prepare update data for blockchain
        update_data = {
            "nodeId": request.node_id,
            "institutionCode": institution_code.upper(),
            "institutionName": request.institution_name,
            "nodeType": request.node_type,
            "mspId": request.msp_id,
            "peerId": request.peer_id,
            "channelName": request.channel_name,
            "status": request.status,
            "publicKey": request.public_key,
            "nodeConfigJson": json.dumps(request.node_config) if request.node_config else ""
        }
        
        # Update institution on blockchain
        # Note: This would require implementing the UpdateInstitution function in the chaincode
        # For now, we'll update the database and log the activity
        
        # Update institution in database
        institution.blockchain_node_id = request.node_id
        institution.blockchain_node_status = request.status
        institution.blockchain_network = "fabric"
        institution.msp_id = request.msp_id
        institution.peer_id = request.peer_id
        institution.channel_name = request.channel_name
        institution.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log activity
        log_activity(
            db,
            "update_institution",
            f"Institution {institution_code} configuration updated",
            {
                "institution_code": institution_code,
                "node_type": request.node_type,
                "status": request.status,
                "msp_id": request.msp_id
            },
            current_user.id
        )
        
        return FabricResponse(
            success=True,
            message="Institution updated successfully",
            data={
                "institution_code": institution_code,
                "node_id": request.node_id,
                "status": request.status,
                "updated_at": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update institution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Network Monitoring Endpoints
@router.get("/network/health", response_model=FabricResponse)
def get_network_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get Fabric network health status"""
    try:
        # Check channel health
        health_result = fabric_sdk.check_channel_health()
        
        if not health_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to check network health")
        
        # Get network statistics
        stats_result = fabric_sdk.get_network_statistics()
        
        return FabricResponse(
            success=True,
            message="Network health retrieved successfully",
            data={
                "health": health_result,
                "statistics": stats_result.get("statistics") if stats_result.get("success") else None
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get network health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/network/statistics", response_model=FabricResponse)
def get_network_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get network-wide statistics"""
    try:
        # Get network statistics
        stats_result = fabric_sdk.get_network_statistics()
        
        if not stats_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
        
        return FabricResponse(
            success=True,
            message="Network statistics retrieved successfully",
            data={
                "statistics": stats_result.get("statistics")
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get network statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-logs", response_model=FabricResponse)
def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    institution_code: Optional[str] = Query(None, description="Filter by institution code"),
    certificate_hash: Optional[str] = Query(None, description="Filter by certificate hash"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get audit logs from blockchain"""
    try:
        # Get audit logs from blockchain
        logs_result = fabric_sdk.get_audit_logs(
            event_type=event_type or "",
            institution_code=institution_code or "",
            certificate_hash=certificate_hash or "",
            limit=limit
        )
        
        if not logs_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")
        
        return FabricResponse(
            success=True,
            message="Audit logs retrieved successfully",
            data={
                "audit_logs": logs_result.get("audit_logs"),
                "count": logs_result.get("count", 0),
                "filters": {
                    "event_type": event_type,
                    "institution_code": institution_code,
                    "certificate_hash": certificate_hash,
                    "limit": limit
                }
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def log_activity(db: Session, activity_type: str, message: str, data: Dict[str, Any], user_id: int):
    """Log activity to database"""
    try:
        activity = NodeActivityLog(
            node_id=1,  # Default node ID - would be determined by context
            institution_id=1,  # Default institution ID - would be determined by context
            activity_type=activity_type,
            activity_message=message,
            activity_data=data,
            triggered_by=user_id,
            created_at=datetime.utcnow()
        )
        
        db.add(activity)
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        # Don't raise - logging failure shouldn't break the main operation

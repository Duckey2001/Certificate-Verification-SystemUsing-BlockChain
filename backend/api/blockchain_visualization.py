#!/usr/bin/env python3
"""
Blockchain visualization and monitoring endpoints
Provides real-time blockchain data for frontend visualization
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models import Certificate, AuditEvent, User, Payment, VerificationLog
from database import get_db
from auth import get_current_user
from utils.blockchain_service import BlockchainService

router = APIRouter(prefix="/api/blockchain", tags=["blockchain-visualization"])

@router.get("/network-stats")
def get_network_stats(
    db: Session = Depends(get_db)
):
    """Get comprehensive blockchain network statistics"""
    try:
        # Get real blockchain statistics
        total_certificates = db.query(func.count(Certificate.id)).scalar()
        blockchain_certificates = db.query(func.count(Certificate.id)).filter(
            Certificate.blockchain_tx_id.isnot(None)
        ).scalar()
        
        # Get recent activity
        recent_issuances = db.query(func.count(Certificate.id)).filter(
            Certificate.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).scalar()
        
        recent_verifications = db.query(func.count(VerificationLog.id)).filter(
            VerificationLog.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).scalar()
        
        # Get blockchain blocks (simulated from audit events)
        blockchain_events = db.query(AuditEvent).filter(
            AuditEvent.event_type.in_(['certificate_issued', 'certificate_uploaded']),
            AuditEvent.certificate_hash.isnot(None)
        ).order_by(AuditEvent.created_at.desc()).all()
        
        # Calculate blocks (group by hour)
        block_count = len(set(
            event.created_at.replace(minute=0, second=0, microsecond=0) 
            for event in blockchain_events
        ))
        
        return {
            "totalBlocks": block_count,
            "totalTransactions": blockchain_certificates,
            "certificatesStored": blockchain_certificates,
            "pendingCertificates": total_certificates - blockchain_certificates,
            "recentIssuances": recent_issuances,
            "recentVerifications": recent_verifications,
            "networkStatus": "active",
            "lastBlockTime": blockchain_events[0].created_at.isoformat() if blockchain_events else None,
            "averageBlockTime": "10 minutes", # Simulated
            "networkNodes": 1, # Will be expanded with real node tracking
            "totalUsers": db.query(func.count(User.id)).scalar(),
            "activeInstitutions": db.query(func.count(func.distinct(User.institution_code))).filter(
                User.institution_code.isnot(None),
                User.is_active == True
            ).scalar()
        }
    except Exception as e:
        return {
            "totalBlocks": 0,
            "totalTransactions": 0,
            "certificatesStored": 0,
            "networkStatus": "error",
            "error": str(e)
        }

@router.get("/blocks")
def get_blocks(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get blockchain blocks with transactions"""
    try:
        # Get blockchain events as blocks
        blockchain_events = db.query(AuditEvent).filter(
            AuditEvent.event_type.in_(['certificate_issued', 'certificate_uploaded']),
            AuditEvent.certificate_hash.isnot(None)
        ).order_by(AuditEvent.created_at.desc()).limit(limit).all()
        
        blocks = []
        for i, event in enumerate(blockchain_events):
            # Get certificate details
            cert = db.query(Certificate).filter(
                Certificate.certificate_hash == event.certificate_hash
            ).first()
            
            # Create block from event
            block = {
                "number": i + 1,
                "hash": event.certificate_hash,
                "timestamp": event.created_at.isoformat(),
                "verified": cert.blockchain_tx_id is not None if cert else False,
                "pending": cert.blockchain_tx_id is None if cert else True,
                "transactions": []
            }
            
            # Add transaction if certificate exists
            if cert:
                block["transactions"].append({
                    "hash": cert.certificate_hash,
                    "type": "certificate",
                    "from": cert.issuer_id,
                    "to": "network",
                    "timestamp": cert.created_at.isoformat(),
                    "certificate_id": cert.id,
                    "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                    "blockchain_tx_id": cert.blockchain_tx_id
                })
            
            blocks.append(block)
        
        return {"blocks": blocks}
    except Exception as e:
        return {"blocks": [], "error": str(e)}

@router.get("/transactions")
def get_transactions(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get recent blockchain transactions"""
    try:
        # Get certificates with blockchain transactions
        certificates = db.query(Certificate).filter(
            Certificate.blockchain_tx_id.isnot(None)
        ).order_by(Certificate.created_at.desc()).limit(limit).all()
        
        transactions = []
        for cert in certificates:
            transactions.append({
                "hash": cert.certificate_hash,
                "blockchain_tx_id": cert.blockchain_tx_id,
                "block_number": cert.blockchain_block_number,
                "timestamp": cert.created_at.isoformat(),
                "type": "certificate",
                "from": cert.issuer_id,
                "to": "network",
                "certificate_id": cert.id,
                "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                "institution": cert.institution,
                "status": "confirmed",
                "confirmations": 6 # Simulated
            })
        
        return {"transactions": transactions}
    except Exception as e:
        return {"transactions": [], "error": str(e)}

@router.get("/certificate/{certificate_hash}/verify")
def verify_certificate_on_blockchain(
    certificate_hash: str,
    db: Session = Depends(get_db)
):
    """Verify certificate exists on blockchain"""
    try:
        blockchain_service = BlockchainService()
        verification_result = blockchain_service.verify_hash_on_blockchain(certificate_hash)
        
        # Get certificate details
        cert = db.query(Certificate).filter(
            Certificate.certificate_hash == certificate_hash
        ).first()
        
        return {
            "certificate_hash": certificate_hash,
            "exists": verification_result.get("exists", False),
            "verified": verification_result.get("verified", False),
            "blockchain_tx_id": cert.blockchain_tx_id if cert else None,
            "block_number": cert.blockchain_block_number if cert else None,
            "network": verification_result.get("network", "unknown"),
            "timestamp": verification_result.get("timestamp"),
            "certificate_details": {
                "student_name": f"{cert.student_name} {cert.student_surname}".strip() if cert else None,
                "student_id": cert.student_id if cert else None,
                "institution": cert.institution if cert else None,
                "issue_date": cert.issue_date.isoformat() if cert and cert.issue_date else None
            } if cert else None
        }
    except Exception as e:
        return {
            "certificate_hash": certificate_hash,
            "exists": False,
            "verified": False,
            "error": str(e)
        }

@router.get("/network-health")
def get_network_health(
    db: Session = Depends(get_db)
):
    """Get blockchain network health status"""
    try:
        # Check recent activity
        recent_activity = db.query(AuditEvent).filter(
            AuditEvent.created_at >= datetime.utcnow() - timedelta(minutes=30)
        ).count()
        
        # Check blockchain service
        blockchain_service = BlockchainService()
        service_status = "active" if blockchain_service._hardhat else "simulated"
        
        # Get error rate
        total_events = db.query(AuditEvent).filter(
            AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        error_events = db.query(AuditEvent).filter(
            AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=24),
            AuditEvent.event_type.like('%error%')
        ).count()
        
        error_rate = (error_events / total_events * 100) if total_events > 0 else 0
        
        return {
            "status": "healthy" if recent_activity > 0 else "idle",
            "service_status": service_status,
            "recent_activity": recent_activity,
            "error_rate": error_rate,
            "last_check": datetime.utcnow().isoformat(),
            "uptime": "99.9%", # Simulated
            "nodes": 1, # Will be expanded
            "gas_price": "20 gwei", # Simulated
            "block_time": "10 seconds" # Simulated
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

@router.get("/institution-activity")
def get_institution_blockchain_activity(
    institution_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get blockchain activity for institution"""
    try:
        # Filter by institution if provided
        if institution_code:
            institution_certs = db.query(Certificate).filter(
                Certificate.institution == institution_code,
                Certificate.blockchain_tx_id.isnot(None)
            ).all()
        else:
            # Use current user's institution
            institution_certs = db.query(Certificate).filter(
                Certificate.institution == current_user.institution_code,
                Certificate.blockchain_tx_id.isnot(None)
            ).all()
        
        activity = []
        for cert in institution_certs:
            activity.append({
                "certificate_hash": cert.certificate_hash,
                "blockchain_tx_id": cert.blockchain_tx_id,
                "timestamp": cert.created_at.isoformat(),
                "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                "student_id": cert.student_id,
                "status": "verified",
                "block_number": cert.blockchain_block_number
            })
        
        return {
            "institution_code": institution_code or current_user.institution_code,
            "total_certificates": len(activity),
            "activity": activity
        }
    except Exception as e:
        return {
            "institution_code": institution_code or current_user.institution_code,
            "total_certificates": 0,
            "activity": [],
            "error": str(e)
        }

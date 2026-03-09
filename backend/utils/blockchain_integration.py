#!/usr/bin/env python3
"""
Blockchain integration utilities for certificate operations
Enhanced with comprehensive logging and monitoring
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import json

from models import Certificate, AuditEvent
from utils.blockchain_service import BlockchainService
from utils.network_monitor import get_network_monitor


class BlockchainIntegration:
    """Enhanced blockchain integration with comprehensive monitoring"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.blockchain_service = BlockchainService()
        self.monitor = get_network_monitor(db_session)
    
    def issue_certificate_on_blockchain(self, certificate: Certificate, user_id: str) -> Dict[str, Any]:
        """Issue certificate on blockchain with comprehensive logging"""
        try:
            # Create certificate hash if not exists
            if not certificate.certificate_hash:
                hash_result = self.blockchain_service.create_certificate_hash(certificate)
                certificate.certificate_hash = hash_result["hash"]
                self.db.commit()
            
            # Store on blockchain
            blockchain_data = {
                "certificate_hash": certificate.certificate_hash,
                "student_name": f"{certificate.student_name} {certificate.student_surname}".strip(),
                "student_id": certificate.student_id,
                "institution": certificate.institution,
                "issue_date": certificate.issue_date.isoformat() if certificate.issue_date else None,
                "examination_year": certificate.examination_year,
                "subjects": certificate.subjects
            }
            
            blockchain_result = self.blockchain_service.store_hash_on_blockchain(blockchain_data)
            
            if blockchain_result.get("success"):
                # Update certificate record
                certificate.blockchain_tx_id = blockchain_result.get("transaction_id")
                certificate.blockchain_network = blockchain_result.get("network", "hardhat")
                certificate.blockchain_block_number = blockchain_result.get("block_number")
                certificate.status = "verified"
                certificate.updated_at = datetime.utcnow()
                
                # Log blockchain operation
                self.monitor.log_blockchain_operation(
                    operation_type="certificate_issued",
                    certificate_hash=certificate.certificate_hash,
                    transaction_id=blockchain_result.get("transaction_id"),
                    user_id=user_id,
                    details={
                        "network": blockchain_result.get("network"),
                        "block_number": blockchain_result.get("block_number"),
                        "institution": certificate.institution,
                        "student_name": f"{certificate.student_name} {certificate.student_surname}".strip(),
                        "gas_used": blockchain_result.get("gas_used")
                    }
                )
                
                # Log certificate lifecycle event
                self.monitor.log_certificate_lifecycle(
                    certificate_id=certificate.id,
                    event_type="blockchain_issued",
                    user_id=user_id,
                    details={
                        "blockchain_tx_id": blockchain_result.get("transaction_id"),
                        "blockchain_network": blockchain_result.get("network"),
                        "block_number": blockchain_result.get("block_number")
                    }
                )
                
                self.db.commit()
                
                return {
                    "success": True,
                    "certificate_hash": certificate.certificate_hash,
                    "transaction_id": blockchain_result.get("transaction_id"),
                    "block_number": blockchain_result.get("block_number"),
                    "network": blockchain_result.get("network"),
                    "message": "Certificate successfully issued on blockchain"
                }
            else:
                # Log failure
                self.monitor.log_blockchain_operation(
                    operation_type="certificate_issue_failed",
                    certificate_hash=certificate.certificate_hash,
                    user_id=user_id,
                    details={
                        "error": blockchain_result.get("error"),
                        "institution": certificate.institution
                    }
                )
                
                return {
                    "success": False,
                    "error": blockchain_result.get("error"),
                    "message": "Failed to issue certificate on blockchain"
                }
                
        except Exception as e:
            # Log exception
            self.monitor.log_blockchain_operation(
                operation_type="certificate_issue_error",
                certificate_hash=certificate.certificate_hash if certificate else "unknown",
                user_id=user_id,
                details={
                    "error": str(e),
                    "exception_type": type(e).__name__
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error issuing certificate on blockchain"
            }
    
    def verify_certificate_on_blockchain(self, certificate_hash: str, user_id: str) -> Dict[str, Any]:
        """Verify certificate on blockchain with comprehensive logging"""
        try:
            # Get certificate details
            certificate = self.db.query(Certificate).filter(
                Certificate.certificate_hash == certificate_hash
            ).first()
            
            if not certificate:
                return {
                    "success": False,
                    "error": "Certificate not found",
                    "message": "Certificate with this hash does not exist"
                }
            
            # Verify on blockchain
            verification_result = self.blockchain_service.verify_hash_on_blockchain(certificate_hash)
            
            # Log verification attempt
            self.monitor.log_blockchain_operation(
                operation_type="certificate_verification",
                certificate_hash=certificate_hash,
                user_id=user_id,
                details={
                    "exists": verification_result.get("exists", False),
                    "verified": verification_result.get("verified", False),
                    "network": verification_result.get("network", "unknown"),
                    "institution": certificate.institution,
                    "student_name": f"{certificate.student_name} {certificate.student_surname}".strip()
                }
            )
            
            # Log certificate lifecycle event
            self.monitor.log_certificate_lifecycle(
                certificate_id=certificate.id,
                event_type="blockchain_verified",
                user_id=user_id,
                details={
                    "verification_result": verification_result.get("verified", False),
                    "network": verification_result.get("network", "unknown")
                }
            )
            
            return {
                "success": True,
                "certificate_hash": certificate_hash,
                "exists": verification_result.get("exists", False),
                "verified": verification_result.get("verified", False),
                "network": verification_result.get("network", "unknown"),
                "certificate_details": {
                    "student_name": f"{certificate.student_name} {certificate.student_surname}".strip(),
                    "student_id": certificate.student_id,
                    "institution": certificate.institution,
                    "issue_date": certificate.issue_date.isoformat() if certificate.issue_date else None,
                    "status": certificate.status,
                    "blockchain_tx_id": certificate.blockchain_tx_id
                },
                "message": "Certificate verification completed"
            }
            
        except Exception as e:
            # Log exception
            self.monitor.log_blockchain_operation(
                operation_type="certificate_verification_error",
                certificate_hash=certificate_hash,
                user_id=user_id,
                details={
                    "error": str(e),
                    "exception_type": type(e).__name__
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error verifying certificate on blockchain"
            }
    
    def report_certificate_tampering(self, certificate_hash: str, computed_hash: str, user_id: str) -> Dict[str, Any]:
        """Report certificate tampering on blockchain"""
        try:
            # Get certificate details
            certificate = self.db.query(Certificate).filter(
                Certificate.certificate_hash == certificate_hash
            ).first()
            
            if not certificate:
                return {
                    "success": False,
                    "error": "Certificate not found",
                    "message": "Certificate with this hash does not exist"
                }
            
            # Report tampering on blockchain
            tamper_result = self.blockchain_service.report_tamper(certificate_hash, computed_hash)
            
            if tamper_result.get("success"):
                # Update certificate status
                certificate.status = "tampered"
                certificate.updated_at = datetime.utcnow()
                
                # Log tampering report
                self.monitor.log_blockchain_operation(
                    operation_type="certificate_tampering_reported",
                    certificate_hash=certificate_hash,
                    transaction_id=tamper_result.get("transaction_id"),
                    user_id=user_id,
                    details={
                        "expected_hash": certificate_hash,
                        "computed_hash": computed_hash,
                        "network": tamper_result.get("network", "hardhat"),
                        "institution": certificate.institution,
                        "student_name": f"{certificate.student_name} {certificate.student_surname}".strip()
                    }
                )
                
                # Log certificate lifecycle event
                self.monitor.log_certificate_lifecycle(
                    certificate_id=certificate.id,
                    event_type="tampering_detected",
                    user_id=user_id,
                    details={
                        "expected_hash": certificate_hash,
                        "computed_hash": computed_hash,
                        "transaction_id": tamper_result.get("transaction_id")
                    }
                )
                
                self.db.commit()
                
                return {
                    "success": True,
                    "certificate_hash": certificate_hash,
                    "transaction_id": tamper_result.get("transaction_id"),
                    "network": tamper_result.get("network", "hardhat"),
                    "message": "Certificate tampering successfully reported on blockchain"
                }
            else:
                # Log failure
                self.monitor.log_blockchain_operation(
                    operation_type="tampering_report_failed",
                    certificate_hash=certificate_hash,
                    user_id=user_id,
                    details={
                        "error": tamper_result.get("error"),
                        "expected_hash": certificate_hash,
                        "computed_hash": computed_hash
                    }
                )
                
                return {
                    "success": False,
                    "error": tamper_result.get("error"),
                    "message": "Failed to report certificate tampering on blockchain"
                }
                
        except Exception as e:
            # Log exception
            self.monitor.log_blockchain_operation(
                operation_type="tampering_report_error",
                certificate_hash=certificate_hash,
                user_id=user_id,
                details={
                    "error": str(e),
                    "exception_type": type(e).__name__,
                    "computed_hash": computed_hash
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error reporting certificate tampering on blockchain"
            }
    
    def get_blockchain_status(self) -> Dict[str, Any]:
        """Get current blockchain status and health"""
        try:
            # Get blockchain service status
            is_real_chain = self.blockchain_service._hardhat is not None
            
            # Get certificate statistics
            total_certificates = self.db.query(Certificate).count()
            blockchain_certificates = self.db.query(Certificate).filter(
                Certificate.blockchain_tx_id.isnot(None)
            ).count()
            
            # Get recent blockchain operations
            recent_operations = self.db.query(AuditEvent).filter(
                AuditEvent.event_type.like('blockchain_%'),
                AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                "status": "active" if is_real_chain else "simulated",
                "network_type": "hardhat" if is_real_chain else "simulation",
                "total_certificates": total_certificates,
                "blockchain_certificates": blockchain_certificates,
                "blockchain_rate": (blockchain_certificates / total_certificates * 100) if total_certificates > 0 else 0,
                "recent_operations_24h": recent_operations,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }

# Factory function
def get_blockchain_integration(db_session) -> BlockchainIntegration:
    """Get blockchain integration instance"""
    return BlockchainIntegration(db_session)

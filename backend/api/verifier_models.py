from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models import Base, User


def generate_uuid():
    return str(uuid.uuid4())


class VerifierCredential(Base):
    """
    Enhanced verifier credentials with blockchain integration
    """
    __tablename__ = "verifier_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    credential_id = Column(String(100), unique=True, nullable=False, index=True)  # Unique verifier ID
    
    # Professional information
    license_number = Column(String(100), unique=True, nullable=True)  # Professional license
    specialization = Column(String(100), nullable=True)  # Area of expertise
    qualification_level = Column(String(50), nullable=True)  # PhD, Masters, Bachelor, etc.
    institution_affiliation = Column(String(255), nullable=True)
    years_experience = Column(Integer, default=0)
    
    # Verification authority
    verification_scope = Column(JSON, nullable=True)  # Types of certificates they can verify
    max_verification_amount = Column(Float, default=1000.0)  # Maximum value per verification
    daily_verification_limit = Column(Integer, default=50)  # Max verifications per day
    
    # Credentials and certificates
    professional_certificates = Column(JSON, nullable=True)  # Array of certificate details
    background_check_status = Column(String(20), default="pending")  # pending, passed, failed
    background_check_date = Column(DateTime, nullable=True)
    accreditation_status = Column(String(20), default="pending")  # pending, approved, rejected, suspended
    
    # Blockchain integration
    blockchain_wallet_address = Column(String(255), nullable=True)
    blockchain_verifier_id = Column(String(100), nullable=True)  # ID on blockchain
    credential_hash = Column(String(64), unique=True, nullable=True)  # Hash of credentials
    blockchain_registered = Column(Boolean, default=False)
    blockchain_tx_id = Column(String(200), nullable=True)
    blockchain_network = Column(String(50), nullable=True)
    
    # Status and metrics
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_count = Column(Integer, default=0)
    successful_verifications = Column(Integer, default=0)
    reputation_score = Column(Float, default=100.0)  # 0-100 reputation score
    last_verification_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Credential expiration
    
    # Relationships
    user = relationship("User", backref="verifier_credentials")


class VerifierAttestation(Base):
    """
    Blockchain attestations for verifier credentials
    """
    __tablename__ = "verifier_attestations"
    
    id = Column(Integer, primary_key=True, index=True)
    verifier_credential_id = Column(Integer, ForeignKey("verifier_credentials.id"), nullable=False, index=True)
    attestation_type = Column(String(50), nullable=False)  # identity, qualification, background_check
    attestation_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Blockchain data
    blockchain_tx_id = Column(String(200), nullable=True)
    blockchain_network = Column(String(50), nullable=True)
    block_number = Column(Integer, nullable=True)
    block_timestamp = Column(DateTime, nullable=True)
    
    # Attestation details
    issuer = Column(String(255), nullable=True)  # Who issued the attestation
    issuer_address = Column(String(255), nullable=True)  # Blockchain address of issuer
    signature = Column(Text, nullable=True)  # Digital signature
    metadata = Column(JSON, nullable=True)
    
    # Status
    is_valid = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verifier_credential = relationship("VerifierCredential", backref="attestations")


class VerifierAuditLog(Base):
    """
    Comprehensive audit log for verifier activities
    """
    __tablename__ = "verifier_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    verifier_credential_id = Column(Integer, ForeignKey("verifier_credentials.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)  # registration, login, verification, credential_update
    action = Column(String(100), nullable=False)  # Specific action performed
    description = Column(Text, nullable=True)
    
    # Related entities
    certificate_hash = Column(String(64), nullable=True, index=True)
    verification_request_id = Column(Integer, nullable=True, index=True)
    blockchain_tx_id = Column(String(200), nullable=True, index=True)
    
    # System information
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Results and status
    status = Column(String(20), nullable=False)  # success, failed, pending
    error_message = Column(Text, nullable=True)
    
    # Changes tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    verifier_credential = relationship("VerifierCredential", backref="audit_logs")
    user = relationship("User", backref="verifier_activities")

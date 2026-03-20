from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    google_id = Column(String(255), unique=True, index=True, nullable=True)  # Google OAuth ID
    github_id = Column(String(255), unique=True, index=True, nullable=True)  # GitHub OAuth ID
    role = Column(String(50), nullable=False)  # admin, issuer, verifier
    institution_code = Column(String(50), nullable=True)  # Foreign key to institutions
    institution = Column(String(255))
    badge = Column(String(100))
    invited_by = Column(Integer, ForeignKey("users.id"))
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Credits and billing
    available_credits = Column(Integer, default=0, nullable=False)
    total_credits_purchased = Column(Integer, default=0, nullable=False)
    credit_balance_updated_at = Column(DateTime, nullable=True)
    
    # Blockchain integration
    blockchain_wallet_address = Column(String(255), nullable=True)
    blockchain_public_key = Column(Text, nullable=True)
    blockchain_user_id = Column(String(100), nullable=True)  # ID on blockchain
    
    # Statistics
    certificates_issued = Column(Integer, default=0, nullable=False)
    certificates_verified = Column(Integer, default=0, nullable=False)
    ocr_scans_today = Column(Integer, default=0, nullable=False)
    last_activity_at = Column(DateTime, nullable=True)
    # OAuth Integration
    google_access_token = Column(String(500), nullable=True)
    google_refresh_token = Column(String(500), nullable=True)
    google_token_expires_at = Column(DateTime, nullable=True)
    google_profile_data = Column(JSON, nullable=True)
    oauth_provider = Column(String(50), default='password')  # password, google, github
    last_oauth_login_at = Column(DateTime, nullable=True)
    
    # Profile Settings
    profile_completion_score = Column(Integer, default=0)
    profile_visibility = Column(String(20), default='public')  # public, private, institution
    profile_theme = Column(String(20), default='light')  # light, dark, auto
    language_preference = Column(String(10), default='en')
    timezone = Column(String(50), default='UTC')
    date_format = Column(String(20), default='YYYY-MM-DD')
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    
    # Notification Settings
    fcm_token = Column(String(500), nullable=True)  # Firebase Cloud Messaging token
    notification_preferences = Column(JSON, nullable=True)  # User notification preferences
    
    # Security Features
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    backup_codes = Column(Text, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    last_password_reset_at = Column(DateTime, nullable=True)
    security_questions = Column(JSON, nullable=True)
    device_fingerprints = Column(JSON, nullable=True)
    
    # Legacy fields for compatibility
    profile_image = Column(LargeBinary, nullable=True)  # Store profile image as binary
    profile_image_url = Column(String(500), nullable=True)  # Store image URL
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    certificates = relationship("Certificate", back_populates="issuer")
    verification_requests_made = relationship("VerificationRequest", foreign_keys="[VerificationRequest.requester_id]", back_populates="requester")
    verification_requests_received = relationship("VerificationRequest", foreign_keys="[VerificationRequest.verifier_id]", back_populates="verifier")
    invitations_sent = relationship("Invitation", foreign_keys="[Invitation.inviter_id]", back_populates="inviter")
    badges = relationship("Badge", back_populates="user")
    verification_logs = relationship("VerificationLog", back_populates="verifier")
    profile_pictures = relationship("ProfilePicture", back_populates="user", cascade="all, delete-orphan")
    user_preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    ocr_history = relationship("OCRHistory", back_populates="user", cascade="all, delete-orphan")


class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_hash = Column(String(64), unique=True, index=True, nullable=False)
    student_id = Column(String(50), nullable=False)
    student_name = Column(String(100), nullable=False)
    student_surname = Column(String(100), nullable=False)
    examination_year = Column(Integer, nullable=False)
    subjects = Column(JSON, nullable=False)
    credits = Column(Integer)
    issue_date = Column(String(10), nullable=False)
    issuer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_image_path = Column(String(500))
    extracted_data = Column(JSON)
    status = Column(String(20), default="pending")
    verification_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # University reference
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)
    reference_number = Column(String(100), unique=True, nullable=True, index=True)
    
    # Payment tracking
    payment_status = Column(String(20), default="unpaid")  # unpaid, paid, refunded
    paid_at = Column(DateTime, nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    # Blockchain metadata (for real chain integration)
    blockchain_tx_id = Column(String(200), nullable=True)
    blockchain_network = Column(String(50), nullable=True)  # e.g. hardhat, sepolia, fabric
    blockchain_block_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issuer = relationship("User", back_populates="certificates")
    verification_requests = relationship("VerificationRequest", foreign_keys="[VerificationRequest.certificate_id]", back_populates="certificate")
    university = relationship("University", back_populates="certificates")
    ocr_history = relationship("OCRHistory", back_populates="certificate", cascade="all, delete-orphan")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True)
    certificate_hash = Column(String(64), ForeignKey("certificates.certificate_hash"), nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    uploaded_image_path = Column(String(500), nullable=True)
    extracted_info = Column(JSON, nullable=True)
    computed_hash = Column(String(64), nullable=True)
    blockchain_match = Column(Boolean, nullable=True)
    
    # Legacy payment fields
    payment_method = Column(String(20), nullable=True)  # mpesa, ecocash, bank
    payment_digits = Column(String(6), nullable=True)
    payment_status = Column(String(20), default="pending")  # pending, confirmed, manual_review, failed
    payment_reference = Column(String(100), nullable=True)
    verification_fee = Column(Float, default=5.0)  # 5 Maloti
    
    # Request details
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    result = Column(String(20), nullable=True)  # valid, invalid, pending
    verification_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    certificate = relationship("Certificate", foreign_keys=[certificate_id], back_populates="verification_requests")
    requester = relationship("User", foreign_keys=[requester_id], back_populates="verification_requests_made")
    verifier = relationship("User", foreign_keys=[verifier_id], back_populates="verification_requests_received")
    payment = relationship("Payment", foreign_keys=[payment_id])


class Payment(Base):
    """
    Enhanced Payment record with M-Pesa B2B integration support.
    Keeps a durable history even if verification is retried.
    """
    __tablename__ = "payments"

    id = Column(String(100), primary_key=True, default=generate_uuid, index=True)
    verification_request_id = Column(Integer, ForeignKey("verification_requests.id"), nullable=True, index=True)
    payer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Payment details
    method = Column(String(50), nullable=False)  # mpesa_b2b, bank_transfer, etc.
    reference = Column(String(100), nullable=False, unique=True)  # Certificate reference
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="LSL")
    status = Column(String(20), default="pending")  # pending, confirmed, failed, refunded
    
    # M-Pesa specific fields
    mpesa_transaction_id = Column(String(100), nullable=True, unique=True)
    mpesa_conversation_id = Column(String(100), nullable=True)
    mpesa_response_code = Column(String(20), nullable=True)
    mpesa_response_description = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Additional data
    failure_reason = Column(String(255), nullable=True)
    payment_metadata = Column(JSON, nullable=True)  # Store additional M-Pesa response data
    
    # Legacy fields for compatibility
    digits = Column(String(6), nullable=True)  # Keep for backward compatibility
    mpesa_merchant_request_id = Column(String(100), nullable=True)
    mpesa_checkout_request_id = Column(String(100), nullable=True)
    mpesa_customer_message = Column(String(255), nullable=True)
    mpesa_phone_number = Column(String(20), nullable=True)
    mpesa_amount = Column(Float, nullable=True)
    mpesa_transaction_date = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    payer = relationship("User", foreign_keys=[payer_user_id])
    verification_request = relationship("VerificationRequest", foreign_keys=[verification_request_id])
    callbacks = relationship("PaymentCallback", back_populates="payment")


class PaymentCallback(Base):
    """
    Payment callback record for M-Pesa and other payment providers.
    """
    __tablename__ = "payment_callbacks"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # mpesa, ecocash, bank
    callback_data = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    payment = relationship("Payment", back_populates="callbacks")


class University(Base):
    """
    University/Institution model for certificate issuers
    """
    __tablename__ = "universities"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    mpesa_paybill = Column(String(20), nullable=True)  # M-Pesa paybill number
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    certificates = relationship("Certificate", back_populates="university")


class AuditEvent(Base):
    """
    Append-only audit log for uploads, verifications, tamper reports, payments, and blockchain events.
    Used by dashboards and SSE notifications.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String(50), nullable=True)
    certificate_hash = Column(String(64), nullable=True, index=True)
    verification_request_id = Column(Integer, ForeignKey("verification_requests.id"), nullable=True, index=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class LoginActivity(Base):
    __tablename__ = "login_activity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, index=True)  # success, failed
    login_method = Column(String(50), nullable=True)  # password, google, github
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(255), primary_key=True, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    expires = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    last_activity_at = Column(DateTime, nullable=True)
    logout_reason = Column(String(50), nullable=True)
    force_logout_at = Column(DateTime, nullable=True)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Invitation(Base):
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    token = Column(String(36), default=generate_uuid, unique=True, index=True)
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="invitations_sent")


class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_type = Column(String(50), nullable=False)
    badge_name = Column(String(100), nullable=False)
    description = Column(Text)
    awarded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="badges")


class Institution(Base):
    """
    Simple institution registry, loosely matching the PostgreSQL dump.
    Used for admin views and to link users to institution codes.
    """
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # ISSUER or VERIFIER
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Blockchain node information
    blockchain_node_id = Column(String(100), unique=True, nullable=True, index=True)
    blockchain_node_url = Column(String(500), nullable=True)
    blockchain_node_port = Column(Integer, nullable=True)
    blockchain_node_status = Column(String(20), default="inactive")  # inactive, active, syncing, error
    blockchain_network = Column(String(50), nullable=True)  # fabric, ethereum, hyperledger
    chaincode_version = Column(String(20), nullable=True)
    chaincode_name = Column(String(100), nullable=True)
    node_public_key = Column(Text, nullable=True)
    node_private_key = Column(Text, nullable=True)  # Encrypted
    msp_id = Column(String(100), nullable=True)  # Membership Service Provider ID
    peer_id = Column(String(100), nullable=True)
    orderer_id = Column(String(100), nullable=True)
    channel_name = Column(String(100), nullable=True)
    chaincode_installed = Column(Boolean, default=False)
    chaincode_instantiated = Column(Boolean, default=False)
    last_sync_at = Column(DateTime, nullable=True)
    node_config = Column(JSON, nullable=True)  # Additional node configuration


class VerificationLog(Base):
    """
    Verification log for tracking certificate verification attempts and results.
    """
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    certificate_hash = Column(String(64), nullable=False, index=True)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    verification_method = Column(String(50), nullable=False)  # hash, file, qr_code
    verification_result = Column(String(20), nullable=False)  # valid, invalid, failed
    verification_details = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    verifier = relationship("User", back_populates="verification_logs")


class Notification(Base):
    """
    Real-time notifications for all system events
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # certificate_issued, verified, payment, system
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    is_read = Column(Boolean, default=False, nullable=False)
    action_url = Column(String(500), nullable=True)  # URL for action button
    action_text = Column(String(100), nullable=True)  # Text for action button
    metadata_json = Column(JSON, nullable=True)  # Additional data
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")


class SystemActivity(Base):
    """
    Comprehensive activity logging for admin dashboard
    """
    __tablename__ = "system_activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_type = Column(String(50), nullable=False, index=True)  # login, certificate_issue, verification, payment
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String(50), nullable=True)
    actor_name = Column(String(255), nullable=True)  # Denormalized for quick display
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    institution_code = Column(String(50), nullable=True, index=True)
    certificate_hash = Column(String(64), nullable=True, index=True)
    verification_request_id = Column(Integer, nullable=True, index=True)
    payment_id = Column(Integer, nullable=True, index=True)
    
    # Activity details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)  # success, failed, pending
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Blockchain tracking
    blockchain_tx_id = Column(String(200), nullable=True)
    blockchain_block_number = Column(Integer, nullable=True)
    blockchain_network = Column(String(50), nullable=True)
    
    # Additional metadata
    metadata_json = Column(JSON, nullable=True)
    impact_score = Column(Integer, default=1)  # 1-10 for importance ranking
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    actor = relationship("User", foreign_keys=[actor_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])


class BlockchainTransaction(Base):
    """
    Track all blockchain transactions for audit and verification
    """
    __tablename__ = "blockchain_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_hash = Column(String(200), unique=True, nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # certificate_issue, user_registration, verification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    certificate_hash = Column(String(64), nullable=True, index=True)
    network = Column(String(50), nullable=False)  # hardhat, sepolia, mainnet
    block_number = Column(Integer, nullable=True)
    block_hash = Column(String(200), nullable=True)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(String(50), nullable=True)
    transaction_fee = Column(Float, nullable=True)
    status = Column(String(20), default="pending")  # pending, confirmed, failed
    confirmations = Column(Integer, default=0)
    contract_address = Column(String(200), nullable=True)
    method_called = Column(String(100), nullable=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")


class ProfilePicture(Base):
    """Profile pictures for users"""
    __tablename__ = "profile_pictures"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile_pictures")


class UserPreference(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dashboard_layout = Column(JSON, default={})
    notification_settings = Column(JSON, default={})
    privacy_settings = Column(JSON, default={})
    accessibility_settings = Column(JSON, default={})
    custom_settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")


class AuditLog(Base):
    """Audit logs for all user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    status = Column(String(20), default='success')
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class BlockchainNode(Base):
    """
    Blockchain node management for institutions
    """
    __tablename__ = "blockchain_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(100), unique=True, nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    node_type = Column(String(50), nullable=False)  # peer, orderer, ca, validator
    network_type = Column(String(50), nullable=False)  # fabric, ethereum, hyperledger
    
    # Network configuration
    url = Column(String(500), nullable=False)
    port = Column(Integer, nullable=False)
    tls_enabled = Column(Boolean, default=True)
    tls_cert_path = Column(String(500), nullable=True)
    tls_key_path = Column(String(500), nullable=True)
    ca_cert_path = Column(String(500), nullable=True)
    
    # Node identity
    msp_id = Column(String(100), nullable=True)
    peer_id = Column(String(100), nullable=True)
    orderer_id = Column(String(100), nullable=True)
    node_public_key = Column(Text, nullable=True)
    node_private_key = Column(Text, nullable=True)  # Encrypted
    node_certificates = Column(JSON, nullable=True)  # Store certificates
    
    # Chaincode information
    chaincode_name = Column(String(100), nullable=True)
    chaincode_version = Column(String(20), nullable=True)
    chaincode_path = Column(String(500), nullable=True)
    chaincode_installed = Column(Boolean, default=False)
    chaincode_instantiated = Column(Boolean, default=False)
    channel_name = Column(String(100), nullable=True)
    
    # Node status
    status = Column(String(20), default="inactive")  # inactive, active, syncing, error, maintenance
    last_heartbeat = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    block_height = Column(Integer, default=0)
    network_height = Column(Integer, default=0)
    
    # Configuration
    node_config = Column(JSON, nullable=True)
    genesis_block = Column(Text, nullable=True)
    configtxlator_path = Column(String(500), nullable=True)
    cryptogen_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    installed_at = Column(DateTime, nullable=True)
    
    # Relationships
    institution = relationship("Institution")
    chaincode_deployments = relationship("ChaincodeDeployment", back_populates="node")


class ChaincodeDeployment(Base):
    """
    Chaincode deployment tracking for blockchain nodes
    """
    __tablename__ = "chaincode_deployments"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(String(100), unique=True, nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("blockchain_nodes.id"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Chaincode details
    chaincode_name = Column(String(100), nullable=False)
    chaincode_version = Column(String(20), nullable=False)
    chaincode_path = Column(String(500), nullable=False)
    chaincode_language = Column(String(20), default="go")  # go, java, node
    
    # Deployment information
    channel_name = Column(String(100), nullable=True)
    endorsement_policy = Column(JSON, nullable=True)
    collection_config = Column(JSON, nullable=True)  # Private data collections
    init_required = Column(Boolean, default=True)
    init_args = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, installing, instantiated, failed, active
    install_tx_id = Column(String(200), nullable=True)
    instantiate_tx_id = Column(String(200), nullable=True)
    package_id = Column(String(200), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    installed_at = Column(DateTime, nullable=True)
    instantiated_at = Column(DateTime, nullable=True)
    
    # Relationships
    node = relationship("BlockchainNode", back_populates="chaincode_deployments")
    institution = relationship("Institution")


class NodeActivityLog(Base):
    """
    Activity log for blockchain nodes
    """
    __tablename__ = "node_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("blockchain_nodes.id"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)  # start, stop, sync, deploy, error
    activity_message = Column(Text, nullable=False)
    activity_data = Column(JSON, nullable=True)
    
    # Status information
    status_before = Column(String(20), nullable=True)
    status_after = Column(String(20), nullable=True)
    block_height_before = Column(Integer, nullable=True)
    block_height_after = Column(Integer, nullable=True)
    
    # Error information
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Metadata
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    node = relationship("BlockchainNode")
    institution = relationship("Institution")
    user = relationship("User")


class OCRHistory(Base):
    """
    Track OCR processing history for certificate extraction
    """
    __tablename__ = "ocr_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    
    # OCR results
    extracted_data = Column(JSON, nullable=True)  # Full extracted data
    extracted_text = Column(Text, nullable=True)  # Raw extracted text
    extracted_fields = Column(JSON, nullable=True)  # Structured fields
    confidence = Column(Float, default=0)  # Overall confidence score (0-100)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Processing metadata
    processing_time_ms = Column(Integer, nullable=True)  # Time taken in milliseconds
    ocr_engine_used = Column(String(100), nullable=True)  # Which OCR engine was used
    api_calls_made = Column(JSON, nullable=True)  # Record of API calls
    warnings = Column(JSON, nullable=True)  # Any warnings during processing
    
    # Link to created certificate
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ocr_history")
    certificate = relationship("Certificate", back_populates="ocr_history")
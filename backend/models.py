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
    profile_image = Column(LargeBinary, nullable=True)  # Store profile image as binary
    profile_image_url = Column(String(500), nullable=True)  # Store image URL
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
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    certificates = relationship("Certificate", back_populates="issuer")
    verification_requests = relationship("VerificationRequest", back_populates="verifier")
    invitations_sent = relationship("Invitation", foreign_keys="[Invitation.inviter_id]", back_populates="inviter")
    badges = relationship("Badge", back_populates="user")
    verification_logs = relationship("VerificationLog", back_populates="verifier")

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
    # Blockchain metadata (for real chain integration)
    blockchain_tx_id = Column(String(200), nullable=True)
    blockchain_network = Column(String(50), nullable=True)  # e.g. hardhat, sepolia, fabric
    blockchain_block_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issuer = relationship("User", back_populates="certificates")
    verifications = relationship("VerificationRequest", back_populates="certificate")

class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_hash = Column(String(64), ForeignKey("certificates.certificate_hash"), nullable=True)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_image_path = Column(String(500), nullable=False)
    extracted_info = Column(JSON, nullable=False)
    computed_hash = Column(String(64), nullable=False)
    blockchain_match = Column(Boolean, nullable=False)
    payment_method = Column(String(20), nullable=True)  # mpesa, ecocash, bank
    payment_digits = Column(String(6), nullable=False)
    payment_status = Column(String(20), default="confirmed")  # pending, confirmed, manual_review, failed
    payment_reference = Column(String(100), nullable=True)
    verification_fee = Column(Float, default=5.0)  # 5 Maloti
    result = Column(String(20), nullable=False)  # valid, invalid, pending
    verification_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    certificate = relationship("Certificate", back_populates="verifications")
    verifier = relationship("User", back_populates="verification_requests")


class Payment(Base):
    """
    Payment record with M-Pesa integration support.
    Keeps a durable history even if verification is retried.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    verification_request_id = Column(Integer, ForeignKey("verification_requests.id"), nullable=True, index=True)
    payer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    method = Column(String(20), nullable=False)  # mpesa, ecocash, bank
    digits = Column(String(6), nullable=False)
    reference = Column(String(100), nullable=True)
    amount = Column(Float, default=5.0)
    status = Column(String(20), default="pending")  # pending, confirmed, manual_review, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    # M-Pesa specific fields
    mpesa_merchant_request_id = Column(String(100), nullable=True)
    mpesa_checkout_request_id = Column(String(100), nullable=True)
    mpesa_response_code = Column(String(10), nullable=True)
    mpesa_response_description = Column(String(255), nullable=True)
    mpesa_customer_message = Column(String(255), nullable=True)
    mpesa_transaction_id = Column(String(50), nullable=True)  # MpesaReceiptNumber
    mpesa_phone_number = Column(String(20), nullable=True)
    mpesa_amount = Column(Float, nullable=True)
    mpesa_transaction_date = Column(String(50), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Relationships
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

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


class CreditTransaction(Base):
    """
    Track all credit purchases and usage
    """
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # purchase, usage, refund, bonus
    amount = Column(Integer, nullable=False)  # Positive for credits gained, negative for used
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    reference_type = Column(String(50), nullable=True)  # certificate, verification, payment
    reference_id = Column(Integer, nullable=True)
    payment_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")

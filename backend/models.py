from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
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
    role = Column(String(50), nullable=False)  # admin, issuer, verifier
    institution = Column(String(255))
    badge = Column(String(100))
    invited_by = Column(Integer, ForeignKey("users.id"))
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

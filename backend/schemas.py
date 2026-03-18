from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    ISSUER = "issuer"
    VERIFIER = "verifier"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    institution: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole
    invitation_token: Optional[str] = None
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserResponse(UserBase):
    id: int
    role: str
    badge: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole

class InvitationResponse(BaseModel):
    invitation_link: str
    token: str
    expires_at: datetime

class Subject(BaseModel):
    name: str
    grade: str
    credits: int

class CertificateCreate(BaseModel):
    student_id: str
    student_name: str
    student_surname: str
    examination_year: int
    subjects: List[Subject]
    credits: Optional[int] = None
    issue_date: str

class CertificateResponse(CertificateCreate):
    id: int
    certificate_hash: str
    issuer_id: int
    original_image_path: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class VerificationRequestBase(BaseModel):
    payment_digits: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None

class VerificationResponse(BaseModel):
    id: int
    certificate_hash: Optional[str] = None
    uploaded_image_path: str
    extracted_info: Dict[str, Any]
    computed_hash: str
    blockchain_match: bool
    payment_method: Optional[str] = None
    payment_digits: str
    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None
    result: str
    verification_date: datetime
    
    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_users: Optional[int] = 0
    total_certificates: Optional[int] = 0
    total_verifications: Optional[int] = 0
    valid_verifications: Optional[int] = 0
    invalid_verifications: Optional[int] = 0

class ActivityRecord(BaseModel):
    username: str
    role: str
    institution: Optional[str]
    result: str
    verification_date: datetime

class AdminDashboardResponse(BaseModel):
    stats: DashboardStats
    recent_activity: List[ActivityRecord]

class IssuerDashboardStats(BaseModel):
    total: int
    verified: int
    pending: int

class IssuerDashboardResponse(BaseModel):
    stats: IssuerDashboardStats
    recent_certificates: List[CertificateResponse]

class VerifierDashboardStats(BaseModel):
    total: int
    valid: int
    invalid: int
    total_fees: float

class VerifierDashboardResponse(BaseModel):
    stats: VerifierDashboardStats
    recent_verifications: List[VerificationResponse]

# Payments & audit
class PaymentRecord(BaseModel):
    id: int
    method: str
    digits: str
    reference: Optional[str] = None
    amount: float
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None

class AuditEventRecord(BaseModel):
    id: int
    event_type: str
    actor_user_id: Optional[int] = None
    actor_role: Optional[str] = None
    certificate_hash: Optional[str] = None
    verification_request_id: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

class BulkUploadFileResult(BaseModel):
    filename: str
    success: bool
    certificate_id: Optional[int] = None
    certificate_hash: Optional[str] = None
    transaction_id: Optional[str] = None
    extracted: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BulkUploadResponse(BaseModel):
    count: int
    success_count: int
    failure_count: int
    results: List[BulkUploadFileResult]

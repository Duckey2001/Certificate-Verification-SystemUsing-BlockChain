#!/usr/bin/env python3
"""
Enhanced Authentication API with full OAuth support
Supports Google OAuth, profile pictures, preferences, and audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session as DbSession  # Rename SQLAlchemy session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os
import uuid
import traceback
from dotenv import load_dotenv

from database import get_db

# Import models with explicit aliases to avoid confusion
from models import User as UserModel
from models import Session as SessionModel  # This is your custom Session model
from models import ProfilePicture, UserPreference, AuditLog, LoginActivity, Institution

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["enhanced-auth"])

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "certivert-dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Enhanced Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "issuer"
    institution_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    profile_visibility: Optional[str] = None
    language_preference: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class GoogleAuthRequest(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict
    preferences: Optional[dict] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    role: str
    institution: Optional[dict]
    is_active: bool
    last_login_at: Optional[datetime]
    profile_completion_score: int
    profile_visibility: str
    oauth_provider: str
    has_profile_picture: bool

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_audit_log(db: DbSession, user_id: Optional[int], action: str, 
                    resource_type: str, resource_id: Optional[str] = None,
                    old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                    ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                    session_id: Optional[str] = None, status: str = "success",
                    error_message: Optional[str] = None):
    """Create an audit log entry"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            status=status,
            error_message=error_message,
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Failed to create audit log: {e}")

def calculate_profile_completion(user: UserModel) -> int:
    """Calculate profile completion score (0-100)"""
    score = 0
    max_score = 100
    
    # Basic info (30 points)
    if user.first_name:
        score += 10
    if user.last_name:
        score += 10
    if user.phone_number:
        score += 10
    
    # Profile details (20 points)
    if user.bio:
        score += 10
    if user.department:
        score += 10
    
    # Institution (20 points)
    if user.institution_code:
        score += 20
    
    # Profile picture (15 points)
    if user.profile_image_url or user.profile_image:
        score += 15
    
    # Preferences (15 points)
    if user.language_preference != 'en':
        score += 5
    if user.timezone != 'UTC':
        score += 5
    if user.profile_visibility != 'public':
        score += 5
    
    return min(score, max_score)

async def get_current_user_enhanced(token: str = Depends(oauth2_scheme), db: DbSession = Depends(get_db)):
    """Enhanced current user dependency with audit logging"""
    # Rollback any existing failed transaction
    try:
        db.rollback()
    except:
        pass
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    # Check if session exists and is active - use SessionModel here
    session = db.query(SessionModel).filter(
        and_(
            SessionModel.session_token == token,
            SessionModel.expires > datetime.utcnow(),
            SessionModel.is_active == True
        )
    ).first()
    
    if not session:
        raise credentials_exception
    
    # Update last activity
    session.last_activity_at = datetime.utcnow()
    db.commit()
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# Enhanced Routes
@router.post("/register", response_model=TokenResponse)
async def register_enhanced(
    request: Request,
    user_data: UserCreate,
    db: DbSession = Depends(get_db)
):
    """Enhanced user registration with full profile support"""
    try:
        # Check if user exists
        existing_user = db.query(UserModel).filter(
            or_(
                UserModel.username == user_data.username,
                UserModel.email == user_data.email
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this username or email already exists"
            )
        
        # Check institution if provided
        institution = None
        if user_data.institution_code:
            institution = db.query(Institution).filter(
                Institution.code == user_data.institution_code
            ).first()
            if not institution:
                raise HTTPException(
                    status_code=400,
                    detail="Institution not found"
                )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = UserModel(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,
            institution_code=user_data.institution_code,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number,
            is_active=True,
            oauth_provider='password',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Calculate profile completion
        user.profile_completion_score = calculate_profile_completion(user)
        db.commit()
        
        # Create user preferences
        preferences = UserPreference(
            user_id=user.id,
            notification_settings={
                "email": True,
                "sms": False,
                "push": True,
                "login_alerts": True,
                "certificate_updates": True,
                "payment_notifications": True
            },
            privacy_settings={
                "profile_visibility": "public",
                "show_email": False,
                "show_phone": False,
                "allow_contact": True
            },
            dashboard_layout={
                "theme": "light",
                "widgets": ["certificates", "verification_requests", "statistics"]
            },
            accessibility_settings={
                "font_size": "medium",
                "high_contrast": False,
                "screen_reader": False
            }
        )
        db.add(preferences)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role}
        )
        
        # Create session - use SessionModel here
        session = SessionModel(
            id=str(uuid.uuid4()),
            session_token=access_token,
            user_id=str(user.id),
            expires=datetime.utcnow() + timedelta(days=7),
            is_active=True,
            device_info={"user_agent": request.headers.get("user-agent")},
            ip_address=request.client.host,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        
        # Log successful registration
        create_audit_log(
            db, user.id, "user_register", "user",
            new_values={
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            session_id=session.id
        )
        
        # Log login activity - REMOVED institution_code
        login_activity = LoginActivity(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            status="success",
            login_method="password",
            created_at=datetime.utcnow()
        )
        db.add(login_activity)
        
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution": {
                    "code": institution.code,
                    "name": institution.name,
                    "role": institution.role
                } if institution else None,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at,
                "profile_completion_score": user.profile_completion_score,
                "profile_visibility": user.profile_visibility,
                "oauth_provider": user.oauth_provider,
                "has_profile_picture": bool(user.profile_image_url or user.profile_image)
            },
            "preferences": {
                "notification_settings": preferences.notification_settings,
                "privacy_settings": preferences.privacy_settings,
                "dashboard_layout": preferences.dashboard_layout
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.post("/login", response_model=TokenResponse)
async def login_enhanced(
    request: Request,
    login_data: UserLogin,
    db: DbSession = Depends(get_db)
):
    """Enhanced login with device tracking and audit logging"""
    try:
        # Rollback any existing failed transaction
        try:
            db.rollback()
        except:
            pass
            
        print(f"🔍 Enhanced login attempt for: {login_data.username}")
        
        # Try to find user by username or email
        user = db.query(UserModel).filter(
            or_(
                UserModel.username == login_data.username,
                UserModel.email == login_data.username
            )
        ).first()
        
        if not user:
            # Log failed attempt
            create_audit_log(
                db, None, "login_failed", "user",
                new_values={"username": login_data.username},
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                status="failed",
                error_message="User not found"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is locked
        if hasattr(user, 'account_locked_until') and user.account_locked_until and user.account_locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=423, 
                detail="Account is temporarily locked. Please try again later."
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Verify password
        if user.oauth_provider == 'password':
            if not verify_password(login_data.password, user.password_hash):
                # Increment failed attempts if the field exists
                if hasattr(user, 'failed_login_attempts'):
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5 and hasattr(user, 'account_locked_until'):
                        user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
                    
                    db.commit()
                
                create_audit_log(
                    db, user.id, "login_failed", "user",
                    new_values={"failed_attempts": getattr(user, 'failed_login_attempts', 0)},
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                    status="failed",
                    error_message="Invalid password"
                )
                raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Reset failed attempts if the field exists
        if hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
        if hasattr(user, 'account_locked_until'):
            user.account_locked_until = None
        
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # Get institution details
        institution = None
        if user.institution_code:
            institution = db.query(Institution).filter(
                Institution.code == user.institution_code
            ).first()
        
        # Create access token
        expires_delta = timedelta(days=30) if login_data.remember_me else timedelta(days=7)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=expires_delta
        )
        
        # Create session with device tracking - use SessionModel here
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            session_token=access_token,
            user_id=str(user.id),
            expires=datetime.utcnow() + expires_delta,
            is_active=True,
            device_info={
                "user_agent": request.headers.get("user-agent"),
                "remember_me": login_data.remember_me
            },
            ip_address=request.client.host,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        
        # Log successful login
        create_audit_log(
            db, user.id, "login_success", "user",
            new_values={
                "login_method": user.oauth_provider,
                "remember_me": login_data.remember_me
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            session_id=session_id
        )
        
        # Log login activity - REMOVED institution_code
        login_activity = LoginActivity(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            status="success",
            login_method=user.oauth_provider,
            created_at=datetime.utcnow()
        )
        db.add(login_activity)
        
        db.commit()
        
        # Get user preferences
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == user.id
        ).first()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(expires_delta.total_seconds()),
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution": {
                    "code": institution.code if institution else None,
                    "name": institution.name if institution else None,
                    "role": institution.role if institution else None
                } if institution else None,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at,
                "profile_completion_score": user.profile_completion_score,
                "profile_visibility": user.profile_visibility,
                "oauth_provider": user.oauth_provider,
                "has_profile_picture": bool(user.profile_image_url or user.profile_image)
            },
            "preferences": {
                "notification_settings": preferences.notification_settings if preferences else {},
                "privacy_settings": preferences.privacy_settings if preferences else {},
                "dashboard_layout": preferences.dashboard_layout if preferences else {}
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Enhanced login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to login")

@router.post("/google-auth", response_model=TokenResponse)
async def google_auth(
    request: Request,
    auth_data: GoogleAuthRequest,
    db: DbSession = Depends(get_db)
):
    """Google OAuth authentication"""
    try:
        # TODO: Verify Google token with Google API
        # For now, we'll simulate the OAuth flow
        
        # Extract user info from Google token (simplified)
        # In production, you'd verify the token with Google's API
        google_user_info = {
            "id": "google_user_id_placeholder",
            "email": "user@gmail.com",
            "name": "Google User",
            "picture": "https://example.com/photo.jpg"
        }
        
        # Find or create user
        user = db.query(UserModel).filter(
            or_(
                UserModel.google_id == google_user_info["id"],
                UserModel.email == google_user_info["email"]
            )
        ).first()
        
        if not user:
            # Create new user from Google data
            user = UserModel(
                username=f"google_{google_user_info['id'][:20]}",
                email=google_user_info["email"],
                google_id=google_user_info["id"],
                role="issuer",
                first_name=google_user_info["name"].split()[0],
                last_name=" ".join(google_user_info["name"].split()[1:]),
                profile_image_url=google_user_info.get("picture"),
                is_active=True,
                is_verified=True,  # Google users are pre-verified
                email_verified_at=datetime.utcnow(),
                oauth_provider='google',
                google_access_token=auth_data.access_token,
                google_refresh_token=auth_data.refresh_token,
                google_token_expires_at=datetime.utcnow() + timedelta(hours=1),
                google_profile_data=google_user_info,
                last_oauth_login_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user
            user.google_access_token = auth_data.access_token
            user.google_refresh_token = auth_data.refresh_token
            user.google_token_expires_at = datetime.utcnow() + timedelta(hours=1)
            user.last_oauth_login_at = datetime.utcnow()
            user.last_login_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role}
        )
        
        # Create session - use SessionModel here
        session = SessionModel(
            id=str(uuid.uuid4()),
            session_token=access_token,
            user_id=str(user.id),
            expires=datetime.utcnow() + timedelta(days=7),
            is_active=True,
            device_info={"user_agent": request.headers.get("user-agent")},
            ip_address=request.client.host,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        
        # Log OAuth login
        create_audit_log(
            db, user.id, "login_oauth_google", "user",
            new_values={"oauth_provider": "google"},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            session_id=session.id
        )
        
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at,
                "profile_completion_score": user.profile_completion_score,
                "profile_visibility": user.profile_visibility,
                "oauth_provider": user.oauth_provider,
                "has_profile_picture": bool(user.profile_image_url or user.profile_image)
            }
        }
        
    except Exception as e:
        print(f"Google auth error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to authenticate with Google")

@router.post("/upload-profile-picture")
async def upload_profile_picture(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user_enhanced),
    db: DbSession = Depends(get_db)
):
    """Upload and update profile picture"""
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/profile_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Deactivate old profile pictures
        db.query(ProfilePicture).filter(
            ProfilePicture.user_id == current_user.id
        ).update({"is_active": False})
        
        # Create new profile picture record
        profile_picture = ProfilePicture(
            user_id=current_user.id,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            is_active=True,
            uploaded_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(profile_picture)
        
        # Update user profile
        current_user.profile_image_url = f"/uploads/profile_pictures/{unique_filename}"
        current_user.updated_at = datetime.utcnow()
        
        # Recalculate profile completion
        current_user.profile_completion_score = calculate_profile_completion(current_user)
        
        # Log profile picture upload
        create_audit_log(
            db, current_user.id, "profile_picture_upload", "user",
            new_values={"file_name": file.filename, "file_path": file_path},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        db.commit()
        
        return {
            "message": "Profile picture uploaded successfully",
            "file_url": current_user.profile_image_url,
            "profile_completion_score": current_user.profile_completion_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile picture upload error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: Request,
    profile_data: UserUpdate,
    current_user: UserModel = Depends(get_current_user_enhanced),
    db: DbSession = Depends(get_db)
):
    """Update user profile with audit logging"""
    try:
        # Store old values for audit
        old_values = {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number,
            "bio": current_user.bio,
            "department": current_user.department,
            "profile_visibility": current_user.profile_visibility,
            "language_preference": current_user.language_preference,
            "timezone": current_user.timezone,
            "email_notifications": current_user.email_notifications,
            "sms_notifications": current_user.sms_notifications,
            "push_notifications": current_user.push_notifications
        }
        
        # Update user profile
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        
        # Recalculate profile completion
        current_user.profile_completion_score = calculate_profile_completion(current_user)
        
        # Store new values for audit
        new_values = {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number,
            "bio": current_user.bio,
            "department": current_user.department,
            "profile_visibility": current_user.profile_visibility,
            "language_preference": current_user.language_preference,
            "timezone": current_user.timezone,
            "email_notifications": current_user.email_notifications,
            "sms_notifications": current_user.sms_notifications,
            "push_notifications": current_user.push_notifications
        }
        
        # Log profile update
        create_audit_log(
            db, current_user.id, "profile_update", "user",
            old_values=old_values,
            new_values=new_values,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        db.commit()
        
        # Get institution details
        institution = None
        if current_user.institution_code:
            institution = db.query(Institution).filter(
                Institution.code == current_user.institution_code
            ).first()
        
        return {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "institution": {
                "code": institution.code if institution else None,
                "name": institution.name if institution else None,
                "role": institution.role if institution else None
            } if institution else None,
            "is_active": current_user.is_active,
            "last_login_at": current_user.last_login_at,
            "profile_completion_score": current_user.profile_completion_score,
            "profile_visibility": current_user.profile_visibility,
            "oauth_provider": current_user.oauth_provider,
            "has_profile_picture": bool(current_user.profile_image_url or current_user.profile_image)
        }
        
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user_enhanced),
    db: DbSession = Depends(get_db)
):
    """Get current user profile with all details"""
    try:
        # Get institution details
        institution = None
        if current_user.institution_code:
            institution = db.query(Institution).filter(
                Institution.code == current_user.institution_code
            ).first()
        
        return {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "institution": {
                "code": institution.code if institution else None,
                "name": institution.name if institution else None,
                "role": institution.role if institution else None
            } if institution else None,
            "is_active": current_user.is_active,
            "last_login_at": current_user.last_login_at,
            "profile_completion_score": current_user.profile_completion_score,
            "profile_visibility": current_user.profile_visibility,
            "oauth_provider": current_user.oauth_provider,
            "has_profile_picture": bool(current_user.profile_image_url or current_user.profile_image)
        }
        
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@router.post("/logout")
async def logout_enhanced(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: UserModel = Depends(get_current_user_enhanced),
    db: DbSession = Depends(get_db)
):
    """Enhanced logout with audit logging"""
    try:
        # Find and deactivate session - use SessionModel here
        session = db.query(SessionModel).filter(
            SessionModel.session_token == token
        ).first()
        
        if session:
            session.is_active = False
            session.logout_reason = "user_logout"
            session.force_logout_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
        
        # Log logout
        create_audit_log(
            db, current_user.id, "logout", "user",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            session_id=session.id if session else None
        )
        
        db.commit()
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to logout")
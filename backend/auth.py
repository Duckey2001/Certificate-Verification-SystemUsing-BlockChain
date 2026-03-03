from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid

# Use jose for JWT operations (since python-jose is installed)
from jose import jwt, JWTError

from database import get_db
from models import User, Session as DbSession
from auth_service import (
    AuthService, 
    create_user_tokens, 
    get_current_user,
    get_current_active_user
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Pydantic models for request/response
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    institution_code: Optional[str] = None
    role: str = "user"

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    role: str
    institution_code: Optional[str]
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token: str  # Added for frontend compatibility
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class MessageResponse(BaseModel):
    message: str

# Auth endpoints
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - expects form data with username and password.
    This matches the OAuth2 password flow expected by the frontend.
    """
    try:
        # Find user by username or email
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user:
            user = db.query(User).filter(User.email == form_data.username).first()
        
        # Check if user exists and password is correct
        if not user or not AuthService.verify_password(form_data.password, user.password_hash):
            # Log failed attempt
            await AuthService.log_login_activity(
                db=db,
                user_id="unknown",
                request=request,
                status="failed",
                failure_reason="Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            await AuthService.log_login_activity(
                db=db,
                user_id=user.id,
                request=request,
                status="failed",
                failure_reason="Account deactivated"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        # Create tokens
        tokens = create_user_tokens(user)
        
        # Create session in database
        expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        AuthService.create_user_session(
            db=db,
            user_id=user.id,
            session_token=tokens["access_token"],
            expires=expires
        )
        
        # Log successful login
        await AuthService.log_login_activity(
            db=db,
            user_id=user.id,
            request=request,
            status="success"
        )
        
        db.commit()
        
        # Return token with user info (frontend expects "token" field)
        return {
            "access_token": tokens["access_token"],
            "token": tokens["access_token"],  # Added for frontend compatibility
            "refresh_token": tokens.get("refresh_token"),
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code,
                "institution": user.institution_code  # For frontend compatibility
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to login")

@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    try:
        # Check if username exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=400, 
                detail="Username already exists"
            )
        
        # Check if email exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=400, 
                detail="Email already exists"
            )
        
        # Create new user
        hashed_password = AuthService.get_password_hash(user_data.password)
        user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            institution_code=user_data.institution_code,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create tokens
        tokens = create_user_tokens(user)
        
        # Create session
        expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        AuthService.create_user_session(
            db=db,
            user_id=user.id,
            session_token=tokens["access_token"],
            expires=expires
        )
        
        # Log registration as login activity
        await AuthService.log_login_activity(
            db=db,
            user_id=user.id,
            request=request,
            status="success",
            login_method="registration"
        )
        
        db.commit()
        
        # Return token with user info
        return {
            "access_token": tokens["access_token"],
            "token": tokens["access_token"],  # Added for frontend compatibility
            "refresh_token": tokens.get("refresh_token"),
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code,
                "institution": user.institution_code  # For frontend compatibility
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register")

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Logout user by invalidating session"""
    try:
        # Delete session
        db.query(DbSession).filter(DbSession.session_token == token).delete()
        db.commit()
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        print(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to logout")

@router.get("/verify")
async def verify_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Verify if token is valid and return user info"""
    try:
        user = await get_current_active_user(token, db)
        
        return {
            "valid": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code,
                "institution": user.institution_code
            }
        }
    except HTTPException:
        return {"valid": False, "user": None}
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return {"valid": False, "user": None}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user info"""
    return current_user

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        from auth_service import refresh_access_token
        tokens = await refresh_access_token(refresh_request.refresh_token, db)
        
        # Get user from token
        user = await get_current_user(tokens["access_token"], db)
        
        return {
            "access_token": tokens["access_token"],
            "token": tokens["access_token"],  # Added for frontend compatibility
            "refresh_token": tokens.get("refresh_token"),
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code,
                "institution": user.institution_code
            }
        }
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify old password
        if not AuthService.verify_password(old_password, current_user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.password_hash = AuthService.get_password_hash(new_password)
        current_user.updated_at = datetime.utcnow()
        
        # Invalidate all other sessions
        AuthService.invalidate_user_sessions(db, current_user.id)
        
        db.commit()
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Password change error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")

# OAuth2 token endpoint (for compatibility)
@router.post("/token")
async def token_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token endpoint"""
    return await login(request, form_data, db)
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv

from database import get_db
from models import User, Session as DbSession, LoginActivity, Institution

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "certivert-dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    institution_code: Optional[str] = None
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    role: str
    institution: Optional[dict]
    is_active: bool
    last_login_at: Optional[datetime]

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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Check if session exists
    session = db.query(DbSession).filter(
        DbSession.session_token == token,
        DbSession.expires > datetime.utcnow()
    ).first()
    
    if not session:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# Routes
@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
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
        user = User(
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
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )
        
        # Create session
        session = DbSession(
            session_token=access_token,
            user_id=user.id,
            expires=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        
        # Log login activity
        login_activity = LoginActivity(
            user_id=user.id,
            institution_code=user.institution_code,
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
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution": {
                    "code": institution.code,
                    "name": institution.name,
                    "role": institution.role
                } if institution else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user"""
    try:
        # Find user
        user = db.query(User).filter(User.username == login_data.username).first()
        
        if not user:
            # Log failed attempt
            login_activity = LoginActivity(
                user_id="unknown",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                status="failed",
                failure_reason="User not found",
                login_method="password",
                created_at=datetime.utcnow()
            )
            db.add(login_activity)
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            login_activity = LoginActivity(
                user_id=user.id,
                institution_code=user.institution_code,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                status="failed",
                failure_reason="Account deactivated",
                login_method="password",
                created_at=datetime.utcnow()
            )
            db.add(login_activity)
            db.commit()
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            login_activity = LoginActivity(
                user_id=user.id,
                institution_code=user.institution_code,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                status="failed",
                failure_reason="Invalid password",
                login_method="password",
                created_at=datetime.utcnow()
            )
            db.add(login_activity)
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )
        
        # Create session
        session = DbSession(
            session_token=access_token,
            user_id=user.id,
            expires=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        
        # Log successful login
        login_activity = LoginActivity(
            user_id=user.id,
            institution_code=user.institution_code,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            status="success",
            login_method="password",
            created_at=datetime.utcnow()
        )
        db.add(login_activity)
        
        db.commit()
        
        # Get institution if any
        institution = None
        if user.institution_code:
            institution = db.query(Institution).filter(
                Institution.code == user.institution_code
            ).first()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution": {
                    "code": institution.code,
                    "name": institution.name,
                    "role": institution.role
                } if institution else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to login")

@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Logout user"""
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify token and return user info"""
    institution = None
    if current_user.institution_code:
        institution = db.query(Institution).filter(
            Institution.code == current_user.institution_code
        ).first()
    
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "institution": {
                "code": institution.code,
                "name": institution.name,
                "role": institution.role
            } if institution else None
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    institution = None
    if current_user.institution_code:
        institution = db.query(Institution).filter(
            Institution.code == current_user.institution_code
        ).first()
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "institution": {
            "code": institution.code,
            "name": institution.name,
            "role": institution.role
        } if institution else None,
        "is_active": current_user.is_active,
        "last_login_at": current_user.last_login_at
    }

@router.post("/token")
async def token_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login"""
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
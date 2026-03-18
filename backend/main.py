from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os

from database import get_db
from models import User
from auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "certificates"), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "verifications"), exist_ok=True)
    
    # Initialize blockchain connection
    from utils.enhanced_blockchain import initialize_blockchain
    blockchain_initialized = await initialize_blockchain()
    if blockchain_initialized:
        print("✅ Blockchain initialized successfully")
    else:
        print("⚠️ Blockchain initialization failed - using simulation mode")
    
    yield
    # Shutdown

app = FastAPI(
    title="CertiVert LGCSE Certificate Verification System",
    description="Blockchain-based certificate verification system for LGCSE certificates",
    version="1.0.0",
    lifespan=lifespan
)

import json
import uuid
from pathlib import Path

# Import local modules
from models import Base, Certificate, VerificationRequest, Invitation, Badge
from schemas import (
    UserCreate, UserResponse, Token, CertificateResponse
)

# Import routers
from api.auth import router as auth_router
from api.enhanced_auth import router as enhanced_auth_router
from api.certificates import router as certificates_router
from api.enhanced_certificates import router as enhanced_certificate_router
from api.google_auth import router as google_auth_router
from api.events import router as events_router
from api.payments import router as payments_router
from api.mpesa import router as mpesa_router
from api.mpesa_integration import router as mpesa_integration_router
from api.mpesa_routes import router as mpesa_routes_router
from api.mpesa_b2b_routes import router as mpesa_b2b_router
from api.dashboard import router as dashboard_router
from api.institutions import router as institutions_router
from api.admin_approval import router as admin_approval_router
from api.ocr import router as ocr_router
from api.websocket import router as websocket_router
from api.activities import router as activities_router
from api.notifications import router as notifications_router

# Import verifier and issuer routers
from api.verifier import router as verifier_router
from api.issuer import router as issuer_router

# Import auth refresh router
from api.auth_refresh import router as auth_refresh_router

# Import admin router
from api.admin import router as admin_router

# Security
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "certivert-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
UPLOAD_DIR = "uploads"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# Database - Import from database module
from database import get_db, SessionLocal, engine


def infer_institution_from_email(email: str) -> Optional[str]:
    """
    Infer institution name/code from email local-part.
    Example: 'letsapobokang.limko@gmail.com' -> 'LIMKO'.
    Only emails containing a dot in the local-part will be used.
    """
    try:
        local_part = email.split("@", 1)[0]
        parts = local_part.split(".")
        if len(parts) >= 2:
            institution_code = parts[-1].upper()
            # Map common institution codes to full names
            institution_mapping = {
                'LIMKO': 'Limkokwing University',
                'NUL': 'National University of Lesotho',
                'BOTHO': 'Botho University',
                'LGCSE': 'LGCSE Examination Council',
                'ECOL': 'Ecol University'
            }
            return institution_mapping.get(institution_code, institution_code)
    except Exception:
        return None
    return None

def is_admin_email(email: str) -> bool:
    """Check if email belongs to admin"""
    return email.lower() == 'letsapobokang.certivert@gmail.com'

def get_institution_role_from_email(email: str) -> str:
    """Determine user role based on email domain and institution"""
    if is_admin_email(email):
        return 'admin'
    
    institution = infer_institution_from_email(email)
    if institution:
        # Default role for institution users is 'issuer' until approved by admin
        return 'pending_issuer'
    
    return None

# Create tables
Base.metadata.create_all(bind=engine)

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS - use specific origins for credentials
_cors_origins = [
    "http://localhost:3000", 
    "http://localhost:3001", 
    "http://localhost:3002", 
    "http://localhost:3003", 
    "http://localhost:3000/static", 
    "http://127.0.0.1:3000", 
    "http://127.0.0.1:33957", 
    "http://127.0.0.1:39417",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8000",
    "http://10.24.42.33:3000",
    "http://10.24.42.33:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type"],
)

# Include routers
app.include_router(enhanced_auth_router)  # Already has prefix /api/auth
app.include_router(auth_router)  # Already has prefix /api/auth
app.include_router(certificates_router, prefix="/api")  # Add /api prefix to match frontend
app.include_router(enhanced_certificate_router, prefix="/api")  # Has prefix /api/certificates
app.include_router(google_auth_router)  # Already has prefix /api/auth
app.include_router(events_router)  # Already has prefix /api/events
app.include_router(payments_router)  # Already has prefix /api/payments
app.include_router(mpesa_router)  # Already has prefix /api/mpesa
app.include_router(mpesa_integration_router)  # Already has prefix /api/mpesa
app.include_router(mpesa_routes_router)  # Already has prefix /api/mpesa
app.include_router(mpesa_b2b_router)  # Already has prefix /api/mpesa
app.include_router(dashboard_router)  # Already has prefix /api/dashboard
app.include_router(institutions_router)  # Already has prefix /api/institutions
app.include_router(admin_approval_router)  # Already has prefix /api/admin
app.include_router(ocr_router)  # Already has prefix /api/ocr
app.include_router(websocket_router)  # Already has prefix /api/ws
app.include_router(activities_router)  # Already has prefix /api/activities
app.include_router(notifications_router)  # Already has prefix /api/notifications

# Add verifier and issuer routers
app.include_router(verifier_router)  # Already has prefix /api/verifier
app.include_router(issuer_router)  # Already has prefix /api/issuer

# Add auth refresh router
app.include_router(auth_refresh_router)  # Has prefix /auth

# Add admin router
app.include_router(admin_router)  # Already has prefix /api/admin

# Auth router endpoints (matching frontend expectations)
@app.get("/api/auth/me")
async def get_current_user_info(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user information"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "institution": user.institution
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/auth/login")
def api_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint for all users."""
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user:
            user = db.query(User).filter(User.email == form_data.username).first()
        
        # Allow any user with password to login
        if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/register", response_model=UserResponse)
def api_register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register endpoint matching frontend API expectations"""
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Infer institution from email if not explicitly provided
    inferred_institution = user_data.institution or infer_institution_from_email(user_data.email)

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role.value,
        institution=inferred_institution,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        institution=user.institution,
        created_at=user.created_at
    )

# Auth functions
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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Simple auth endpoints for testing
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

@app.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Infer institution from email if not explicitly provided
    inferred_institution = user_data.institution or infer_institution_from_email(user_data.email)

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role.value,
        institution=inferred_institution,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        institution=user.institution,
        created_at=user.created_at
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to CertiVert API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
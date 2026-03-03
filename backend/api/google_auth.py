from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import secrets
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import requests
from jose import jwt as jose_jwt

from database import get_db
from models import User, LoginActivity, Institution
from auth import AuthService, create_user_tokens
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/auth/google", tags=["google-auth"])

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
GOOGLE_FRONTEND_REDIRECT = os.getenv("GOOGLE_FRONTEND_REDIRECT", "http://localhost:3000/auth/callback")
SECRET_KEY = os.getenv("SECRET_KEY", "certivert-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Institution email domain mapping
INSTITUTION_DOMAINS = {
    'nul.ls': {'code': 'NUL', 'name': 'National University of Lesotho', 'role': 'verifier'},
    'limkokwing.ls': {'code': 'LIMKO', 'name': 'Limkokwing University', 'role': 'verifier'},
    'botho.ls': {'code': 'BOTHO', 'name': 'Botho University', 'role': 'verifier'},
    'ecol.ls': {'code': 'ECOL', 'name': 'Examination Council of Lesotho', 'role': 'issuer'},
    'lec.ls': {'code': 'LEC', 'name': 'Lesotho Education Council', 'role': 'issuer'},
    'gov.ls': {'code': 'GOV', 'name': 'Government of Lesotho', 'role': 'verifier'},
}

# Admin emails (hardcoded for security)
ADMIN_EMAILS = [
    'letsapobokang.certivert@gmail.com',
    'admin@certivert.com',
    'superadmin@certivert.com'
]

class TokenResponse(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

def is_admin_email(email: str) -> bool:
    """Check if email belongs to admin"""
    return email.lower() in [admin.lower() for admin in ADMIN_EMAILS]

def get_institution_from_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Determine institution from email domain
    Returns institution details or None if not recognized
    """
    try:
        domain = email.split('@')[-1].lower()
        
        # Check exact domain match
        if domain in INSTITUTION_DOMAINS:
            return INSTITUTION_DOMAINS[domain]
        
        # Check for subdomains
        for known_domain, details in INSTITUTION_DOMAINS.items():
            if domain.endswith('.' + known_domain) or known_domain.endswith('.' + domain):
                return details
        
        # Check for institutional email patterns
        local_part = email.split('@')[0].lower()
        for code in ['nul', 'limko', 'botho', 'ecol', 'lec']:
            if code in local_part or code in domain:
                # Map to appropriate institution
                code_map = {
                    'nul': ('NUL', 'National University of Lesotho', 'verifier'),
                    'limko': ('LIMKO', 'Limkokwing University', 'verifier'),
                    'botho': ('BOTHO', 'Botho University', 'verifier'),
                    'ecol': ('ECOL', 'Examination Council of Lesotho', 'issuer'),
                    'lec': ('LEC', 'Lesotho Education Council', 'issuer')
                }
                if code in code_map:
                    inst_code, inst_name, role = code_map[code]
                    return {'code': inst_code, 'name': inst_name, 'role': role}
        
    except Exception as e:
        print(f"Error parsing email domain: {e}")
    
    return None

def get_institution_role_from_email(email: str) -> str:
    """Determine user role based on email"""
    if is_admin_email(email):
        return 'admin'
    
    institution = get_institution_from_email(email)
    if institution:
        # Return the role specified for the institution, or default to pending
        return institution.get('role', 'pending')
    
    return 'pending'  # Default role for unrecognized emails

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_secure_state_token() -> str:
    """Generate a secure state token for OAuth flow"""
    return secrets.token_urlsafe(32)

def validate_state_token(token: str, stored_token: str) -> bool:
    """Validate state token to prevent CSRF"""
    return secrets.compare_digest(token, stored_token)

@router.get("/login")
async def google_login(request: Request):
    """Initiate Google OAuth login with state parameter for CSRF protection"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
        )
    
    # Generate state token for CSRF protection
    state = generate_secure_state_token()
    
    # Store state in session or cookie (implement based on your session management)
    # For now, we'll return it in the response and expect it back
    request.session['oauth_state'] = state
    
    # Google OAuth URL with all required parameters
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline&"
        f"prompt=consent&"
        f"state={state}"
    )
    
    return {
        "auth_url": google_auth_url,
        "state": state
    }

@router.get("/callback")
async def google_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback and redirect to frontend"""
    
    # Check for OAuth error
    if error:
        # Log the error
        print(f"Google OAuth error: {error}")
        redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error={error}"
        return RedirectResponse(url=redirect_url)
    
    # Validate state token (CSRF protection)
    stored_state = request.session.get('oauth_state')
    if not state or not stored_state or not validate_state_token(state, stored_state):
        redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error=invalid_state"
        return RedirectResponse(url=redirect_url)
    
    # Clear the used state
    request.session.pop('oauth_state', None)
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error=oauth_not_configured"
        return RedirectResponse(url=redirect_url)
    
    try:
        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        tokens = token_response.json()
        
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        
        if not id_token or not access_token:
            redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error=invalid_token_response"
            return RedirectResponse(url=redirect_url)
        
        # Verify and decode the ID token
        # In production, you should verify the token signature
        # For now, we'll just decode it
        import jwt
        try:
            # First try to verify with Google's public keys
            google_certs_url = "https://www.googleapis.com/oauth2/v1/certs"
            certs_response = requests.get(google_certs_url, timeout=10)
            certs = certs_response.json()
            
            # Get the key ID from the token header
            header = jwt.get_unverified_header(id_token)
            key_id = header.get('kid')
            
            if key_id and key_id in certs:
                public_key = certs[key_id]
                token_info = jwt.decode(
                    id_token, 
                    public_key, 
                    algorithms=['RS256'],
                    audience=GOOGLE_CLIENT_ID
                )
            else:
                # Fallback to unverified decode (not recommended for production)
                token_info = jwt.decode(id_token, options={"verify_signature": False})
        except Exception as e:
            print(f"Token verification error: {e}")
            # Fallback to userinfo endpoint
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_info_response = requests.get(user_info_url, headers=headers, timeout=10)
            user_info_response.raise_for_status()
            token_info = user_info_response.json()
        
        google_id = token_info.get("sub") or token_info.get("id")
        email = token_info.get("email")
        name = token_info.get("name", "")
        picture = token_info.get("picture")
        
        if not email:
            redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error=email_required"
            return RedirectResponse(url=redirect_url)
        
        # Process the user
        result = await process_google_user(db, google_id, email, name, picture, request)
        
        # Redirect to frontend with token
        redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?token={result['token']}&user={result['user']['username']}"
        return RedirectResponse(url=redirect_url)
        
    except requests.RequestException as e:
        print(f"Google OAuth request error: {e}")
        redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error=oauth_request_failed"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        print(f"Google OAuth callback error: {e}")
        redirect_url = f"{GOOGLE_FRONTEND_REDIRECT}?error=internal_error"
        return RedirectResponse(url=redirect_url)

async def process_google_user(
    db: Session,
    google_id: str,
    email: str,
    name: str,
    picture: Optional[str],
    request: Request
) -> Dict[str, Any]:
    """Process Google user data and create/update user"""
    
    # Check if email is from allowed institution
    institution_info = get_institution_from_email(email)
    
    # Determine role based on email
    role = get_institution_role_from_email(email)
    
    # Check if user exists by Google ID or email
    user = db.query(User).filter(
        (User.google_id == google_id) | (User.email == email)
    ).first()
    
    institution_code = None
    if institution_info:
        # Check if institution exists in database
        institution = db.query(Institution).filter(
            Institution.code == institution_info['code']
        ).first()
        
        if institution:
            institution_code = institution.code
        else:
            # Create new institution if it doesn't exist
            new_institution = Institution(
                id=str(uuid.uuid4()),
                code=institution_info['code'],
                name=institution_info['name'],
                role=institution_info['role'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_institution)
            db.commit()
            institution_code = new_institution.code
    
    if user:
        # Update existing user
        if not user.google_id:
            user.google_id = google_id
        
        if institution_code and not user.institution_code:
            user.institution_code = institution_code
        
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        db.commit()
    else:
        # Create new user
        # Generate username from email or name
        username_base = email.split("@")[0].lower()
        # Remove special characters
        username_base = ''.join(e for e in username_base if e.isalnum())
        
        if not username_base and name:
            username_base = name.lower().replace(" ", "").replace(".", "")
        
        username = username_base
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{username_base}{counter}"
            counter += 1
        
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=None,  # OAuth users don't have password
            google_id=google_id,
            institution_code=institution_code,
            role=role,
            is_active=True,
            last_login_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create JWT tokens
    tokens = create_user_tokens(user)
    
    # Log login activity
    await AuthService.log_login_activity(
        db=db,
        user_id=user.id,
        request=request,
        status="success",
        login_method="google"
    )
    
    return {
        "token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens["expires_in"],
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "institution_code": user.institution_code
        }
    }

@router.post("/callback", response_model=TokenResponse)
async def google_callback_api(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback for API clients (non-redirect flow)"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )
    
    try:
        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        tokens = token_response.json()
        
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        
        if not id_token or not access_token:
            raise HTTPException(status_code=400, detail="Invalid token response from Google")
        
        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers, timeout=10)
        user_info_response.raise_for_status()
        google_user = user_info_response.json()
        
        google_id = google_user.get("id")
        email = google_user.get("email")
        name = google_user.get("name", "")
        picture = google_user.get("picture")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Process the user
        result = await process_google_user(db, google_id, email, name, picture, request)
        
        return result
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

class VerifyTokenRequest(BaseModel):
    token: str

@router.post("/verify-token", response_model=TokenResponse)
async def verify_google_token(
    request: Request,
    payload: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """Verify Google ID token and create/login user"""
    token = payload.token
    
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )
    
    try:
        # Verify the token with Google
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        response = requests.get(verify_url, timeout=10)
        response.raise_for_status()
        token_info = response.json()
        
        # Verify audience
        if token_info.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid token audience")
        
        # Check if email is verified
        if not token_info.get("email_verified"):
            raise HTTPException(status_code=400, detail="Email not verified by Google")
        
        google_id = token_info.get("sub")
        email = token_info.get("email")
        name = token_info.get("name", "")
        picture = token_info.get("picture")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Process the user
        result = await process_google_user(db, google_id, email, name, picture, request)
        
        return result
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Google token verification error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@router.get("/institutions")
async def get_supported_institutions():
    """Get list of supported institutions for Google OAuth"""
    institutions = []
    for domain, details in INSTITUTION_DOMAINS.items():
        institutions.append({
            "domain": domain,
            "code": details['code'],
            "name": details['name'],
            "role": details['role']
        })
    
    return {
        "institutions": institutions,
        "admin_emails": ADMIN_EMAILS
    }
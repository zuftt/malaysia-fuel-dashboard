"""
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import os

from app.database import get_db
from app.models import User
from app.schemas import UserLogin, TokenResponse

router = APIRouter()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(user_id: int, role: str):
    """Create JWT access token"""
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    Returns JWT token
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # TODO: Verify password hash
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"])
    # if not pwd_context.verify(credentials.password, user.password_hash):
    
    token = create_access_token(user.id, user.role)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/register")
async def register(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Register new user (admin only in production)
    """
    # Check if user exists
    existing = db.query(User).filter(User.email == credentials.email).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    new_user = User(
        email=credentials.email,
        password_hash="hashed_password",  # TODO: Hash password
        role="viewer",
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "success": True,
        "user_id": new_user.id,
        "email": new_user.email,
        "role": new_user.role
    }


@router.get("/me")
async def get_current_user(token: str = None):
    """
    Get current user info (from JWT token)
    """
    # TODO: Implement token verification
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token"
        )
    
    return {
        "user_id": 1,
        "email": "user@example.com",
        "role": "admin"
    }

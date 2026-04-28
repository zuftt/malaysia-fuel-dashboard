"""
Authentication API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
import bcrypt
import jwt
import os

from app.database import get_db
from app.models import User
from app.schemas import UserLogin, TokenResponse

# Use the same Limiter instance the app state was wired with in main.py.
# slowapi keys by remote address; storage is in-memory per worker.
_limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Configuration — refuse to start without a strong SECRET_KEY.
_DEFAULT_SECRET = "dev-secret-key-change-in-production"
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY or SECRET_KEY == _DEFAULT_SECRET:
    raise RuntimeError(
        "SECRET_KEY env var is missing or set to the placeholder default. "
        "Generate one with `python -c 'import secrets; print(secrets.token_urlsafe(32))'` "
        "and set it on Render before starting the API."
    )
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters of high-entropy random data.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Bearer token scheme
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int, role: str):
    """Create JWT access token"""
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get the current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    payload = decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    return user


async def require_admin(user: User = Depends(get_current_user_dep)) -> User:
    """Dependency that requires the user to be an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Pre-computed bcrypt hash of a random throwaway password — used to flatten timing
# when the email is not found, so an attacker can't enumerate accounts via response time.
_DUMMY_HASH = bcrypt.hashpw(b"timing-attack-defence", bcrypt.gensalt()).decode("utf-8")


@router.post("/login", response_model=TokenResponse)
@_limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    Returns JWT token
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    # Always run bcrypt to keep timing constant regardless of whether email exists.
    password_hash = user.password_hash if user else _DUMMY_HASH
    password_ok = verify_password(credentials.password, password_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token(user.id, user.role)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/register")
async def register(
    credentials: UserLogin,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Register new user (admin only)
    """
    existing = db.query(User).filter(User.email == credentials.email).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    new_user = User(
        email=credentials.email,
        password_hash=hash_password(credentials.password),
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
async def get_current_user(user: User = Depends(get_current_user_dep)):
    """
    Get current user info (from JWT token)
    """
    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

# --- Password hashing setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a secure password hash (bcrypt max length = 72 bytes)."""
    # ✅ Добавляем защиту от ошибки "password cannot be longer than 72 bytes"
    password = password[:72]
    return pwd_context.hash(password)

# --- JWT token creation and verification ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def get_user_from_token(token: str) -> Optional[dict]:
    """Extract user information from JWT token."""
    payload = verify_token(token)
    if not payload:
        return None

    # JWT стандартно хранит user_id в "sub"
    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        return None

    return {"user_id": user_id, "role": role}

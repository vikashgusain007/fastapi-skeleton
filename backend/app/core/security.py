from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from core.config import settings

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """
    Generate bcrypt hash of the password.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    subject: str | Any, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: str | Any, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.REFRESH_SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    """
    Decode and validate a token.
    Raises jwt.PyJWTError for invalid/expired tokens.
    """
    secret = settings.REFRESH_SECRET_KEY if is_refresh else settings.SECRET_KEY
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    # Validate token type
    expected_type = "refresh" if is_refresh else "access"
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Token type mismatch")
    return payload

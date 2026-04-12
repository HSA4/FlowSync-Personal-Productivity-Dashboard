"""Security Utilities - JWT and Password Hashing"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import base64

from app.core.config import settings
from app.core.errors import AuthenticationError


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    # Check if it's a bcrypt hash (starts with $2a$ or $2b$)
    if hashed_password.startswith('$2a$') or hashed_password.startswith('$2b$'):
        # Standard bcrypt hash
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    else:
        # Try base64 decoded
        try:
            decoded = base64.b64decode(hashed_password).decode('utf-8')
            return bcrypt.checkpw(plain_password.encode('utf-8'), decoded.encode('utf-8'))
        except:
            return False


def get_password_hash(password: str) -> str:
    """Hash a password (truncates to 72 bytes for bcrypt limit)"""
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Return as string
    return hashed.decode('utf-8')


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise AuthenticationError("Invalid or expired token")


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Get the payload from a token without raising exceptions"""
    try:
        return decode_access_token(token)
    except AuthenticationError:
        return None


def create_refresh_token(user_id: int) -> str:
    """Create a refresh token (longer-lived)"""
    expires_delta = timedelta(days=30)
    return create_access_token(
        data={"sub": str(user_id), "type": "refresh"},
        expires_delta=expires_delta,
    )


def verify_token(token: str) -> Optional[int]:
    """Verify a token and return the user ID"""
    payload = get_token_payload(token)
    if payload:
        return int(payload.get("sub", 0))
    return None

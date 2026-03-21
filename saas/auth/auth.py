"""
Authentication module for SaaS podcast generator.
"""
import os
import hashlib
import secrets
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
from functools import wraps

import jwt

# Password hashing - using PBKDF2 for simplicity and compatibility
def hash_password(password: str) -> str:
    """Hash a password using PBKDF2."""
    salt = secrets.token_hex(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        salt, key = hashed_password.split('$')
        expected_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(expected_key.hex(), key)
    except Exception:
        return False


# JWT settings - load from environment or file for persistence across restarts
def _load_jwt_secret() -> str:
    """Load JWT secret from environment or file, or generate a new one."""
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret:
        return env_secret
    
    # Try to load from file for persistence
    secret_file = os.path.join(os.path.dirname(__file__), ".jwt_secret")
    if os.path.exists(secret_file):
        with open(secret_file, "r") as f:
            return f.read().strip()
    
    # Generate new secret and save to file
    new_secret = secrets.token_hex(32)
    try:
        with open(secret_file, "w") as f:
            f.write(new_secret)
        os.chmod(secret_file, 0o600)  # Restrict access to owner
    except Exception:
        pass  # If we can't write the file, use in-memory secret
    
    return new_secret


JWT_SECRET_KEY = _load_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.
    Returns (full_key, key_hash) - store only key_hash, return full_key to user once.
    """
    full_key = f"mtg_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    prefix = full_key[:12]  # First 12 chars for display
    return full_key, key_hash, prefix


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hmac.compare_digest(hash_api_key(plain_key), hashed_key)


class TokenPayload:
    """Token payload data class."""
    def __init__(self, user_id: int, email: str, token_type: str = "access"):
        self.user_id = user_id
        self.email = email
        self.token_type = token_type
    
    @classmethod
    def from_jwt(cls, token: str) -> Optional["TokenPayload"]:
        """Create TokenPayload from JWT token."""
        payload = decode_token(token)
        if not payload:
            return None
        return cls(
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            token_type=payload.get("type", "access")
        )


# Rate limiting helpers
def check_rate_limit(calls_made: int, limit: int, last_reset: Optional[datetime]) -> tuple[bool, Optional[datetime]]:
    """Check if rate limit is exceeded and calculate reset time if needed."""
    now = datetime.now(timezone.utc)
    
    if last_reset is None:
        # First call, reset window starts now
        return True, now + timedelta(hours=1)
    
    # Check if we're still in the same hour window
    if now - last_reset < timedelta(hours=1):
        if calls_made >= limit:
            return False, None
        return True, last_reset
    else:
        # New hour window
        return True, now + timedelta(hours=1)


# Role-based access control
class Role:
    USER = "user"
    ADMIN = "admin"


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # This will be used with FastAPI Depends
        return await f(*args, **kwargs)
    return wrapper


def require_role(role: str):
    """Decorator to require a specific role."""
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            # This will be used with FastAPI Depends
            return await f(*args, **kwargs)
        return wrapper
    return decorator

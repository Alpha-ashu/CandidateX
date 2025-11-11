"""
Authentication utilities for password hashing, JWT tokens, and security.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from app.config import settings
from app.models.user import TokenData, UserRole

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type_in_payload = payload.get("type")

        if token_type_in_payload != token_type:
            return None

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None or role is None:
            return None

        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            return None

        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp)
        else:
            exp_datetime = None

        return TokenData(user_id=user_id, email=email, role=user_role, exp=exp_datetime)

    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def create_password_reset_token(email: str) -> str:
    """Create password reset token."""
    expire = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    to_encode = {"email": email, "exp": expire, "type": "password_reset"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("type")

        if token_type != "password_reset":
            return None

        email: str = payload.get("email")
        return email if email else None

    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def create_email_verification_token(user_id: str, email: str) -> str:
    """Create email verification token."""
    expire = datetime.utcnow() + timedelta(hours=24)  # 24 hours
    to_encode = {"user_id": user_id, "email": email, "exp": expire, "type": "email_verification"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_email_verification_token(token: str) -> Optional[Dict[str, str]]:
    """Verify email verification token and return user data."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("type")

        if token_type != "email_verification":
            return None

        user_id: str = payload.get("user_id")
        email: str = payload.get("email")

        if user_id and email:
            return {"user_id": user_id, "email": email}
        return None

    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage."""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return requirements."""
    requirements = {
        "length": len(password) >= 8,
        "uppercase": any(c.isupper() for c in password),
        "lowercase": any(c.islower() for c in password),
        "digit": any(c.isdigit() for c in password),
        "special": any(not c.isalnum() for c in password)
    }

    requirements["valid"] = all(requirements.values())
    return requirements

"""
User model for MongoDB.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration."""
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    ADMIN = "admin"

class UserStatus(str, Enum):
    """User account status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class User(BaseModel):
    """User model."""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    email: EmailStr = Field(..., unique=True, index=True)
    full_name: str = Field(..., min_length=1, max_length=100)
    password_hash: str
    role: UserRole = Field(default=UserRole.CANDIDATE)
    status: UserStatus = Field(default=UserStatus.PENDING_VERIFICATION)

    # Profile information
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    # Account settings
    email_verified: bool = Field(default=False)
    two_factor_enabled: bool = Field(default=False)
    preferred_language: str = Field(default="en")
    timezone: str = Field(default="UTC")

    # Security
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None

    # Social login
    google_id: Optional[str] = None
    linkedin_id: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @classmethod
    def from_mongo(cls, data: dict) -> "User":
        """Create User instance from MongoDB document."""
        if "_id" in data and isinstance(data["_id"], ObjectId):
            data["_id"] = str(data["_id"])
        return cls(**data)

class UserInDB(User):
    """User model for database operations."""
    pass

class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    role: UserRole = Field(default=UserRole.CANDIDATE)
    phone: Optional[str] = None
    location: Optional[str] = None

class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None

class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr

class PasswordReset(BaseModel):
    """Password reset model."""
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePassword(BaseModel):
    """Change password model."""
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserProfile(BaseModel):
    """User profile response model."""
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus
    avatar_url: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    bio: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    email_verified: bool
    two_factor_enabled: bool
    preferred_language: str
    timezone: str
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class TokenData(BaseModel):
    """JWT token data model."""
    user_id: str
    email: str
    role: UserRole
    exp: Optional[datetime] = None

class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile

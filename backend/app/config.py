"""
Configuration settings for CandidateX backend.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Literal
import os
from pathlib import Path
from pydantic import field_validator

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Application settings
    APP_NAME: str = "CandidateX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: Literal['DEBUG', 'INFO', 'WARN', 'ERROR'] = 'INFO'
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_V1_STR: str = "/api/v1"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://candidatex.com",
    ]

    # Database settings
    MONGODB_URL: str = "mongodb://localhost:27017/candidatex"
    MONGODB_DATABASE: str = "candidatex"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # JWT settings
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@candidatex.com"
    EMAIL_FROM_NAME: str = "CandidateX"

    # AI Service settings
    GOOGLE_AI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gemini-pro"

    # Cloud Storage settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "candidatex-files"
    FIREBASE_CONFIG: Optional[dict] = None

    # Security settings
    BCRYPT_ROUNDS: int = 12
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30

    # File upload settings
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"]

    # Interview settings
    MAX_QUESTIONS_PER_INTERVIEW: int = 20
    DEFAULT_QUESTION_TIME_LIMIT: int = 300  # 5 minutes
    INTERVIEW_SESSION_TIMEOUT: int = 3600  # 1 hour

    # Anti-cheat settings
    ANTICHEAT_ENABLED: bool = True
    FACE_DETECTION_THRESHOLD: float = 0.8
    TAB_SWITCH_WARNINGS: int = 3
    FULLSCREEN_CHECK_INTERVAL: int = 5000  # 5 seconds

    # Analytics settings
    ANALYTICS_RETENTION_DAYS: int = 365
    DASHBOARD_CACHE_TTL: int = 300  # 5 minutes

    # Admin settings
    ADMIN_EMAIL: str = "admin@candidatex.com"
    SUPPORT_EMAIL: str = "support@candidatex.com"

    # External API settings
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Monitoring settings
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator('DEBUG', mode='before')
    @classmethod
    def coerce_debug(cls, v):
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ('1','true','yes','on'):  return True
            if s in ('0','false','no','off'): return False
            # If someone put a level into DEBUG, treat only DEBUG as True
            if s in ('debug','info','warn','warning','error'):
                return s == 'debug'
        return v

# Create global settings instance
settings = Settings()

# Validate critical settings
def validate_settings():
    """Validate critical application settings."""
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-in-production":
        raise ValueError("SECRET_KEY must be set in production")

    if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY == "your-jwt-secret-key-change-in-production":
        raise ValueError("JWT_SECRET_KEY must be set in production")

    # Validate AI service configuration
    if not settings.GOOGLE_AI_API_KEY and not settings.OPENAI_API_KEY:
        print("Warning: No AI API keys configured. AI features will be limited.")

    # Validate email configuration
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        print("Warning: Email service not configured. Email features will be disabled.")

# Run validation on import
validate_settings()

"""
Authentication routes for user registration, login, and password management.
"""
from datetime import datetime, timedelta
from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import (
    User, UserCreate, UserLogin, UserProfile, Token,
    PasswordResetRequest, PasswordReset, ChangePassword,
    UserStatus, UserRole
)
from app.models import get_database
from app.auth.utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, create_password_reset_token,
    verify_password_reset_token, create_email_verification_token,
    validate_password_strength
)
from app.auth.dependencies import get_current_user
from app.config import settings
from app.utils.database import db_manager

# Email service would be imported here
# from app.services.email import send_email

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new user account.
    """
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    password_validation = validate_password_strength(user_data.password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements"
        )

    # Create user
    user_dict = user_data.dict()
    user_dict["password_hash"] = get_password_hash(user_data.password)
    user_dict["status"] = UserStatus.ACTIVE  # Set to ACTIVE for immediate access in development
    user_dict["email_verified"] = True  # Skip email verification in development
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()

    # Remove password from dict
    del user_dict["password"]

    result = await db.users.insert_one(user_dict)
    user_id = result.inserted_id

    # Get created user
    from bson import ObjectId
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    user = User.from_mongo(user_doc)

    # Create default data for the new user
    try:
        await db_manager._create_user_default_data(str(user_id), user.role)
        logger.info(f"Created default data for user: {user.email}")
    except Exception as e:
        logger.warning(f"Failed to create default data for user {user.email}: {e}")
        # Don't fail registration if default data creation fails

    # Create email verification token
    verification_token = create_email_verification_token(str(user_id), user.email)

    # Send verification email (background task)
    # background_tasks.add_task(
    #     send_email,
    #     to_email=user.email,
    #     subject="Verify your CandidateX account",
    #     template="email_verification",
    #     context={"verification_token": verification_token}
    # )

    logger.info(f"User registered: {user.email} (ID: {user_id})")

    # Return UserProfile with explicit field mapping
    return UserProfile(
        id=str(user_id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        avatar_url=user.avatar_url,
        phone=user.phone,
        location=user.location,
        bio=user.bio,
        linkedin_url=user.linkedin_url,
        github_url=user.github_url,
        email_verified=user.email_verified,
        two_factor_enabled=user.two_factor_enabled,
        preferred_language=user.preferred_language,
        timezone=user.timezone,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Authenticate user and return JWT tokens.
    """
    # Find user by email
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user = User.from_mongo(user_doc)

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to failed login attempts"
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        # Increment failed attempts
        failed_attempts = user.failed_login_attempts + 1
        update_data = {"failed_login_attempts": failed_attempts}

        # Lock account if too many attempts
        if failed_attempts >= settings.ACCOUNT_LOCKOUT_ATTEMPTS:
            lock_until = datetime.utcnow() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_DURATION_MINUTES)
            update_data["locked_until"] = lock_until

        await db.users.update_one(
            {"_id": user.id},
            {"$set": update_data}
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check account status
    if user.status != UserStatus.ACTIVE:
        if user.status == UserStatus.PENDING_VERIFICATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address before logging in"
            )
        elif user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

    # Reset failed attempts and update last login
    await db.users.update_one(
        {"_id": user.id},
        {
            "$set": {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Create tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Calculate expiration time
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    logger.info(f"User logged in: {user.email} (ID: {user.id})")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            avatar_url=user.avatar_url,
            phone=user.phone,
            location=user.location,
            bio=user.bio,
            linkedin_url=user.linkedin_url,
            github_url=user.github_url,
            email_verified=user.email_verified,
            two_factor_enabled=user.two_factor_enabled,
            preferred_language=user.preferred_language,
            timezone=user.timezone,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )

@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Refresh access token using refresh token.
    """
    from app.auth.utils import verify_token

    token_data = verify_token(refresh_token, "refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    from bson import ObjectId
    user_doc = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    user = User.from_mongo(user_doc)
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active"
        )

    # Create new tokens
    new_token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value
    }

    access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            avatar_url=user.avatar_url,
            phone=user.phone,
            location=user.location,
            bio=user.bio,
            linkedin_url=user.linkedin_url,
            github_url=user.github_url,
            email_verified=user.email_verified,
            two_factor_enabled=user.two_factor_enabled,
            preferred_language=user.preferred_language,
            timezone=user.timezone,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )

@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Request password reset for user account.
    """
    user_doc = await db.users.find_one({"email": request.email})
    if not user_doc:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}

    user = User.from_mongo(user_doc)

    # Create password reset token
    reset_token = create_password_reset_token(user.email)

    # Store token in database
    await db.users.update_one(
        {"_id": user.id},
        {
            "$set": {
                "password_reset_token": reset_token,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Send reset email (background task)
    # background_tasks.add_task(
    #     send_email,
    #     to_email=user.email,
    #     subject="Reset your CandidateX password",
    #     template="password_reset",
    #     context={"reset_token": reset_token}
    # )

    logger.info(f"Password reset requested for: {user.email}")

    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Reset user password using reset token.
    """
    # Verify token
    email = verify_password_reset_token(reset_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Find user
    user_doc = await db.users.find_one({"email": email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    user = User.from_mongo(user_doc)

    # Validate new password
    password_validation = validate_password_strength(reset_data.new_password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements"
        )

    # Update password and clear reset token
    await db.users.update_one(
        {"_id": user.id},
        {
            "$set": {
                "password_hash": get_password_hash(reset_data.new_password),
                "password_reset_token": None,
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "password_reset_expires": 1
            }
        }
    )

    logger.info(f"Password reset completed for: {user.email}")

    return {"message": "Password has been reset successfully"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Change current user's password.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password
    password_validation = validate_password_strength(password_data.new_password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements"
        )

    # Update password
    await db.users.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "password_hash": get_password_hash(password_data.new_password),
                "updated_at": datetime.utcnow()
            }
        }
    )

    logger.info(f"Password changed for user: {current_user.email}")

    return {"message": "Password changed successfully"}

@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Verify user email address using verification token.
    """
    from app.auth.utils import verify_email_verification_token

    token_data = verify_email_verification_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    user_id = token_data["user_id"]
    email = token_data["email"]

    # Update user status
    from bson import ObjectId
    result = await db.users.update_one(
        {"_id": ObjectId(user_id), "email": email},
        {
            "$set": {
                "email_verified": True,
                "status": UserStatus.ACTIVE,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    logger.info(f"Email verified for user: {email}")

    return {"message": "Email verified successfully"}

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        status=current_user.status,
        avatar_url=current_user.avatar_url,
        phone=current_user.phone,
        location=current_user.location,
        bio=current_user.bio,
        linkedin_url=current_user.linkedin_url,
        github_url=current_user.github_url,
        email_verified=current_user.email_verified,
        two_factor_enabled=current_user.two_factor_enabled,
        preferred_language=current_user.preferred_language,
        timezone=current_user.timezone,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

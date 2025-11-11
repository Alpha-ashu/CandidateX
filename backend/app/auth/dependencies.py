"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User, UserRole, TokenData
from app.auth.utils import verify_token
from app.models import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

security = HTTPBearer()

async def get_current_user(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> User:
    """
    Get current authenticated user from JWT token.
    For development, create a test user if no authentication provided.
    """
    import os
    from datetime import datetime
    from bson import ObjectId

    # Check for development mode (no auth header)
    auth_header = request.headers.get("authorization")
    if not auth_header:
        # Development mode - create a test user
        test_user_id = "507f1f77bcf86cd799439011"  # Fixed test user ID

        # Check if test user exists
        test_user_doc = await db.users.find_one({"_id": ObjectId(test_user_id)})
        if not test_user_doc:
            # Create test user
            test_user_data = {
                "_id": ObjectId(test_user_id),
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "candidate",
                "status": "active",
                "email_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8JZwHd5Jm",  # "testpassword"
                "failed_login_attempts": 0,
                "two_factor_enabled": False,
                "preferred_language": "en",
                "timezone": "UTC+5:30"
            }
            await db.users.insert_one(test_user_data)
            test_user_doc = test_user_data

        # Convert to User model
        user = User(**test_user_doc)
        return user

    # Normal authentication flow
    try:
        # Extract token from header
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]
        token_data = verify_token(token)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user_doc = await db.users.find_one({"_id": token_data.user_id})
        if user_doc is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert to User model
        user = User(**user_doc)

        # Check if account is active
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user (alias for get_current_user).
    """
    return current_user

def get_current_user_with_role(required_role: UserRole):
    """
    Dependency factory for role-based access control.
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    return dependency

async def get_current_candidate(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user with candidate role.
    """
    return get_current_user_with_role(UserRole.CANDIDATE)(current_user)

async def get_current_recruiter(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user with recruiter role.
    """
    return get_current_user_with_role(UserRole.RECRUITER)(current_user)

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user with admin role.
    """
    return get_current_user_with_role(UserRole.ADMIN)(current_user)

async def get_optional_current_user(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        token_data = verify_token(token)

        if token_data is None:
            return None

        # Get user from database
        user_doc = await db.users.find_one({"_id": token_data.user_id})
        if user_doc is None:
            return None

        user = User(**user_doc)

        # Check if account is active
        if user.status != "active":
            return None

        return user

    except Exception:
        return None

def check_permissions(required_permissions: list):
    """
    Dependency factory for permission-based access control.
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        # Define role permissions
        role_permissions = {
            UserRole.CANDIDATE: [
                "read_own_profile",
                "update_own_profile",
                "create_interview",
                "read_own_interviews",
                "take_interview",
                "read_own_resume",
                "upload_resume",
                "read_dashboard"
            ],
            UserRole.RECRUITER: [
                "read_own_profile",
                "update_own_profile",
                "create_interview",
                "read_own_interviews",
                "read_candidate_profiles",
                "read_candidate_resumes",
                "conduct_live_interview",
                "read_dashboard",
                "read_analytics"
            ],
            UserRole.ADMIN: [
                "read_own_profile",
                "update_own_profile",
                "manage_users",
                "manage_interviews",
                "manage_system",
                "read_all_analytics",
                "configure_system",
                "audit_logs"
            ]
        }

        user_permissions = role_permissions.get(current_user.role, [])

        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {permission}"
                )

        return current_user
    return dependency

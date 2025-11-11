"""
User management routes for profile operations and user administration.
"""
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import User, UserUpdate, UserProfile, UserStatus, UserRole
from app.models import get_database
from app.auth.dependencies import get_current_user, get_current_admin, check_permissions

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.
    """
    return UserProfile(**current_user.dict())

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update current user's profile information.
    """
    # Prepare update data
    update_data = profile_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Add updated timestamp
    update_data["updated_at"] = current_user.created_at.utcnow().replace(tzinfo=None)

    # Update user in database
    result = await db.users.update_one(
        {"_id": current_user.id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile update failed"
        )

    # Get updated user
    updated_user_doc = await db.users.find_one({"_id": current_user.id})
    updated_user = User(**updated_user_doc)

    logger.info(f"Profile updated for user: {current_user.email}")

    return UserProfile(**updated_user.dict())

@router.get("/users", response_model=List[UserProfile])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List users with filtering and pagination (Admin only).
    """
    # Build query
    query = {}

    if role:
        query["role"] = role.value

    if status:
        query["status"] = status.value

    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}}
        ]

    # Get users
    cursor = db.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
    users_docs = await cursor.to_list(length=None)

    users = [User(**doc) for doc in users_docs]

    return [UserProfile(**user.dict()) for user in users]

@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get user by ID (Admin only).
    """
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = User(**user_doc)
    return UserProfile(**user.dict())

@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update user information (Admin only).
    """
    # Check if user exists
    existing_user_doc = await db.users.find_one({"_id": user_id})
    if not existing_user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prepare update data
    update_data = user_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Add updated timestamp and updater info
    update_data["updated_at"] = current_user.created_at.utcnow().replace(tzinfo=None)
    update_data["updated_by"] = current_user.id

    # Update user
    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User update failed"
        )

    # Get updated user
    updated_user_doc = await db.users.find_one({"_id": user_id})
    updated_user = User(**updated_user_doc)

    logger.info(f"User updated by admin {current_user.email}: {updated_user.email}")

    return UserProfile(**updated_user.dict())

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status: UserStatus,
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update user account status (Admin only).
    """
    # Check if user exists
    existing_user_doc = await db.users.find_one({"_id": user_id})
    if not existing_user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from deactivating themselves
    if user_id == current_user.id and status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own account status"
        )

    # Update user status
    result = await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "status": status.value,
                "updated_at": current_user.created_at.utcnow().replace(tzinfo=None),
                "updated_by": current_user.id
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status update failed"
        )

    logger.info(f"User status updated by admin {current_user.email}: {user_id} -> {status.value}")

    return {"message": f"User status updated to {status.value}"}

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update user role (Admin only).
    """
    # Check if user exists
    existing_user_doc = await db.users.find_one({"_id": user_id})
    if not existing_user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from changing their own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Update user role
    result = await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "role": role.value,
                "updated_at": current_user.created_at.utcnow().replace(tzinfo=None),
                "updated_by": current_user.id
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role update failed"
        )

    logger.info(f"User role updated by admin {current_user.email}: {user_id} -> {role.value}")

    return {"message": f"User role updated to {role.value}"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete user account (Admin only).
    """
    # Check if user exists
    existing_user_doc = await db.users.find_one({"_id": user_id})
    if not existing_user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Delete user
    result = await db.users.delete_one({"_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User deletion failed"
        )

    logger.info(f"User deleted by admin {current_user.email}: {user_id}")

    return {"message": "User deleted successfully"}

@router.get("/stats")
async def get_user_statistics(
    current_user: User = Depends(check_permissions(["manage_users"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get user statistics (Admin only).
    """
    # Get user counts by role
    pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    role_stats = await db.users.aggregate(pipeline).to_list(length=None)

    # Get user counts by status
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    status_stats = await db.users.aggregate(pipeline).to_list(length=None)

    # Get total users
    total_users = await db.users.count_documents({})

    # Get recent registrations (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = await db.users.count_documents({"created_at": {"$gte": thirty_days_ago}})

    return {
        "total_users": total_users,
        "recent_registrations": recent_users,
        "role_distribution": {stat["_id"]: stat["count"] for stat in role_stats},
        "status_distribution": {stat["_id"]: stat["count"] for stat in status_stats}
    }

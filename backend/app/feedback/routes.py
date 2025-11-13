"""
Feedback routes for collecting and managing user feedback.
"""
from datetime import datetime
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import (
    Feedback, FeedbackCreate, FeedbackResponse, User
)
from app.models import get_database
from app.auth.dependencies import get_current_user, get_optional_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit user feedback.
    Anonymous feedback is allowed.
    """
    # Create feedback document
    feedback_dict = feedback_data.dict()
    feedback_dict["user_id"] = current_user.id if current_user else None
    feedback_dict["user_agent"] = request.headers.get("user-agent")
    feedback_dict["created_at"] = datetime.utcnow()
    feedback_dict["updated_at"] = datetime.utcnow()

    result = await db.feedback.insert_one(feedback_dict)
    feedback_id = result.inserted_id

    # Get created feedback
    from bson import ObjectId
    feedback_doc = await db.feedback.find_one({"_id": ObjectId(feedback_id)})
    feedback = Feedback.from_mongo(feedback_doc)

    logger.info(f"Feedback submitted: {feedback.subject} (ID: {feedback_id})")

    return FeedbackResponse(
        id=str(feedback_id),
        user_id=feedback.user_id,
        feedback_type=feedback.feedback_type,
        subject=feedback.subject,
        message=feedback.message,
        rating=feedback.rating,
        page_url=feedback.page_url,
        status=feedback.status,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )

@router.get("/", response_model=List[FeedbackResponse])
async def get_feedback_list(
    feedback_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get list of feedback submissions.
    Admin and recruiter roles can view all feedback.
    Regular users can only view their own feedback.
    """
    query = {}

    # Filter by user if not admin/recruiter
    if current_user.role.value not in ["admin", "recruiter"]:
        query["user_id"] = current_user.id

    # Additional filters
    if feedback_type:
        query["feedback_type"] = feedback_type
    if status:
        query["status"] = status

    cursor = db.feedback.find(query).sort("created_at", -1)
    feedback_docs = await cursor.to_list(length=None)

    feedback_list = []
    for doc in feedback_docs:
        feedback = Feedback.from_mongo(doc)
        feedback_list.append(FeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            feedback_type=feedback.feedback_type,
            subject=feedback.subject,
            message=feedback.message,
            rating=feedback.rating,
            page_url=feedback.page_url,
            status=feedback.status,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at
        ))

    return feedback_list

@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get specific feedback by ID.
    Users can only view their own feedback unless they are admin/recruiter.
    """
    from bson import ObjectId

    feedback_doc = await db.feedback.find_one({"_id": ObjectId(feedback_id)})
    if not feedback_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    feedback = Feedback.from_mongo(feedback_doc)

    # Check permissions
    if (current_user.role.value not in ["admin", "recruiter"] and
        feedback.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this feedback"
        )

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        feedback_type=feedback.feedback_type,
        subject=feedback.subject,
        message=feedback.message,
        rating=feedback.rating,
        page_url=feedback.page_url,
        status=feedback.status,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )

@router.put("/{feedback_id}/status", response_model=FeedbackResponse)
async def update_feedback_status(
    feedback_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update feedback status (admin/recruiter only).
    """
    # Check permissions
    if current_user.role.value not in ["admin", "recruiter"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update feedback status"
        )

    from bson import ObjectId

    # Validate status
    valid_statuses = ["pending", "reviewed", "resolved"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Update feedback
    result = await db.feedback.update_one(
        {"_id": ObjectId(feedback_id)},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    # Get updated feedback
    feedback_doc = await db.feedback.find_one({"_id": ObjectId(feedback_id)})
    feedback = Feedback.from_mongo(feedback_doc)

    logger.info(f"Feedback status updated: {feedback_id} -> {status}")

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        feedback_type=feedback.feedback_type,
        subject=feedback.subject,
        message=feedback.message,
        rating=feedback.rating,
        page_url=feedback.page_url,
        status=feedback.status,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )

@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete feedback.
    Users can delete their own feedback, admins can delete any.
    """
    from bson import ObjectId

    # Get feedback first to check ownership
    feedback_doc = await db.feedback.find_one({"_id": ObjectId(feedback_id)})
    if not feedback_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    feedback = Feedback.from_mongo(feedback_doc)

    # Check permissions
    if (current_user.role.value not in ["admin", "recruiter"] and
        feedback.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this feedback"
        )

    # Delete feedback
    result = await db.feedback.delete_one({"_id": ObjectId(feedback_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    logger.info(f"Feedback deleted: {feedback_id}")

    return {"message": "Feedback deleted successfully"}

@router.get("/stats/summary")
async def get_feedback_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get feedback statistics summary (admin/recruiter only).
    """
    if current_user.role.value not in ["admin", "recruiter"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view feedback statistics"
        )

    # Get total feedback count
    total_count = await db.feedback.count_documents({})

    # Get feedback by type
    type_pipeline = [
        {"$group": {"_id": "$feedback_type", "count": {"$sum": 1}}}
    ]
    type_stats = await db.feedback.aggregate(type_pipeline).to_list(length=None)

    # Get feedback by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_stats = await db.feedback.aggregate(status_pipeline).to_list(length=None)

    # Get average rating
    rating_pipeline = [
        {"$match": {"rating": {"$ne": None}}},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
    ]
    rating_result = await db.feedback.aggregate(rating_pipeline).to_list(length=1)
    avg_rating = rating_result[0]["avg_rating"] if rating_result else None

    return {
        "total_feedback": total_count,
        "feedback_by_type": {item["_id"]: item["count"] for item in type_stats},
        "feedback_by_status": {item["_id"]: item["count"] for item in status_stats},
        "average_rating": round(avg_rating, 2) if avg_rating else None
    }

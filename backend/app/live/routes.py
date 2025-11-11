"""
Live interview routes for scheduling and managing real-time video interviews.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.live_interview import (
    LiveInterviewSession, LiveInterviewCreate, LiveInterviewUpdate, LiveInterviewResponse,
    InterviewRoom, InterviewRoomResponse, LiveInterviewStatus, LiveInterviewType,
    InterviewFeedback, InterviewMessage, InterviewRecording, InterviewSignalingMessage,
    WebRTCSessionDescription, WebRTCIceCandidate
)
from app.models.user import User, UserRole
from app.models import get_database, get_redis
from app.auth.dependencies import get_current_user, check_permissions
from app.websocket.routes import manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=LiveInterviewResponse)
async def create_live_interview(
    interview_data: LiveInterviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new live interview session.
    """
    # Verify user is a recruiter or admin
    if current_user.role not in [UserRole.RECRUITER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters and admins can schedule live interviews"
        )

    # Verify candidate exists
    candidate_doc = await db.users.find_one({"_id": interview_data.candidate_id})
    if not candidate_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    # Check for scheduling conflicts
    conflict_query = {
        "$or": [
            {"interviewer_id": current_user.id},
            {"candidate_id": interview_data.candidate_id}
        ],
        "scheduled_at": {
            "$gte": interview_data.scheduled_at - timedelta(minutes=30),
            "$lte": interview_data.scheduled_at + timedelta(minutes=interview_data.duration_minutes + 30)
        },
        "status": {"$in": ["scheduled", "waiting", "in_progress"]}
    }

    conflict = await db.live_interviews.find_one(conflict_query)
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scheduling conflict detected"
        )

    # Create interview session
    interview_dict = interview_data.dict()
    interview_dict["interviewer_id"] = current_user.id
    interview_dict["interviewer_name"] = current_user.full_name
    interview_dict["status"] = LiveInterviewStatus.SCHEDULED
    interview_dict["created_at"] = datetime.utcnow()
    interview_dict["updated_at"] = datetime.utcnow()
    interview_dict["created_by"] = current_user.id

    result = await db.live_interviews.insert_one(interview_dict)
    interview_id = str(result.inserted_id)

    # Get created interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    interview = LiveInterviewSession(**interview_doc)

    logger.info(f"Live interview created: {interview_id} by {current_user.email}")

    return LiveInterviewResponse(**interview.dict())

@router.get("/", response_model=List[LiveInterviewResponse])
async def list_live_interviews(
    status_filter: Optional[LiveInterviewStatus] = None,
    type_filter: Optional[LiveInterviewType] = None,
    upcoming_only: bool = False,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List live interviews for the current user.
    """
    # Build query based on user role
    query = {}
    if current_user.role == UserRole.RECRUITER:
        query["interviewer_id"] = current_user.id
    elif current_user.role == UserRole.CANDIDATE:
        query["candidate_id"] = current_user.id
    else:  # Admin
        # Admins can see all interviews
        pass

    if status_filter:
        query["status"] = status_filter.value

    if type_filter:
        query["interview_type"] = type_filter.value

    if upcoming_only:
        query["scheduled_at"] = {"$gte": datetime.utcnow()}

    # Get interviews
    cursor = db.live_interviews.find(query).sort("scheduled_at", -1).skip(skip).limit(limit)
    interviews_docs = await cursor.to_list(length=None)

    interviews = [LiveInterviewSession(**doc) for doc in interviews_docs]

    return [LiveInterviewResponse(**interview.dict()) for interview in interviews]

@router.get("/{interview_id}", response_model=LiveInterviewResponse)
async def get_live_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get live interview details.
    """
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    # Check access permissions
    if current_user.role not in [UserRole.ADMIN] and \
       interview.interviewer_id != current_user.id and \
       interview.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return LiveInterviewResponse(**interview.dict())

@router.put("/{interview_id}", response_model=LiveInterviewResponse)
async def update_live_interview(
    interview_id: str,
    interview_data: LiveInterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update live interview details.
    """
    # Get existing interview
    existing_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    existing_interview = LiveInterviewSession(**existing_doc)

    # Check permissions
    if current_user.role not in [UserRole.ADMIN] and existing_interview.interviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interviewers and admins can update interviews"
        )

    # Prevent updates to completed/cancelled interviews
    if existing_interview.status in [LiveInterviewStatus.COMPLETED, LiveInterviewStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update completed or cancelled interviews"
        )

    # Prepare update data
    update_data = interview_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id

    # Update interview
    result = await db.live_interviews.update_one(
        {"_id": interview_id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview update failed"
        )

    # Get updated interview
    updated_doc = await db.live_interviews.find_one({"_id": interview_id})
    updated_interview = LiveInterviewSession(**updated_doc)

    logger.info(f"Live interview updated: {interview_id}")

    return LiveInterviewResponse(**updated_interview.dict())

@router.delete("/{interview_id}")
async def delete_live_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a live interview.
    """
    # Get existing interview
    existing_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    existing_interview = LiveInterviewSession(**existing_doc)

    # Check permissions
    if current_user.role not in [UserRole.ADMIN] and existing_interview.interviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interviewers and admins can delete interviews"
        )

    # Prevent deletion of in-progress interviews
    if existing_interview.status == LiveInterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete in-progress interviews"
        )

    # Delete interview
    result = await db.live_interviews.delete_one({"_id": interview_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview deletion failed"
        )

    # Clean up related data
    await db.interview_messages.delete_many({"interview_id": interview_id})
    await db.interview_recordings.delete_many({"interview_id": interview_id})

    # Clean up interview room if exists
    if existing_interview.room_id:
        await db.interview_rooms.delete_one({"room_id": existing_interview.room_id})

    logger.info(f"Live interview deleted: {interview_id}")

    return {"message": "Live interview deleted successfully"}

@router.post("/{interview_id}/start")
async def start_live_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Start a live interview session.
    """
    # Get interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    # Check permissions
    if current_user.role not in [UserRole.ADMIN] and interview.interviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interviewers and admins can start interviews"
        )

    # Check if interview can be started
    if interview.status != LiveInterviewStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview cannot be started (status: {interview.status.value})"
        )

    # Check if interview is scheduled to start within reasonable time
    now = datetime.utcnow()
    if abs((interview.scheduled_at - now).total_seconds()) > 1800:  # 30 minutes
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview can only be started within 30 minutes of scheduled time"
        )

    # Create interview room
    room_id = str(uuid.uuid4())
    room = InterviewRoom(
        room_id=room_id,
        live_interview_id=interview_id,
        webrtc_config=get_webrtc_config(),
        turn_servers=get_turn_servers(),
        stun_servers=get_stun_servers(),
        expires_at=now + timedelta(hours=2)  # Room expires in 2 hours
    )

    await db.interview_rooms.insert_one(room.dict())

    # Update interview status
    update_data = {
        "status": LiveInterviewStatus.IN_PROGRESS.value,
        "room_id": room_id,
        "started_at": now,
        "updated_at": now
    }

    await db.live_interviews.update_one(
        {"_id": interview_id},
        {"$set": update_data}
    )

    logger.info(f"Live interview started: {interview_id}")

    return {
        "message": "Live interview started successfully",
        "room_id": room_id
    }

@router.post("/{interview_id}/join")
async def join_live_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Join a live interview room.
    """
    # Get interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    # Check permissions
    if current_user.role not in [UserRole.ADMIN] and \
       interview.interviewer_id != current_user.id and \
       interview.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if interview is in progress
    if interview.status != LiveInterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not in progress"
        )

    # Get room details
    room_doc = await db.interview_rooms.find_one({"room_id": interview.room_id})
    if not room_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview room not found"
        )

    room = InterviewRoom(**room_doc)

    # Generate access token for user
    access_token = str(uuid.uuid4())
    room.access_tokens[current_user.id] = access_token

    # Update room
    await db.interview_rooms.update_one(
        {"room_id": room.room_id},
        {"$set": {"access_tokens": room.access_tokens}}
    )

    # Log participant join
    participant_data = {
        "user_id": current_user.id,
        "name": current_user.full_name,
        "role": "interviewer" if interview.interviewer_id == current_user.id else "candidate",
        "joined_at": datetime.utcnow()
    }

    await db.live_interviews.update_one(
        {"_id": interview_id},
        {"$push": {"participants": participant_data}}
    )

    room_response = InterviewRoomResponse(
        room_id=room.room_id,
        webrtc_config=room.webrtc_config,
        turn_servers=room.turn_servers,
        stun_servers=room.stun_servers,
        max_participants=room.max_participants,
        allow_screen_share=room.allow_screen_share,
        allow_file_share=room.allow_file_share,
        recording_enabled=room.recording_enabled,
        access_token=access_token,
        expires_at=room.expires_at
    )

    logger.info(f"User {current_user.email} joined live interview: {interview_id}")

    return room_response

@router.post("/{interview_id}/end")
async def end_live_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    End a live interview session.
    """
    # Get interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    # Check permissions
    if current_user.role not in [UserRole.ADMIN] and interview.interviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interviewers and admins can end interviews"
        )

    # Check if interview is in progress
    if interview.status != LiveInterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not in progress"
        )

    # Calculate actual duration
    now = datetime.utcnow()
    actual_duration = int((now - (interview.started_at or now)).total_seconds() / 60)

    # Update interview status
    update_data = {
        "status": LiveInterviewStatus.COMPLETED.value,
        "ended_at": now,
        "actual_duration": actual_duration,
        "updated_at": now
    }

    await db.live_interviews.update_one(
        {"_id": interview_id},
        {"$set": update_data}
    )

    # Deactivate room
    if interview.room_id:
        await db.interview_rooms.update_one(
            {"room_id": interview.room_id},
            {"$set": {"is_active": False}}
        )

    logger.info(f"Live interview ended: {interview_id}")

    return {"message": "Live interview ended successfully"}

@router.post("/{interview_id}/feedback")
async def submit_interview_feedback(
    interview_id: str,
    feedback: InterviewFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit feedback for a completed live interview.
    """
    # Get interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    # Check if interview is completed
    if interview.status != LiveInterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted for completed interviews"
        )

    # Determine feedback type
    feedback_field = None
    if interview.interviewer_id == current_user.id:
        feedback_field = "interviewer_feedback"
    elif interview.candidate_id == current_user.id:
        feedback_field = "candidate_feedback"
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interview participants can submit feedback"
        )

    # Submit feedback
    feedback_data = feedback.dict()
    feedback_data["submitted_at"] = datetime.utcnow()
    feedback_data["submitted_by"] = current_user.id

    await db.live_interviews.update_one(
        {"_id": interview_id},
        {
            "$set": {
                feedback_field: feedback_data,
                "overall_rating": feedback.overall_rating,
                "updated_at": datetime.utcnow()
            }
        }
    )

    logger.info(f"Feedback submitted for interview {interview_id} by {current_user.email}")

    return {"message": "Feedback submitted successfully"}

@router.get("/{interview_id}/messages")
async def get_interview_messages(
    interview_id: str,
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get chat messages for a live interview.
    """
    # Verify access to interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    if current_user.role not in [UserRole.ADMIN] and \
       interview.interviewer_id != current_user.id and \
       interview.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get messages
    query = {"interview_id": interview_id}
    if since:
        query["timestamp"] = {"$gte": since}

    cursor = db.interview_messages.find(query).sort("timestamp", 1)
    messages = await cursor.to_list(length=None)

    return {"messages": messages}

@router.post("/{interview_id}/messages")
async def send_interview_message(
    interview_id: str,
    message: str,
    message_type: str = "text",
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send a chat message in a live interview.
    """
    # Verify access to interview
    interview_doc = await db.live_interviews.find_one({"_id": interview_id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live interview not found"
        )

    interview = LiveInterviewSession(**interview_doc)

    if current_user.role not in [UserRole.ADMIN] and \
       interview.interviewer_id != current_user.id and \
       interview.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Create message
    message_doc = {
        "id": str(uuid.uuid4()),
        "interview_id": interview_id,
        "sender_id": current_user.id,
        "sender_name": current_user.full_name,
        "message_type": message_type,
        "content": message,
        "timestamp": datetime.utcnow()
    }

    await db.interview_messages.insert_one(message_doc)

    # Broadcast message via WebSocket
    await manager.broadcast_to_interview({
        "type": "chat_message",
        "message": message_doc
    }, interview.room_id or interview_id)

    return {"message": "Message sent successfully"}

# Helper functions
def get_webrtc_config() -> Dict[str, Any]:
    """Get WebRTC configuration."""
    return {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"}
        ],
        "iceCandidatePoolSize": 10
    }

def get_turn_servers() -> List[Dict[str, str]]:
    """Get TURN server configuration."""
    # In production, use actual TURN servers
    return [
        {
            "urls": "turn:turn.example.com:3478",
            "username": "user",
            "credential": "pass"
        }
    ]

def get_stun_servers() -> List[str]:
    """Get STUN server URLs."""
    return [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
        "stun:stun2.l.google.com:19302"
    ]

"""
Interview management routes for creating, conducting, and managing interviews.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

from app.models.interview import (
    InterviewSession, InterviewCreate, InterviewUpdate, InterviewSessionResponse,
    InterviewSummary, InterviewAnalytics, InterviewStatus, InterviewType, InterviewMode,
    AntiCheatEvent
)
from app.models.user import User
from app.models import get_database, get_redis
from app.auth.dependencies import get_current_user, check_permissions
from app.ai.service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/test", response_model=dict)
async def test_interview_creation():
    """Test endpoint without authentication."""
    return {"message": "Test endpoint works"}

@router.post("/", response_model=InterviewSessionResponse)
async def create_interview(
    interview_data: InterviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new interview session.
    """
    # Create interview session
    interview_dict = interview_data.dict()
    interview_dict["user_id"] = current_user.id
    interview_dict["status"] = InterviewStatus.CREATED
    interview_dict["created_at"] = datetime.utcnow()
    interview_dict["updated_at"] = datetime.utcnow()
    interview_dict["created_by"] = current_user.id

    # Create basic fallback questions directly (skip AI service for now)
    fallback_questions = []
    base_questions = [
        {
            "question_text": "Tell me about yourself and your background.",
            "type": "text",
            "category": "behavioral",
            "difficulty_level": "easy",
            "skills_assessed": ["communication"],
            "time_limit": 300
        },
        {
            "question_text": "What are your greatest strengths?",
            "type": "text",
            "category": "behavioral",
            "difficulty_level": "easy",
            "skills_assessed": ["self-awareness"],
            "time_limit": 300
        },
        {
            "question_text": "Describe a challenging situation you faced and how you handled it.",
            "type": "text",
            "category": "behavioral",
            "difficulty_level": "medium",
            "skills_assessed": ["problem-solving", "communication"],
            "time_limit": 300
        },
        {
            "question_text": "Where do you see yourself in 5 years?",
            "type": "text",
            "category": "behavioral",
            "difficulty_level": "medium",
            "skills_assessed": ["planning", "career-goals"],
            "time_limit": 300
        },
        {
            "question_text": "Why are you interested in this position?",
            "type": "text",
            "category": "behavioral",
            "difficulty_level": "easy",
            "skills_assessed": ["motivation"],
            "time_limit": 300
        }
    ]

    # Generate requested number of questions
    for i in range(interview_data.question_count):
        question = base_questions[i % len(base_questions)].copy()
        question["question_text"] = f"{question['question_text']} (Question {i+1})"
        fallback_questions.append(question)

    interview_dict["questions"] = fallback_questions
    interview_dict["status"] = InterviewStatus.CREATED
    logger.info(f"Created {len(fallback_questions)} questions for interview")

    try:
        result = await db.interviews.insert_one(interview_dict)
        interview_id = str(result.inserted_id)
        logger.info(f"Database insertion successful, ID: {interview_id}")

        # Get created interview
        interview_doc = await db.interviews.find_one({"_id": interview_id})
        if not interview_doc:
            logger.error("Failed to retrieve created interview")
            raise HTTPException(status_code=500, detail="Failed to retrieve created interview")

        interview = InterviewSession(**interview_doc)
        logger.info(f"Interview model created successfully")

        response_data = InterviewSessionResponse(**interview.dict())
        logger.info(f"Response model created successfully")

        return response_data
    except Exception as e:
        logger.error(f"Error in interview creation: {e}")
        raise HTTPException(status_code=500, detail=f"Interview creation failed: {str(e)}")

@router.get("/", response_model=List[InterviewSummary])
async def list_user_interviews(
    skip: int = 0,
    limit: int = 20,
    status: Optional[InterviewStatus] = None,
    type: Optional[InterviewType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List user's interview sessions.
    """
    # Build query
    query = {"user_id": current_user.id}
    if status:
        query["status"] = status.value
    if type:
        query["type"] = type.value

    # Get interviews
    cursor = db.interviews.find(query).skip(skip).limit(limit).sort("created_at", -1)
    interviews_docs = await cursor.to_list(length=None)

    interviews = [InterviewSession(**doc) for doc in interviews_docs]

    return [
        InterviewSummary(
            id=interview.id,
            job_title=interview.job_title,
            type=interview.type,
            mode=interview.mode,
            status=interview.status,
            overall_score=interview.overall_score,
            question_count=len(interview.questions),
            completed_questions=len([r for r in interview.responses if r.get("submitted_at")]),
            total_duration=interview.total_duration,
            completed_at=interview.completed_at,
            ai_feedback=interview.ai_feedback
        )
        for interview in interviews
    ]

@router.get("/{interview_id}", response_model=InterviewSessionResponse)
async def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get interview session details.
    """
    interview_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    interview = InterviewSession(**interview_doc)
    return InterviewSessionResponse(**interview.dict())

@router.put("/{interview_id}", response_model=InterviewSessionResponse)
async def update_interview(
    interview_id: str,
    interview_data: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update interview session.
    """
    # Check if interview exists and belongs to user
    existing_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    existing_interview = InterviewSession(**existing_doc)

    # Prevent updates to completed or in-progress interviews
    if existing_interview.status in [InterviewStatus.COMPLETED, InterviewStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update completed or in-progress interviews"
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
    result = await db.interviews.update_one(
        {"_id": interview_id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview update failed"
        )

    # Get updated interview
    updated_doc = await db.interviews.find_one({"_id": interview_id})
    updated_interview = InterviewSession(**updated_doc)

    logger.info(f"Interview updated: {interview_id}")

    return InterviewSessionResponse(**updated_interview.dict())

@router.delete("/{interview_id}")
async def delete_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete interview session.
    """
    # Check if interview exists and belongs to user
    existing_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    existing_interview = InterviewSession(**existing_doc)

    # Prevent deletion of in-progress interviews
    if existing_interview.status == InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete in-progress interviews"
        )

    # Delete interview
    result = await db.interviews.delete_one({"_id": interview_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview deletion failed"
        )

    logger.info(f"Interview deleted: {interview_id}")

    return {"message": "Interview deleted successfully"}

@router.post("/{interview_id}/start")
async def start_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Start an interview session.
    """
    # Check if interview exists and belongs to user
    interview_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    interview = InterviewSession(**interview_doc)

    # Check if interview can be started
    if interview.status != InterviewStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview cannot be started (status: {interview.status.value})"
        )

    if not interview.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview questions not ready yet"
        )

    # Start interview
    now = datetime.utcnow()
    update_data = {
        "status": InterviewStatus.IN_PROGRESS.value,
        "started_at": now,
        "updated_at": now
    }

    # Initialize responses if not exists
    if not interview.responses:
        update_data["responses"] = [
            {
                "question_id": q.get("id", f"q{i}"),
                "started_at": now,
                "time_spent": 0
            }
            for i, q in enumerate(interview.questions)
        ]

    result = await db.interviews.update_one(
        {"_id": interview_id},
        {"$set": update_data}
    )

    # Store session in Redis for real-time tracking
    session_data = {
        "interview_id": interview_id,
        "user_id": current_user.id,
        "current_question": 0,
        "start_time": now.isoformat(),
        "anti_cheat_events": []
    }
    await redis_client.setex(f"interview_session:{interview_id}", 3600, json.dumps(session_data))

    logger.info(f"Interview started: {interview_id}")

    return {"message": "Interview started successfully"}

@router.post("/{interview_id}/submit-response")
async def submit_response(
    interview_id: str,
    question_index: int,
    response_text: Optional[str] = None,
    time_spent: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit response for a question.
    """
    # Check if interview exists and belongs to user
    interview_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    interview = InterviewSession(**interview_doc)

    # Check if interview is in progress
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not in progress"
        )

    # Validate question index
    if question_index < 0 or question_index >= len(interview.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question index"
        )

    # Update response
    responses = interview.responses.copy()
    if question_index >= len(responses):
        responses.extend([{}] * (question_index - len(responses) + 1))

    response_data = responses[question_index]
    response_data["response_text"] = response_text
    response_data["submitted_at"] = datetime.utcnow()
    response_data["time_spent"] = time_spent or response_data.get("time_spent", 0)

    # Evaluate response with AI (background task)
    question = interview.questions[question_index]
    if response_text:
        background_tasks.add_task(
            evaluate_response_background,
            interview_id,
            question_index,
            question.get("question_text", ""),
            response_text
        )

    # Update interview
    await db.interviews.update_one(
        {"_id": interview_id},
        {
            "$set": {
                "responses": responses,
                "updated_at": datetime.utcnow()
            }
        }
    )

    logger.info(f"Response submitted for interview {interview_id}, question {question_index}")

    return {"message": "Response submitted successfully"}

@router.post("/{interview_id}/complete")
async def complete_interview(
    interview_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Complete an interview session.
    """
    # Check if interview exists and belongs to user
    interview_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not interview_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    interview = InterviewSession(**interview_doc)

    # Check if interview is in progress
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not in progress"
        )

    # Calculate total duration
    now = datetime.utcnow()
    total_duration = int((now - interview.started_at).total_seconds()) if interview.started_at else 0

    # Update interview status
    update_data = {
        "status": InterviewStatus.COMPLETED.value,
        "completed_at": now,
        "total_duration": total_duration,
        "updated_at": now
    }

    await db.interviews.update_one(
        {"_id": interview_id},
        {"$set": update_data}
    )

    # Generate overall feedback (background task)
    background_tasks.add_task(
        generate_overall_feedback_background,
        interview_id,
        interview.job_title,
        interview.experience_level
    )

    # Clean up Redis session
    await redis_client.delete(f"interview_session:{interview_id}")

    logger.info(f"Interview completed: {interview_id}")

    return {"message": "Interview completed successfully"}

@router.get("/analytics/overview", response_model=InterviewAnalytics)
async def get_interview_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get interview analytics for the current user.
    """
    # Get user's interviews
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": None,
            "total_interviews": {"$sum": 1},
            "completed_interviews": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "total_score": {"$sum": {"$ifNull": ["$overall_score", 0]}},
            "total_duration": {"$sum": {"$ifNull": ["$total_duration", 0]}},
            "interviews": {"$push": {
                "id": "$_id",
                "job_title": "$job_title",
                "type": "$type",
                "mode": "$mode",
                "status": "$status",
                "overall_score": "$overall_score",
                "completed_at": "$completed_at"
            }}
        }}
    ]

    result = await db.interviews.aggregate(pipeline).to_list(length=1)
    stats = result[0] if result else {
        "total_interviews": 0,
        "completed_interviews": 0,
        "total_score": 0,
        "total_duration": 0,
        "interviews": []
    }

    # Calculate averages
    average_score = (stats["total_score"] / stats["completed_interviews"]) if stats["completed_interviews"] > 0 else None
    average_duration = (stats["total_duration"] / stats["completed_interviews"]) if stats["completed_interviews"] > 0 else None

    # Get type and mode distributions
    type_pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    mode_pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": "$mode", "count": {"$sum": 1}}}
    ]

    type_stats = await db.interviews.aggregate(type_pipeline).to_list(length=None)
    mode_stats = await db.interviews.aggregate(mode_pipeline).to_list(length=None)

    # Get recent interviews
    recent_cursor = db.interviews.find({"user_id": current_user.id}).sort("created_at", -1).limit(10)
    recent_docs = await recent_cursor.to_list(length=None)
    recent_interviews = [
        InterviewSummary(
            id=str(doc["_id"]),
            job_title=doc["job_title"],
            type=doc["type"],
            mode=doc["mode"],
            status=doc["status"],
            overall_score=doc.get("overall_score"),
            question_count=len(doc.get("questions", [])),
            completed_questions=len([r for r in doc.get("responses", []) if r.get("submitted_at")]),
            total_duration=doc.get("total_duration"),
            completed_at=doc.get("completed_at"),
            ai_feedback=doc.get("ai_feedback")
        )
        for doc in recent_docs
    ]

    return InterviewAnalytics(
        total_interviews=stats["total_interviews"],
        completed_interviews=stats["completed_interviews"],
        average_score=average_score,
        average_duration=average_duration,
        interviews_by_type={stat["_id"]: stat["count"] for stat in type_stats},
        interviews_by_mode={stat["_id"]: stat["count"] for stat in mode_stats},
        score_distribution={},  # TODO: Implement score distribution
        recent_interviews=recent_interviews
    )

# Background tasks
async def generate_interview_questions_background(
    interview_id: str,
    job_title: str,
    job_description: Optional[str],
    experience_level: str,
    question_count: int,
    interview_mode: str,
    interview_type: str
):
    """Background task to generate interview questions."""
    try:
        db = await get_database()
        questions = await ai_service.generate_interview_questions(
            job_title, job_description, experience_level,
            question_count, interview_mode, interview_type
        )

        # Update interview with generated questions
        await db.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "questions": questions,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Questions generated for interview: {interview_id}")

    except Exception as e:
        logger.error(f"Failed to generate questions for interview {interview_id}: {e}")

async def evaluate_response_background(
    interview_id: str,
    question_index: int,
    question_text: str,
    response_text: str
):
    """Background task to evaluate response."""
    try:
        db = await get_database()
        evaluation = await ai_service.evaluate_response(question_text, response_text)

        # Update response with evaluation
        await db.interviews.update_one(
            {"_id": interview_id, f"responses.{question_index}": {"$exists": True}},
            {
                "$set": {
                    f"responses.{question_index}.ai_score": evaluation["score"],
                    f"responses.{question_index}.ai_feedback": evaluation["feedback"],
                    f"responses.{question_index}.strengths": evaluation["strengths"],
                    f"responses.{question_index}.improvements": evaluation["improvements"],
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Response evaluated for interview {interview_id}, question {question_index}")

    except Exception as e:
        logger.error(f"Failed to evaluate response for interview {interview_id}: {e}")

async def generate_overall_feedback_background(
    interview_id: str,
    job_title: str,
    experience_level: str
):
    """Background task to generate overall feedback."""
    try:
        db = await get_database()

        # Get interview with responses
        interview_doc = await db.interviews.find_one({"_id": interview_id})
        if not interview_doc:
            return

        interview = InterviewSession(**interview_doc)
        responses = interview.responses

        # Check if there are any actual responses (not empty/null)
        has_actual_responses = any(
            r.get("response_text") and r.get("response_text").strip()
            for r in responses
        )

        if not has_actual_responses:
            # No actual responses provided - don't generate fake feedback
            feedback = {
                "overall_score": 0,
                "overall_feedback": "No responses were provided for evaluation.",
                "strengths": [],
                "weaknesses": ["No responses submitted"],
                "recommendations": [
                    {"title": "Complete the Interview", "description": "Please provide answers to the interview questions to receive personalized feedback."}
                ],
                "communication_score": 0,
                "technical_score": 0,
                "problem_solving_score": 0,
                "behavioral_score": 0
            }
        else:
            # Generate feedback using AI
            feedback = await ai_service.generate_overall_feedback(
                responses, job_title, experience_level
            )

        # Update interview with feedback
        await db.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "overall_score": feedback["overall_score"],
                    "ai_feedback": feedback,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Overall feedback generated for interview: {interview_id}")

    except Exception as e:
        logger.error(f"Failed to generate feedback for interview {interview_id}: {e}")

# WebSocket endpoint for real-time interview management
@router.websocket("/{interview_id}/ws")
async def interview_websocket(
    interview_id: str,
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    WebSocket endpoint for real-time interview interaction.
    """
    await websocket.accept()

    try:
        # Verify interview access
        interview_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
        if not interview_doc:
            await websocket.send_json({"error": "Interview not found"})
            await websocket.close()
            return

        interview = InterviewSession(**interview_doc)

        # Handle WebSocket messages
        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "start_question":
                question_index = data.get("question_index", 0)
                # Handle question start logic
                await websocket.send_json({
                    "type": "question_started",
                    "question_index": question_index,
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "submit_answer":
                question_index = data.get("question_index")
                answer = data.get("answer")
                # Handle answer submission
                await websocket.send_json({
                    "type": "answer_received",
                    "question_index": question_index,
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "anti_cheat_event":
                event_data = data.get("event", {})
                # Log anti-cheat event
                event = AntiCheatEvent(
                    session_id=interview_id,
                    user_id=current_user.id,
                    event_type=event_data.get("type", "unknown"),
                    description=event_data.get("description", ""),
                    metadata=event_data.get("metadata", {})
                )

                await db.anti_cheat_events.insert_one(event.dict())

                # Update interview with event
                await db.interviews.update_one(
                    {"_id": interview_id},
                    {
                        "$push": {"anti_cheat_events": event.dict()},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for interview: {interview_id}")
    except Exception as e:
        logger.error(f"WebSocket error for interview {interview_id}: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

"""
WebSocket routes for real-time communication.
"""
from typing import Dict, List, Any, Optional
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

from app.models.user import User
from app.models import get_database, get_redis
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Global connection manager
class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.interview_sessions: Dict[str, List[str]] = {}  # interview_id -> [user_ids]

    async def connect(self, websocket: WebSocket, user_id: str, interview_id: str = None):
        """Connect a user to a WebSocket."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        self.active_connections[user_id][interview_id or "general"] = websocket

        if interview_id:
            if interview_id not in self.interview_sessions:
                self.interview_sessions[interview_id] = []
            if user_id not in self.interview_sessions[interview_id]:
                self.interview_sessions[interview_id].append(user_id)

        logger.info(f"User {user_id} connected to WebSocket (interview: {interview_id})")

    def disconnect(self, user_id: str, interview_id: str = None):
        """Disconnect a user from WebSocket."""
        if user_id in self.active_connections:
            if interview_id and interview_id in self.active_connections[user_id]:
                del self.active_connections[user_id][interview_id]
            elif not interview_id:
                del self.active_connections[user_id]

        if interview_id and interview_id in self.interview_sessions:
            if user_id in self.interview_sessions[interview_id]:
                self.interview_sessions[interview_id].remove(user_id)
                if not self.interview_sessions[interview_id]:
                    del self.interview_sessions[interview_id]

        logger.info(f"User {user_id} disconnected from WebSocket (interview: {interview_id})")

    async def send_personal_message(self, message: Dict[str, Any], user_id: str, interview_id: str = None):
        """Send message to specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id].get(interview_id or "general")
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    self.disconnect(user_id, interview_id)

    async def broadcast_to_interview(self, message: Dict[str, Any], interview_id: str, exclude_user: str = None):
        """Broadcast message to all users in an interview session."""
        if interview_id in self.interview_sessions:
            for user_id in self.interview_sessions[interview_id]:
                if user_id != exclude_user:
                    await self.send_personal_message(message, user_id, interview_id)

    async def send_to_interview_participants(self, message: Dict[str, Any], interview_id: str, participant_ids: List[str]):
        """Send message to specific participants in an interview."""
        for user_id in participant_ids:
            await self.send_personal_message(message, user_id, interview_id)

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/interview/{interview_id}")
async def interview_websocket(
    websocket: WebSocket,
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    WebSocket endpoint for interview real-time communication.
    """
    # Verify interview access
    interview_doc = await db.interviews.find_one({"_id": interview_id, "user_id": current_user.id})
    if not interview_doc:
        await websocket.close(code=1008, reason="Interview not found or access denied")
        return

    await manager.connect(websocket, current_user.id, interview_id)

    try:
        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "start_question":
                question_index = data.get("question_index", 0)
                # Handle question start logic
                await manager.send_personal_message({
                    "type": "question_started",
                    "question_index": question_index,
                    "timestamp": asyncio.get_event_loop().time()
                }, current_user.id, interview_id)

            elif message_type == "submit_answer":
                question_index = data.get("question_index")
                answer = data.get("answer")
                time_spent = data.get("time_spent")

                # Store answer in Redis for real-time tracking
                answer_key = f"interview_answer:{interview_id}:{current_user.id}:{question_index}"
                await redis_client.setex(answer_key, 3600, json.dumps({
                    "answer": answer,
                    "time_spent": time_spent,
                    "submitted_at": asyncio.get_event_loop().time()
                }))

                # Broadcast to interviewers (if any)
                await manager.broadcast_to_interview({
                    "type": "answer_submitted",
                    "user_id": current_user.id,
                    "question_index": question_index,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "anti_cheat_event":
                event_data = data.get("event", {})
                severity = event_data.get("severity", "low")

                # Log anti-cheat event
                event = {
                    "session_id": interview_id,
                    "user_id": current_user.id,
                    "event_type": event_data.get("type", "unknown"),
                    "severity": severity,
                    "description": event_data.get("description", ""),
                    "timestamp": asyncio.get_event_loop().time(),
                    "metadata": event_data.get("metadata", {})
                }

                # Store in database
                await db.anti_cheat_events.insert_one(event)

                # Update interview with event
                await db.interviews.update_one(
                    {"_id": interview_id},
                    {"$push": {"anti_cheat_events": event}}
                )

                # Alert administrators for high-severity events
                if severity == "high":
                    await manager.send_personal_message({
                        "type": "admin_alert",
                        "message": f"High-severity anti-cheat event detected for user {current_user.id}",
                        "event": event
                    }, "admin", "system")  # Assuming admin user exists

            elif message_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                }, current_user.id, interview_id)

            elif message_type == "chat_message":
                message_text = data.get("message", "")
                recipient_id = data.get("recipient_id")

                if recipient_id:
                    # Private message
                    await manager.send_personal_message({
                        "type": "chat_message",
                        "sender_id": current_user.id,
                        "message": message_text,
                        "timestamp": asyncio.get_event_loop().time()
                    }, recipient_id, interview_id)
                else:
                    # Broadcast to all interview participants
                    await manager.broadcast_to_interview({
                        "type": "chat_message",
                        "sender_id": current_user.id,
                        "message": message_text,
                        "timestamp": asyncio.get_event_loop().time()
                    }, interview_id)

            elif message_type == "screen_share_start":
                # Handle screen sharing start
                await manager.broadcast_to_interview({
                    "type": "screen_share_started",
                    "user_id": current_user.id,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "screen_share_end":
                # Handle screen sharing end
                await manager.broadcast_to_interview({
                    "type": "screen_share_ended",
                    "user_id": current_user.id,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "typing_indicator":
                # Broadcast typing indicator
                await manager.broadcast_to_interview({
                    "type": "user_typing",
                    "user_id": current_user.id,
                    "is_typing": data.get("is_typing", False)
                }, interview_id, exclude_user=current_user.id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {current_user.id} in interview {interview_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {current_user.id} in interview {interview_id}: {e}")
    finally:
        manager.disconnect(current_user.id, interview_id)

@router.websocket("/live-interview/{interview_id}")
async def live_interview_websocket(
    websocket: WebSocket,
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    WebSocket endpoint for live interview sessions between recruiters and candidates.
    """
    # Verify interview access (different logic for live interviews)
    # This would need to check if user is a participant in the live interview
    interview_doc = await db.live_interviews.find_one({
        "_id": interview_id,
        "$or": [
            {"candidate_id": current_user.id},
            {"recruiter_id": current_user.id}
        ]
    })

    if not interview_doc:
        await websocket.close(code=1008, reason="Live interview not found or access denied")
        return

    await manager.connect(websocket, current_user.id, interview_id)

    try:
        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "join_interview":
                # Handle user joining live interview
                await manager.broadcast_to_interview({
                    "type": "user_joined",
                    "user_id": current_user.id,
                    "user_name": current_user.full_name,
                    "user_role": current_user.role.value,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "leave_interview":
                # Handle user leaving live interview
                await manager.broadcast_to_interview({
                    "type": "user_left",
                    "user_id": current_user.id,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "video_stream_ready":
                stream_id = data.get("stream_id")
                await manager.broadcast_to_interview({
                    "type": "video_stream_available",
                    "user_id": current_user.id,
                    "stream_id": stream_id,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "request_whiteboard":
                # Handle whiteboard sharing request
                await manager.broadcast_to_interview({
                    "type": "whiteboard_requested",
                    "user_id": current_user.id,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id)

            elif message_type == "share_whiteboard":
                whiteboard_data = data.get("whiteboard_data", {})
                await manager.broadcast_to_interview({
                    "type": "whiteboard_update",
                    "user_id": current_user.id,
                    "whiteboard_data": whiteboard_data,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "code_share":
                code_content = data.get("code", "")
                language = data.get("language", "text")
                await manager.broadcast_to_interview({
                    "type": "code_shared",
                    "user_id": current_user.id,
                    "code": code_content,
                    "language": language,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "file_share":
                file_info = data.get("file_info", {})
                await manager.broadcast_to_interview({
                    "type": "file_shared",
                    "user_id": current_user.id,
                    "file_info": file_info,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id, exclude_user=current_user.id)

            elif message_type == "interview_feedback":
                feedback_data = data.get("feedback", {})
                # Store feedback in database
                await db.live_interview_feedback.insert_one({
                    "interview_id": interview_id,
                    "from_user_id": current_user.id,
                    "to_user_id": data.get("to_user_id"),
                    "feedback": feedback_data,
                    "timestamp": asyncio.get_event_loop().time()
                })

                # Send private feedback if specified
                to_user_id = data.get("to_user_id")
                if to_user_id:
                    await manager.send_personal_message({
                        "type": "feedback_received",
                        "from_user_id": current_user.id,
                        "feedback": feedback_data,
                        "timestamp": asyncio.get_event_loop().time()
                    }, to_user_id, interview_id)

            elif message_type == "end_interview":
                # Handle interview ending
                await manager.broadcast_to_interview({
                    "type": "interview_ended",
                    "ended_by": current_user.id,
                    "timestamp": asyncio.get_event_loop().time()
                }, interview_id)

                # Update interview status in database
                await db.live_interviews.update_one(
                    {"_id": interview_id},
                    {
                        "$set": {
                            "status": "completed",
                            "ended_at": asyncio.get_event_loop().time(),
                            "ended_by": current_user.id
                        }
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"Live interview WebSocket disconnected for user {current_user.id} in interview {interview_id}")

        # Notify other participants
        await manager.broadcast_to_interview({
            "type": "user_left",
            "user_id": current_user.id,
            "timestamp": asyncio.get_event_loop().time()
        }, interview_id)

    except Exception as e:
        logger.error(f"Live interview WebSocket error for user {current_user.id} in interview {interview_id}: {e}")
    finally:
        manager.disconnect(current_user.id, interview_id)

@router.websocket("/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis)
):
    """
    WebSocket endpoint for real-time notifications.
    """
    await manager.connect(websocket, current_user.id, "notifications")

    try:
        # Subscribe to user-specific notification channel
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"notifications:{current_user.id}")

        async def listen_for_notifications():
            """Listen for notifications from Redis."""
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        notification_data = json.loads(message["data"])
                        await websocket.send_json({
                            "type": "notification",
                            "data": notification_data,
                            "timestamp": asyncio.get_event_loop().time()
                        })
            except Exception as e:
                logger.error(f"Notification listener error for user {current_user.id}: {e}")

        # Start listening task
        listen_task = asyncio.create_task(listen_for_notifications())

        # Handle WebSocket messages
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                })
            elif data.get("type") == "mark_read":
                notification_id = data.get("notification_id")
                # Mark notification as read in database
                await websocket.send_json({
                    "type": "notification_marked_read",
                    "notification_id": notification_id,
                    "timestamp": asyncio.get_event_loop().time()
                })

    except WebSocketDisconnect:
        logger.info(f"Notifications WebSocket disconnected for user {current_user.id}")
    except Exception as e:
        logger.error(f"Notifications WebSocket error for user {current_user.id}: {e}")
    finally:
        manager.disconnect(current_user.id, "notifications")

# Utility functions for sending notifications
async def send_notification_to_user(user_id: str, notification: Dict[str, Any], redis_client):
    """Send notification to specific user via Redis pub/sub."""
    try:
        await redis_client.publish(f"notifications:{user_id}", json.dumps(notification))
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")

async def broadcast_notification_to_interview(interview_id: str, notification: Dict[str, Any], redis_client, db):
    """Broadcast notification to all participants in an interview."""
    try:
        # Get interview participants
        interview_doc = await db.interviews.find_one({"_id": interview_id})
        if interview_doc:
            user_id = interview_doc.get("user_id")
            await send_notification_to_user(user_id, notification, redis_client)

        # For live interviews, get all participants
        live_interview_doc = await db.live_interviews.find_one({"_id": interview_id})
        if live_interview_doc:
            for participant_id in [live_interview_doc.get("candidate_id"), live_interview_doc.get("recruiter_id")]:
                if participant_id:
                    await send_notification_to_user(participant_id, notification, redis_client)

    except Exception as e:
        logger.error(f"Failed to broadcast notification for interview {interview_id}: {e}")

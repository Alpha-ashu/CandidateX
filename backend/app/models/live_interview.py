"""
Live interview models for real-time video/audio interviews.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class LiveInterviewStatus(str, Enum):
    """Live interview status enumeration."""
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    TECHNICAL_ISSUE = "technical_issue"

class LiveInterviewType(str, Enum):
    """Live interview type enumeration."""
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"
    MIXED = "mixed"

class ParticipantRole(str, Enum):
    """Participant role in live interview."""
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"

class InterviewRoom(BaseModel):
    """Interview room model for live sessions."""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    room_id: str = Field(..., unique=True, index=True)  # Unique room identifier
    live_interview_id: str = Field(..., index=True)

    # WebRTC configuration
    webrtc_config: Dict[str, Any] = Field(default_factory=dict)
    turn_servers: List[Dict[str, str]] = Field(default_factory=list)
    stun_servers: List[str] = Field(default_factory=list)

    # Room settings
    max_participants: int = Field(default=2)
    allow_screen_share: bool = Field(default=True)
    allow_file_share: bool = Field(default=True)
    recording_enabled: bool = Field(default=False)

    # Security
    room_password: Optional[str] = None
    access_tokens: Dict[str, str] = Field(default_factory=dict)  # user_id -> access_token

    # Status
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class LiveInterviewSession(BaseModel):
    """Live interview session model."""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    # Participants
    interviewer_id: str = Field(..., index=True)
    candidate_id: str = Field(..., index=True)
    interviewer_name: str
    candidate_name: str

    # Interview details
    job_title: str = Field(..., min_length=1, max_length=200)
    job_description: Optional[str] = Field(None, max_length=2000)
    company: Optional[str] = Field(None, max_length=100)
    experience_level: str = Field(default="mid")
    interview_type: LiveInterviewType = Field(default=LiveInterviewType.MIXED)

    # Scheduling
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=180)
    timezone: str = Field(default="UTC")

    # Status and progress
    status: LiveInterviewStatus = Field(default=LiveInterviewStatus.SCHEDULED)
    room_id: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    actual_duration: Optional[int] = None  # minutes

    # Interview content
    agenda: List[str] = Field(default_factory=list)
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[Dict[str, Any]] = Field(default_factory=list)

    # Recording and media
    recording_url: Optional[str] = None
    shared_files: List[Dict[str, Any]] = Field(default_factory=list)
    whiteboard_data: List[Dict[str, Any]] = Field(default_factory=list)

    # Feedback and evaluation
    interviewer_feedback: Optional[Dict[str, Any]] = None
    candidate_feedback: Optional[Dict[str, Any]] = None
    overall_rating: Optional[int] = Field(None, ge=1, le=5)

    # Technical issues
    technical_issues: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class InterviewParticipant(BaseModel):
    """Interview participant model."""
    user_id: str
    name: str
    email: str
    role: ParticipantRole
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    connection_quality: Optional[str] = None  # good, fair, poor
    device_info: Optional[Dict[str, Any]] = None

class InterviewMessage(BaseModel):
    """Chat message model for live interviews."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    interview_id: str
    sender_id: str
    sender_name: str
    message_type: str = Field(default="text")  # text, system, file, code
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class InterviewRecording(BaseModel):
    """Interview recording model."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    interview_id: str
    recording_type: str = Field(default="video")  # video, audio, screen
    file_url: str
    file_size: int
    duration: int  # seconds
    format: str
    quality: str = Field(default="high")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LiveInterviewCreate(BaseModel):
    """Live interview creation model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    candidate_id: str
    candidate_name: str
    job_title: str = Field(..., min_length=1, max_length=200)
    job_description: Optional[str] = Field(None, max_length=2000)
    company: Optional[str] = Field(None, max_length=100)
    experience_level: str = Field(default="mid")
    interview_type: LiveInterviewType = Field(default=LiveInterviewType.MIXED)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=180)
    timezone: str = Field(default="UTC")
    agenda: List[str] = Field(default_factory=list)

class LiveInterviewUpdate(BaseModel):
    """Live interview update model."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    job_description: Optional[str] = Field(None, max_length=2000)
    company: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[str] = None
    interview_type: Optional[LiveInterviewType] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    timezone: Optional[str] = None
    agenda: Optional[List[str]] = None
    status: Optional[LiveInterviewStatus] = None

class InterviewFeedback(BaseModel):
    """Interview feedback model."""
    overall_rating: int = Field(..., ge=1, le=5)
    communication_skills: int = Field(..., ge=1, le=5)
    technical_skills: int = Field(..., ge=1, le=5)
    problem_solving: int = Field(..., ge=1, le=5)
    cultural_fit: int = Field(..., ge=1, le=5)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    hiring_decision: str = Field(default="pending")  # pending, accept, reject, hold
    notes: Optional[str] = Field(None, max_length=2000)

class LiveInterviewResponse(BaseModel):
    """Live interview response model."""
    id: str
    title: str
    description: Optional[str]
    interviewer_id: str
    interviewer_name: str
    candidate_id: str
    candidate_name: str
    job_title: str
    job_description: Optional[str]
    company: Optional[str]
    experience_level: str
    interview_type: LiveInterviewType
    scheduled_at: datetime
    duration_minutes: int
    timezone: str
    status: LiveInterviewStatus
    room_id: Optional[str]
    agenda: List[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    actual_duration: Optional[int]
    overall_rating: Optional[int]
    created_at: datetime
    updated_at: datetime

class InterviewRoomResponse(BaseModel):
    """Interview room response model."""
    room_id: str
    webrtc_config: Dict[str, Any]
    turn_servers: List[Dict[str, str]]
    stun_servers: List[str]
    max_participants: int
    allow_screen_share: bool
    allow_file_share: bool
    recording_enabled: bool
    access_token: str
    expires_at: Optional[datetime]

class WebRTCIceCandidate(BaseModel):
    """WebRTC ICE candidate model."""
    candidate: str
    sdpMid: str
    sdpMLineIndex: int

class WebRTCSessionDescription(BaseModel):
    """WebRTC session description model."""
    type: str  # offer, answer
    sdp: str

class InterviewSignalingMessage(BaseModel):
    """WebRTC signaling message model."""
    type: str  # offer, answer, candidate, hangup
    from_user: str
    to_user: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

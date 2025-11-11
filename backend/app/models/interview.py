"""
Interview models for MongoDB.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class InterviewType(str, Enum):
    """Interview type enumeration."""
    MOCK = "mock"
    LIVE = "live"
    AI_MOCK = "ai_mock"

class InterviewMode(str, Enum):
    """Interview mode enumeration."""
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    MIXED = "mixed"

class InterviewStatus(str, Enum):
    """Interview status enumeration."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class QuestionType(str, Enum):
    """Question type enumeration."""
    TEXT = "text"
    MULTIPLE_CHOICE = "multiple_choice"
    CODING = "coding"

class InterviewSession(BaseModel):
    """Interview session model."""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str = Field(..., index=True)
    type: InterviewType = Field(default=InterviewType.MOCK)
    mode: InterviewMode = Field(default=InterviewMode.MIXED)
    status: InterviewStatus = Field(default=InterviewStatus.CREATED)

    # Configuration
    job_title: str
    job_description: Optional[str] = None
    company: Optional[str] = None
    experience_level: str = Field(default="mid")  # entry, mid, senior
    question_count: int = Field(default=10, ge=5, le=20)
    time_limit_per_question: int = Field(default=300, ge=60, le=600)  # seconds

    # Questions and responses
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    responses: List[Dict[str, Any]] = Field(default_factory=list)

    # AI-generated content
    ai_feedback: Optional[Dict[str, Any]] = None
    overall_score: Optional[float] = Field(None, ge=0, le=100)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration: Optional[int] = None  # seconds

    # Anti-cheat data
    anti_cheat_events: List[Dict[str, Any]] = Field(default_factory=list)
    flagged_for_review: bool = Field(default=False)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class InterviewQuestion(BaseModel):
    """Interview question model."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    session_id: str
    question_number: int
    type: QuestionType = Field(default=QuestionType.TEXT)
    question_text: str
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: Optional[str] = None  # For multiple choice
    time_limit: int  # seconds
    category: str  # behavioral, technical, etc.

    # AI metadata
    ai_generated: bool = Field(default=True)
    difficulty_level: str = Field(default="medium")  # easy, medium, hard
    skills_assessed: List[str] = Field(default_factory=list)

class InterviewResponse(BaseModel):
    """Interview response model."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    session_id: str
    question_id: str
    response_text: Optional[str] = None
    response_audio_url: Optional[str] = None
    response_video_url: Optional[str] = None
    selected_option: Optional[str] = None  # For multiple choice

    # Timing
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_spent: Optional[int] = None  # seconds

    # AI evaluation
    ai_score: Optional[float] = Field(None, ge=0, le=10)
    ai_feedback: Optional[str] = None
    strengths: Optional[List[str]] = Field(default_factory=list)
    improvements: Optional[List[str]] = Field(default_factory=list)

class InterviewFeedback(BaseModel):
    """Interview feedback model."""
    session_id: str
    overall_score: float = Field(..., ge=0, le=100)
    overall_feedback: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Detailed scores
    communication_score: Optional[float] = Field(None, ge=0, le=10)
    technical_score: Optional[float] = Field(None, ge=0, le=10)
    problem_solving_score: Optional[float] = Field(None, ge=0, le=10)
    behavioral_score: Optional[float] = Field(None, ge=0, le=10)

    # Benchmarking
    percentile_rank: Optional[float] = Field(None, ge=0, le=100)
    industry_average: Optional[float] = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)

class InterviewCreate(BaseModel):
    """Interview creation model."""
    type: InterviewType = Field(default=InterviewType.MOCK)
    mode: InterviewMode = Field(default=InterviewMode.MIXED)
    job_title: str = Field(..., min_length=1, max_length=200)
    job_description: Optional[str] = Field(None, max_length=2000)
    company: Optional[str] = Field(None, max_length=100)
    experience_level: str = Field(default="mid")
    question_count: int = Field(default=10, ge=5, le=20)
    time_limit_per_question: int = Field(default=300, ge=60, le=600)

class InterviewUpdate(BaseModel):
    """Interview update model."""
    status: Optional[InterviewStatus] = None
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    job_description: Optional[str] = Field(None, max_length=2000)
    company: Optional[str] = Field(None, max_length=100)

class InterviewSessionResponse(BaseModel):
    """Interview session response model."""
    id: str
    user_id: str
    type: InterviewType
    mode: InterviewMode
    status: InterviewStatus
    job_title: str
    job_description: Optional[str]
    company: Optional[str]
    experience_level: str
    question_count: int
    time_limit_per_question: int
    questions: List[Dict[str, Any]]
    current_question_index: int = 0
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_duration: Optional[int]
    ai_feedback: Optional[Dict[str, Any]]
    overall_score: Optional[float]
    created_at: datetime
    updated_at: datetime

class InterviewSummary(BaseModel):
    """Interview summary model."""
    id: str
    job_title: str
    type: InterviewType
    mode: InterviewMode
    status: InterviewStatus
    overall_score: Optional[float]
    question_count: int
    completed_questions: int
    total_duration: Optional[int]
    completed_at: Optional[datetime]
    ai_feedback: Optional[Dict[str, Any]]

class InterviewAnalytics(BaseModel):
    """Interview analytics model."""
    total_interviews: int
    completed_interviews: int
    average_score: Optional[float]
    average_duration: Optional[int]
    interviews_by_type: Dict[str, int]
    interviews_by_mode: Dict[str, int]
    score_distribution: Dict[str, int]
    recent_interviews: List[InterviewSummary]

class AntiCheatEvent(BaseModel):
    """Anti-cheat event model."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    session_id: str
    user_id: str
    event_type: str  # tab_switch, face_not_detected, etc.
    severity: str = Field(default="low")  # low, medium, high
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

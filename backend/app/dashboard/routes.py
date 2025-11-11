"""
Dashboard routes for analytics, reporting, and user insights.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import User, UserRole
from app.models.interview import InterviewSession, InterviewStatus, InterviewType, InterviewMode
from app.models import get_database, get_redis
from app.auth.dependencies import get_current_user, check_permissions

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/candidate/overview")
async def get_candidate_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get candidate dashboard overview.
    """
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get interview statistics
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": None,
            "total_interviews": {"$sum": 1},
            "completed_interviews": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "in_progress_interviews": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
            "average_score": {"$avg": {"$cond": [{"$ne": ["$overall_score", None]}, "$overall_score", None]}},
            "total_time_spent": {"$sum": {"$ifNull": ["$total_duration", 0]}}
        }}
    ]

    stats_result = await db.interviews.aggregate(pipeline).to_list(length=1)
    stats = stats_result[0] if stats_result else {
        "total_interviews": 0,
        "completed_interviews": 0,
        "in_progress_interviews": 0,
        "average_score": None,
        "total_time_spent": 0
    }

    # Get recent interviews
    recent_interviews_cursor = db.interviews.find({"user_id": current_user.id}).sort("created_at", -1).limit(5)
    recent_interviews_docs = await recent_interviews_cursor.to_list(length=None)

    recent_interviews = []
    for doc in recent_interviews_docs:
        interview = InterviewSession(**doc)
        recent_interviews.append({
            "id": interview.id,
            "job_title": interview.job_title,
            "status": interview.status.value,
            "overall_score": interview.overall_score,
            "completed_at": interview.completed_at,
            "created_at": interview.created_at
        })

    # Get skill progress (mock data for now)
    skill_progress = {
        "communication": {"current": 7.2, "target": 8.0, "trend": "improving"},
        "technical": {"current": 6.8, "target": 8.0, "trend": "improving"},
        "problem_solving": {"current": 7.5, "target": 8.0, "trend": "stable"},
        "behavioral": {"current": 8.1, "target": 8.5, "trend": "improving"}
    }

    # Get upcoming events (mock data)
    upcoming_events = [
        {
            "id": "event_1",
            "title": "Mock Interview Workshop",
            "date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "type": "workshop"
        },
        {
            "id": "event_2",
            "title": "Career Networking Event",
            "date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "type": "networking"
        }
    ]

    return {
        "stats": stats,
        "recent_interviews": recent_interviews,
        "skill_progress": skill_progress,
        "upcoming_events": upcoming_events,
        "notifications": []  # TODO: Implement notifications
    }

@router.get("/candidate/analytics")
async def get_candidate_analytics(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed candidate analytics.
    """
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Calculate date range
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get interviews in period
    interviews_cursor = db.interviews.find({
        "user_id": current_user.id,
        "created_at": {"$gte": start_date}
    }).sort("created_at", 1)

    interviews_docs = await interviews_cursor.to_list(length=None)
    interviews = [InterviewSession(**doc) for doc in interviews_docs]

    # Calculate analytics
    completed_interviews = [i for i in interviews if i.status == InterviewStatus.COMPLETED]
    scores = [i.overall_score for i in completed_interviews if i.overall_score is not None]

    analytics = {
        "period": period,
        "total_interviews": len(interviews),
        "completed_interviews": len(completed_interviews),
        "completion_rate": (len(completed_interviews) / len(interviews)) * 100 if interviews else 0,
        "average_score": sum(scores) / len(scores) if scores else None,
        "score_trend": calculate_score_trend(completed_interviews),
        "time_spent_trend": calculate_time_trend(completed_interviews),
        "question_type_performance": calculate_question_performance(completed_interviews),
        "improvement_areas": identify_improvement_areas(completed_interviews)
    }

    return analytics

@router.get("/recruiter/overview")
async def get_recruiter_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get recruiter dashboard overview.
    """
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get interview statistics for interviews created by recruiter
    # Note: This assumes recruiters can create interviews for candidates
    pipeline = [
        {"$match": {"created_by": current_user.id}},
        {"$group": {
            "_id": None,
            "total_interviews": {"$sum": 1},
            "completed_interviews": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "average_candidate_score": {"$avg": {"$cond": [{"$ne": ["$overall_score", None]}, "$overall_score", None]}},
            "total_candidates": {"$addToSet": "$user_id"}
        }}
    ]

    stats_result = await db.interviews.aggregate(pipeline).to_list(length=1)
    stats = stats_result[0] if stats_result else {
        "total_interviews": 0,
        "completed_interviews": 0,
        "average_candidate_score": None,
        "total_candidates": []
    }

    stats["total_candidates"] = len(stats["total_candidates"]) if stats_result else 0

    # Get recent candidate interviews
    recent_interviews_cursor = db.interviews.find({"created_by": current_user.id}).sort("created_at", -1).limit(10)
    recent_interviews_docs = await recent_interviews_cursor.to_list(length=None)

    recent_candidates = []
    for doc in recent_interviews_docs:
        interview = InterviewSession(**doc)
        # Get candidate info
        candidate_doc = await db.users.find_one({"_id": interview.user_id})
        candidate_name = candidate_doc.get("full_name", "Unknown") if candidate_doc else "Unknown"

        recent_candidates.append({
            "id": interview.id,
            "candidate_name": candidate_name,
            "job_title": interview.job_title,
            "status": interview.status.value,
            "score": interview.overall_score,
            "completed_at": interview.completed_at
        })

    # Get hiring pipeline metrics (mock data)
    pipeline_metrics = {
        "applied": 45,
        "screened": 32,
        "interviewed": 18,
        "offered": 5,
        "hired": 3
    }

    # Get top performing candidates
    top_candidates = await get_top_performing_candidates(current_user.id, db)

    return {
        "stats": stats,
        "recent_candidates": recent_candidates,
        "pipeline_metrics": pipeline_metrics,
        "top_candidates": top_candidates,
        "scheduled_interviews": []  # TODO: Implement scheduling
    }

@router.get("/recruiter/analytics")
async def get_recruiter_analytics(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed recruiter analytics.
    """
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Calculate date range
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get interviews created by recruiter
    interviews_cursor = db.interviews.find({
        "created_by": current_user.id,
        "created_at": {"$gte": start_date}
    })

    interviews_docs = await interviews_cursor.to_list(length=None)
    interviews = [InterviewSession(**doc) for doc in interviews_docs]

    # Calculate analytics
    completed_interviews = [i for i in interviews if i.status == InterviewStatus.COMPLETED]

    analytics = {
        "period": period,
        "total_interviews_conducted": len(interviews),
        "completed_interviews": len(completed_interviews),
        "completion_rate": (len(completed_interviews) / len(interviews)) * 100 if interviews else 0,
        "average_candidate_score": calculate_average_score(completed_interviews),
        "score_distribution": calculate_score_distribution(completed_interviews),
        "popular_job_titles": calculate_popular_jobs(interviews),
        "interview_duration_trends": calculate_duration_trends(completed_interviews),
        "candidate_feedback_summary": summarize_candidate_feedback(completed_interviews)
    }

    return analytics

@router.get("/admin/overview")
async def get_admin_dashboard(
    current_user: User = Depends(check_permissions(["read_all_analytics"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get admin dashboard overview.
    """
    # Get system-wide statistics
    user_stats = await db.users.aggregate([
        {"$group": {
            "_id": None,
            "total_users": {"$sum": 1},
            "active_users": {"$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}},
            "new_users_30d": {"$sum": {"$cond": [{"$gte": ["$created_at", datetime.utcnow() - timedelta(days=30)]}, 1, 0]}}
        }}
    ]).to_list(length=1)

    interview_stats = await db.interviews.aggregate([
        {"$group": {
            "_id": None,
            "total_interviews": {"$sum": 1},
            "completed_interviews": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "average_score": {"$avg": {"$cond": [{"$ne": ["$overall_score", None]}, "$overall_score", None]}}
        }}
    ]).to_list(length=1)

    system_stats = {
        "users": user_stats[0] if user_stats else {"total_users": 0, "active_users": 0, "new_users_30d": 0},
        "interviews": interview_stats[0] if interview_stats else {"total_interviews": 0, "completed_interviews": 0, "average_score": None}
    }

    # Get recent activity
    recent_activity = await get_recent_system_activity(db)

    # Get system health metrics (mock data)
    system_health = {
        "api_response_time": 245,  # ms
        "error_rate": 0.02,  # 2%
        "uptime": 99.8,  # %
        "database_connections": 12
    }

    # Get revenue metrics (mock data)
    revenue_metrics = {
        "monthly_revenue": 12500,
        "subscription_growth": 15.3,  # %
        "churn_rate": 2.1,  # %
        "lifetime_value": 450
    }

    return {
        "system_stats": system_stats,
        "recent_activity": recent_activity,
        "system_health": system_health,
        "revenue_metrics": revenue_metrics,
        "alerts": []  # TODO: Implement system alerts
    }

@router.get("/admin/analytics")
async def get_admin_analytics(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(check_permissions(["read_all_analytics"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed admin analytics.
    """
    # Calculate date range
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get comprehensive analytics
    analytics = {
        "period": period,
        "user_growth": await calculate_user_growth(start_date, db),
        "interview_trends": await calculate_interview_trends(start_date, db),
        "engagement_metrics": await calculate_engagement_metrics(start_date, db),
        "performance_metrics": await calculate_performance_metrics(start_date, db),
        "geographic_distribution": await calculate_geographic_distribution(db),
        "feature_usage": await calculate_feature_usage(start_date, db)
    }

    return analytics

# Helper functions
def calculate_score_trend(interviews: List[InterviewSession]) -> List[Dict[str, Any]]:
    """Calculate score trend over time."""
    if not interviews:
        return []

    # Sort by completion date
    sorted_interviews = sorted(interviews, key=lambda x: x.completed_at or x.created_at)

    trend = []
    for interview in sorted_interviews:
        if interview.overall_score is not None:
            trend.append({
                "date": (interview.completed_at or interview.created_at).isoformat(),
                "score": interview.overall_score
            })

    return trend

def calculate_time_trend(interviews: List[InterviewSession]) -> List[Dict[str, Any]]:
    """Calculate time spent trend."""
    if not interviews:
        return []

    sorted_interviews = sorted(interviews, key=lambda x: x.completed_at or x.created_at)

    trend = []
    for interview in sorted_interviews:
        if interview.total_duration:
            trend.append({
                "date": (interview.completed_at or interview.created_at).isoformat(),
                "duration": interview.total_duration
            })

    return trend

def calculate_question_performance(interviews: List[InterviewSession]) -> Dict[str, Any]:
    """Calculate performance by question type."""
    # Mock implementation
    return {
        "behavioral": {"average_score": 8.2, "count": 45},
        "technical": {"average_score": 7.1, "count": 38},
        "mixed": {"average_score": 7.8, "count": 29}
    }

def identify_improvement_areas(interviews: List[InterviewSession]) -> List[str]:
    """Identify areas for improvement."""
    # Mock implementation
    return [
        "Technical question responses could be more detailed",
        "Consider practicing time management",
        "Focus on STAR method for behavioral questions"
    ]

async def get_top_performing_candidates(recruiter_id: str, db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    """Get top performing candidates for recruiter."""
    # Mock implementation
    return [
        {"name": "John Doe", "score": 92, "job_title": "Software Engineer"},
        {"name": "Jane Smith", "score": 89, "job_title": "Product Manager"},
        {"name": "Bob Johnson", "score": 87, "job_title": "Data Scientist"}
    ]

def calculate_average_score(interviews: List[InterviewSession]) -> Optional[float]:
    """Calculate average score."""
    scores = [i.overall_score for i in interviews if i.overall_score is not None]
    return sum(scores) / len(scores) if scores else None

def calculate_score_distribution(interviews: List[InterviewSession]) -> Dict[str, int]:
    """Calculate score distribution."""
    distribution = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "0-59": 0}

    for interview in interviews:
        if interview.overall_score is not None:
            if interview.overall_score >= 90:
                distribution["90-100"] += 1
            elif interview.overall_score >= 80:
                distribution["80-89"] += 1
            elif interview.overall_score >= 70:
                distribution["70-79"] += 1
            elif interview.overall_score >= 60:
                distribution["60-69"] += 1
            else:
                distribution["0-59"] += 1

    return distribution

def calculate_popular_jobs(interviews: List[InterviewSession]) -> List[Dict[str, Any]]:
    """Calculate popular job titles."""
    job_counts = {}
    for interview in interviews:
        job_counts[interview.job_title] = job_counts.get(interview.job_title, 0) + 1

    return [
        {"job_title": job, "count": count}
        for job, count in sorted(job_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

def calculate_duration_trends(interviews: List[InterviewSession]) -> List[Dict[str, Any]]:
    """Calculate interview duration trends."""
    # Mock implementation
    return [
        {"date": "2025-01-01", "average_duration": 1800},
        {"date": "2025-01-02", "average_duration": 1950},
        {"date": "2025-01-03", "average_duration": 1750}
    ]

def summarize_candidate_feedback(interviews: List[InterviewSession]) -> Dict[str, Any]:
    """Summarize candidate feedback."""
    # Mock implementation
    return {
        "average_rating": 4.2,
        "common_feedback": [
            "Helpful preparation tool",
            "Good AI feedback",
            "Realistic interview experience"
        ],
        "suggested_improvements": [
            "More question variety",
            "Better mobile experience"
        ]
    }

async def get_recent_system_activity(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    """Get recent system activity."""
    # Mock implementation
    return [
        {"type": "user_registered", "description": "New user registered", "timestamp": datetime.utcnow().isoformat()},
        {"type": "interview_completed", "description": "Interview completed", "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat()},
        {"type": "admin_action", "description": "User account updated", "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat()}
    ]

async def calculate_user_growth(start_date: datetime, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Calculate user growth metrics."""
    # Mock implementation
    return {
        "new_users": 1250,
        "growth_rate": 15.3,
        "retention_rate": 87.2,
        "churn_rate": 2.1
    }

async def calculate_interview_trends(start_date: datetime, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Calculate interview trends."""
    # Mock implementation
    return {
        "total_interviews": 5420,
        "completion_rate": 78.5,
        "average_score": 76.8,
        "popular_categories": ["Software Engineering", "Product Management", "Data Science"]
    }

async def calculate_engagement_metrics(start_date: datetime, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Calculate engagement metrics."""
    # Mock implementation
    return {
        "daily_active_users": 1250,
        "session_duration": 1800,  # seconds
        "feature_usage": {
            "mock_interviews": 85,
            "resume_analysis": 62,
            "skill_assessment": 43
        }
    }

async def calculate_performance_metrics(start_date: datetime, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Calculate performance metrics."""
    # Mock implementation
    return {
        "api_response_time": 245,  # ms
        "error_rate": 0.02,  # 2%
        "uptime": 99.8,  # %
        "throughput": 1250  # requests/minute
    }

async def calculate_geographic_distribution(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Calculate geographic distribution."""
    # Mock implementation
    return {
        "top_countries": [
            {"country": "United States", "users": 4520},
            {"country": "India", "users": 3210},
            {"country": "United Kingdom", "users": 1890}
        ],
        "top_cities": [
            {"city": "New York", "users": 890},
            {"city": "London", "users": 650},
            {"city": "Mumbai", "users": 580}
        ]
    }

async def calculate_feature_usage(start_date: datetime, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Calculate feature usage statistics."""
    # Mock implementation
    return {
        "mock_interviews": {"usage": 85, "growth": 12.5},
        "live_interviews": {"usage": 15, "growth": 8.3},
        "resume_analysis": {"usage": 62, "growth": 15.7},
        "skill_assessment": {"usage": 43, "growth": 22.1},
        "community_features": {"usage": 28, "growth": 35.2}
    }

"""
Admin routes for system administration and management.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import User, UserRole, UserStatus
from app.models.interview import InterviewSession, InterviewStatus
from app.models import get_database, get_redis
from app.auth.dependencies import check_permissions
from app.config import settings
from app.utils.database import db_manager, reset_database, delete_user_data, create_test_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/system/health")
async def get_system_health(
    current_user: User = Depends(check_permissions(["configure_system"])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Get system health status.
    """
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check MongoDB
    try:
        await db.command("ping")
        health_status["services"]["mongodb"] = {"status": "healthy", "response_time": 10}
    except Exception as e:
        health_status["services"]["mongodb"] = {"status": "unhealthy", "error": str(e)}

    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = {"status": "healthy", "response_time": 5}
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Check AI services (mock)
    health_status["services"]["ai_service"] = {"status": "healthy", "response_time": 150}

    # Overall status
    all_healthy = all(service["status"] == "healthy" for service in health_status["services"].values())
    health_status["overall_status"] = "healthy" if all_healthy else "degraded"

    return health_status

@router.get("/system/metrics")
async def get_system_metrics(
    period: str = Query("1h", pattern="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(check_permissions(["configure_system"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get system performance metrics.
    """
    # Calculate time range
    hours = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}[period]
    start_time = datetime.utcnow() - timedelta(hours=hours)

    # Mock metrics - in real implementation, these would come from monitoring systems
    metrics = {
        "period": period,
        "api_metrics": {
            "total_requests": 125430,
            "average_response_time": 245,  # ms
            "error_rate": 0.02,  # 2%
            "requests_per_second": 35.2
        },
        "database_metrics": {
            "connection_count": 12,
            "query_count": 89234,
            "average_query_time": 15,  # ms
            "cache_hit_rate": 87.5  # %
        },
        "user_metrics": {
            "active_users": 1250,
            "new_registrations": 45,
            "login_attempts": 2150,
            "failed_logins": 12
        },
        "interview_metrics": {
            "total_interviews": 5420,
            "completed_interviews": 4230,
            "average_duration": 1800,  # seconds
            "ai_processing_time": 120  # seconds
        }
    }

    return metrics

@router.get("/audit/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(check_permissions(["audit_logs"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get audit logs for system activities.
    """
    # Build query
    query = {}
    if action:
        query["action"] = action
    if user_id:
        query["user_id"] = user_id
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["timestamp"] = date_query

    # Get audit logs (assuming audit_logs collection exists)
    try:
        cursor = db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=None)

        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": str(log["_id"]),
                "timestamp": log["timestamp"].isoformat(),
                "user_id": log.get("user_id"),
                "action": log.get("action"),
                "resource": log.get("resource"),
                "details": log.get("details", {}),
                "ip_address": log.get("ip_address"),
                "user_agent": log.get("user_agent")
            })

        return {
            "logs": formatted_logs,
            "total": len(formatted_logs),  # In real implementation, use count_documents
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        # If audit_logs collection doesn't exist, return empty result
        logger.warning(f"Audit logs not available: {e}")
        return {
            "logs": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "message": "Audit logging not configured"
        }

@router.post("/system/maintenance")
async def trigger_maintenance(
    maintenance_type: str = Query(..., pattern="^(cache_clear|db_optimize|logs_rotate)$"),
    current_user: User = Depends(check_permissions(["configure_system"])),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    redis_client = Depends(get_redis)
):
    """
    Trigger system maintenance operations.
    """
    if maintenance_type == "cache_clear":
        # Clear Redis cache
        await redis_client.flushdb()
        message = "Cache cleared successfully"

    elif maintenance_type == "db_optimize":
        # Trigger database optimization (background task)
        background_tasks.add_task(optimize_database)
        message = "Database optimization started"

    elif maintenance_type == "logs_rotate":
        # Rotate application logs (background task)
        background_tasks.add_task(rotate_logs)
        message = "Log rotation started"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid maintenance type"
        )

    logger.info(f"Maintenance triggered by {current_user.email}: {maintenance_type}")

    return {"message": message}

@router.get("/config")
async def get_system_config(
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """
    Get system configuration (sensitive data masked).
    """
    config = {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG
        },
        "database": {
            "mongodb_url": mask_sensitive(settings.MONGODB_URL),
            "database_name": settings.MONGODB_DATABASE
        },
        "redis": {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB
        },
        "ai_services": {
            "google_ai_enabled": bool(settings.GOOGLE_AI_API_KEY),
            "openai_enabled": bool(settings.OPENAI_API_KEY),
            "model": settings.AI_MODEL
        },
        "email": {
            "smtp_server": settings.SMTP_SERVER,
            "smtp_port": settings.SMTP_PORT,
            "from_email": settings.EMAIL_FROM,
            "enabled": bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
        },
        "security": {
            "jwt_expiration": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "bcrypt_rounds": settings.BCRYPT_ROUNDS,
            "account_lockout_attempts": settings.ACCOUNT_LOCKOUT_ATTEMPTS
        },
        "limits": {
            "max_upload_size": settings.MAX_UPLOAD_SIZE,
            "max_questions_per_interview": settings.MAX_QUESTIONS_PER_INTERVIEW,
            "default_question_time_limit": settings.DEFAULT_QUESTION_TIME_LIMIT
        }
    }

    return config

@router.put("/config/{config_key}")
async def update_system_config(
    config_key: str,
    value: Any,
    current_user: User = Depends(check_permissions(["configure_system"])),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Update system configuration (limited to safe configurations).
    """
    # Define allowed configuration updates
    allowed_configs = {
        "debug": bool,
        "max_questions_per_interview": int,
        "default_question_time_limit": int,
        "account_lockout_attempts": int,
        "account_lockout_duration_minutes": int
    }

    if config_key not in allowed_configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration key '{config_key}' cannot be updated via API"
        )

    # Validate value type
    expected_type = allowed_configs[config_key]
    if not isinstance(value, expected_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value type for '{config_key}'. Expected {expected_type.__name__}"
        )

    # Update configuration (in real implementation, this would update a config file or database)
    # For now, just log the change
    logger.info(f"Configuration updated by {current_user.email}: {config_key} = {value}")

    # In a real implementation, you might:
    # - Update environment variables
    # - Write to configuration file
    # - Update database settings
    # - Restart services if necessary

    return {
        "message": f"Configuration '{config_key}' updated successfully",
        "new_value": value
    }

@router.get("/reports/user-activity")
async def get_user_activity_report(
    start_date: datetime,
    end_date: datetime,
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
    current_user: User = Depends(check_permissions(["read_all_analytics"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate user activity report.
    """
    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    if (end_date - start_date).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 1 year"
        )

    # Mock report data - in real implementation, aggregate from audit logs and user activity
    report = {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by
        },
        "summary": {
            "total_users": 1250,
            "active_users": 890,
            "new_registrations": 145,
            "total_sessions": 5420
        },
        "activity_trends": generate_activity_trends(start_date, end_date, group_by),
        "top_features": [
            {"feature": "mock_interviews", "usage_count": 3420, "unique_users": 890},
            {"feature": "resume_analysis", "usage_count": 2150, "unique_users": 650},
            {"feature": "skill_assessment", "usage_count": 1890, "unique_users": 580}
        ],
        "user_engagement": {
            "highly_engaged": 320,  # users with >10 sessions
            "moderately_engaged": 450,  # users with 5-10 sessions
            "low_engagement": 480  # users with <5 sessions
        }
    }

    return report

@router.get("/reports/interview-performance")
async def get_interview_performance_report(
    start_date: datetime,
    end_date: datetime,
    current_user: User = Depends(check_permissions(["read_all_analytics"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate interview performance report.
    """
    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    # Mock report data
    report = {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "total_interviews": 5420,
            "completed_interviews": 4230,
            "completion_rate": 78.0,
            "average_score": 76.8,
            "average_duration": 1800  # seconds
        },
        "score_distribution": {
            "90-100": 890,
            "80-89": 1240,
            "70-79": 1320,
            "60-69": 680,
            "0-59": 100
        },
        "popular_job_titles": [
            {"title": "Software Engineer", "count": 1250},
            {"title": "Product Manager", "count": 890},
            {"title": "Data Scientist", "count": 650},
            {"title": "UX Designer", "count": 420}
        ],
        "performance_trends": {
            "score_trend": generate_score_trends(start_date, end_date),
            "completion_trend": generate_completion_trends(start_date, end_date)
        },
        "ai_feedback_summary": {
            "common_strengths": ["Communication skills", "Technical knowledge"],
            "common_weaknesses": ["Time management", "Specific examples"],
            "average_ai_processing_time": 120  # seconds
        }
    }

    return report

@router.post("/backup")
async def trigger_backup(
    backup_type: str = Query("full", pattern="^(full|incremental|config)$"),
    current_user: User = Depends(check_permissions(["configure_system"])),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Trigger system backup.
    """
    # In real implementation, this would trigger actual backup processes
    background_tasks.add_task(perform_backup, backup_type)

    logger.info(f"Backup triggered by {current_user.email}: {backup_type}")

    return {
        "message": f"{backup_type.capitalize()} backup started",
        "backup_type": backup_type,
        "started_at": datetime.utcnow().isoformat()
    }

# Helper functions
def mask_sensitive(value: str) -> str:
    """Mask sensitive information in configuration."""
    if "://" in value:
        # Mask database URLs
        parts = value.split("://")
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1]
            if "@" in rest:
                # Has credentials
                credentials_end = rest.find("@")
                masked = rest[:credentials_end].replace(".", "*").replace(":", "*")
                return f"{protocol}://{masked}@{rest[credentials_end+1:]}"
    return value

async def optimize_database():
    """Perform database optimization."""
    # Mock implementation
    logger.info("Database optimization completed")

async def rotate_logs():
    """Rotate application logs."""
    # Mock implementation
    logger.info("Log rotation completed")

def generate_activity_trends(start_date: datetime, end_date: datetime, group_by: str) -> List[Dict[str, Any]]:
    """Generate mock activity trends."""
    # Mock data
    trends = []
    current = start_date
    while current <= end_date:
        trends.append({
            "period": current.isoformat(),
            "active_users": 125 + (current.day % 10) * 10,
            "new_registrations": 5 + (current.day % 5),
            "total_sessions": 200 + (current.day % 20) * 15
        })

        if group_by == "hour":
            current += timedelta(hours=1)
        elif group_by == "day":
            current += timedelta(days=1)
        elif group_by == "week":
            current += timedelta(weeks=1)
        else:  # month
            current = current.replace(day=1, month=current.month + 1) if current.month < 12 else current.replace(day=1, month=1, year=current.year + 1)

    return trends

def generate_score_trends(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Generate mock score trends."""
    trends = []
    current = start_date
    base_score = 75.0

    while current <= end_date:
        trends.append({
            "date": current.isoformat(),
            "average_score": base_score + (current.day % 10) - 5,
            "total_interviews": 50 + (current.day % 20)
        })
        current += timedelta(days=1)

    return trends

def generate_completion_trends(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Generate mock completion trends."""
    trends = []
    current = start_date

    while current <= end_date:
        trends.append({
            "date": current.isoformat(),
            "completion_rate": 75.0 + (current.day % 10),
            "total_started": 60 + (current.day % 15),
            "total_completed": 45 + (current.day % 12)
        })
        current += timedelta(days=1)

    return trends

async def perform_backup(backup_type: str):
    """Perform system backup."""
    # Mock implementation
    logger.info(f"{backup_type.capitalize()} backup completed")

# Database management endpoints
@router.get("/database/stats")
async def get_database_stats(
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """Get database statistics."""
    try:
        stats = await db_manager.get_database_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve database statistics"
        )

@router.post("/database/reset-user-data/{user_id}")
async def reset_user_data(
    user_id: str,
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """Reset user data while preserving authentication info."""
    try:
        await db_manager.reset_user_data(user_id)
        logger.info(f"User data reset for {user_id} by {current_user.email}")
        return {"message": f"User data reset successfully for user {user_id}"}
    except Exception as e:
        logger.error(f"Failed to reset user data for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset user data"
        )

@router.delete("/database/user-data/{user_id}")
async def delete_user_database_data(
    user_id: str,
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """Delete user data (admin only)."""
    try:
        success = await delete_user_data(user_id, current_user.role)
        if success:
            logger.info(f"User data deleted for {user_id} by {current_user.email}")
            return {"message": f"User data deleted successfully for user {user_id}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete user data"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user data for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user data"
        )

@router.post("/database/backup")
async def create_database_backup(
    backup_name: str = Query(..., min_length=1, max_length=100),
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """Create database backup."""
    try:
        backup_metadata = await db_manager.backup_database(backup_name)
        logger.info(f"Database backup created: {backup_name} by {current_user.email}")
        return {
            "message": "Database backup created successfully",
            "backup": backup_metadata
        }
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create database backup"
        )

@router.post("/database/reset")
async def reset_entire_database(
    confirm: bool = Query(False, description="Must be true to confirm database reset"),
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """Reset entire database to initial state (DANGER: This deletes all data!)."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required. Set confirm=true to proceed with database reset."
        )

    try:
        await reset_database()
        logger.warning(f"Database reset performed by {current_user.email}")
        return {"message": "Database reset completed successfully"}
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset database"
        )

@router.post("/database/create-test-user")
async def create_test_user_endpoint(
    email: str = Query(..., description="User email"),
    full_name: str = Query(..., description="User full name"),
    role: UserRole = Query(UserRole.CANDIDATE, description="User role"),
    current_user: User = Depends(check_permissions(["configure_system"]))
):
    """Create a test user for development/testing."""
    try:
        user_id = await create_test_user(email, full_name, role)
        logger.info(f"Test user created: {email} by {current_user.email}")
        return {
            "message": "Test user created successfully",
            "user_id": user_id,
            "email": email,
            "role": role.value
        }
    except Exception as e:
        logger.error(f"Failed to create test user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test user"
        )

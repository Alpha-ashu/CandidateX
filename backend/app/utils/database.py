"""
Database utilities and initialization for CandidateX.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis

from app.config import settings
from app.auth.utils import get_password_hash
from app.models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for initialization and utilities."""

    def __init__(self):
        self.db_client: Optional[AsyncIOMotorClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to database services."""
        try:
            # Connect to MongoDB
            self.db_client = AsyncIOMotorClient(settings.MONGODB_URL)
            await self.db_client.admin.command('ping')
            self.database = self.db_client[settings.MONGODB_DATABASE]
            logger.info("Connected to MongoDB")

            # Connect to Redis (optional)
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Connected to Redis")
            except Exception as redis_error:
                logger.warning(f"Failed to connect to Redis: {redis_error}")
                self.redis_client = None

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Disconnect from database services."""
        if self.db_client:
            self.db_client.close()
        if self.redis_client:
            await self.redis_client.close()

    async def initialize_database(self):
        """Initialize database with default data and indexes."""
        if self.database is None:
            raise Exception("Database not connected")

        logger.info("Initializing database...")

        # Create indexes
        await self._create_indexes()

        # Create default users
        await self._create_default_users()

        # Create default data
        await self._create_default_data()

        logger.info("Database initialization completed")

    async def _create_indexes(self):
        """Create database indexes for performance."""
        logger.info("Creating database indexes...")

        # User indexes
        await self.database.users.create_index("email", unique=True)
        await self.database.users.create_index("role")
        await self.database.users.create_index("status")
        await self.database.users.create_index("created_at")
        await self.database.users.create_index("updated_at")

        # Interview indexes
        await self.database.interviews.create_index("user_id")
        await self.database.interviews.create_index("created_by")
        await self.database.interviews.create_index("status")
        await self.database.interviews.create_index("created_at")
        await self.database.interviews.create_index("updated_at")
        await self.database.interviews.create_index([("user_id", 1), ("created_at", -1)])

        # Resume indexes
        await self.database.resumes.create_index("user_id")
        await self.database.resumes.create_index("created_at")
        await self.database.resumes.create_index("updated_at")

        # Live interview indexes
        await self.database.live_interviews.create_index("scheduled_at")
        await self.database.live_interviews.create_index("status")
        await self.database.live_interviews.create_index("created_at")

        # Role-specific collection indexes
        await self.database.candidate_profiles.create_index("user_id", unique=True)
        await self.database.candidate_progress.create_index("user_id", unique=True)
        await self.database.candidate_analytics.create_index("user_id")

        await self.database.recruiter_profiles.create_index("user_id", unique=True)
        await self.database.recruiter_analytics.create_index("user_id")

        await self.database.admin_audit_logs.create_index("timestamp")
        await self.database.admin_audit_logs.create_index("action")
        await self.database.admin_audit_logs.create_index("user_id")

        logger.info("Database indexes created")

    async def _create_default_users(self):
        """Create default users for testing and administration."""
        logger.info("Creating default users...")

        default_users = [
            {
                "email": "admin@candidatex.com",
                "full_name": "System Administrator",
                "password": "Admin123!",
                "role": UserRole.ADMIN,
                "status": UserStatus.ACTIVE,
                "email_verified": True
            },
            {
                "email": "test.candidate@candidatex.com",
                "full_name": "Test Candidate",
                "password": "Test123!",
                "role": UserRole.CANDIDATE,
                "status": UserStatus.ACTIVE,
                "email_verified": True
            },
            {
                "email": "test.recruiter@candidatex.com",
                "full_name": "Test Recruiter",
                "password": "Test123!",
                "role": UserRole.RECRUITER,
                "status": UserStatus.ACTIVE,
                "email_verified": True
            }
        ]

        for user_data in default_users:
            # Check if user already exists
            existing_user = await self.database.users.find_one({"email": user_data["email"]})
            if existing_user:
                logger.info(f"User {user_data['email']} already exists, skipping")
                continue

            # Create user
            user_dict = {
                **user_data,
                "password_hash": get_password_hash(user_data["password"]),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            del user_dict["password"]  # Remove plain password

            result = await self.database.users.insert_one(user_dict)
            logger.info(f"Created user {user_data['email']} with ID {result.inserted_id}")

            # Create default data for the user
            await self._create_user_default_data(str(result.inserted_id), user_data["role"])

    async def _create_user_default_data(self, user_id: str, role: UserRole):
        """Create default data for a new user."""
        logger.info(f"Creating default data for user {user_id} with role {role}")

        current_time = datetime.now(timezone.utc)

        if role == UserRole.CANDIDATE:
            # Create candidate profile
            candidate_profile = {
                "user_id": user_id,
                "experience_level": "entry",
                "preferred_job_titles": ["Software Engineer", "Web Developer"],
                "skills": ["Python", "JavaScript", "HTML", "CSS"],
                "target_companies": [],
                "interview_goals": {
                    "weekly_interviews": 3,
                    "target_score": 80,
                    "focus_areas": ["Technical Skills", "Communication"]
                },
                "statistics": {
                    "total_interviews": 0,
                    "completed_interviews": 0,
                    "average_score": 0,
                    "best_score": 0,
                    "current_streak": 0
                },
                "created_at": current_time,
                "updated_at": current_time
            }

            # Create candidate progress tracking
            candidate_progress = {
                "user_id": user_id,
                "skill_progress": {
                    "communication": {"current": 0, "target": 80, "trend": "starting"},
                    "technical": {"current": 0, "target": 80, "trend": "starting"},
                    "problem_solving": {"current": 0, "target": 80, "trend": "starting"},
                    "behavioral": {"current": 0, "target": 80, "trend": "starting"}
                },
                "milestones": [],
                "achievements": [],
                "created_at": current_time,
                "updated_at": current_time
            }

            # Create sample interviews for candidate
            sample_interviews = [
                {
                    "user_id": user_id,
                    "job_title": "Software Engineer",
                    "job_description": "Full-stack development position",
                    "experience_level": "mid",
                    "question_count": 5,
                    "interview_mode": "technical",
                    "status": "completed",
                    "overall_score": 85,
                    "created_at": current_time,
                    "updated_at": current_time,
                    "created_by": user_id
                },
                {
                    "user_id": user_id,
                    "job_title": "Product Manager",
                    "job_description": "Product management role",
                    "experience_level": "senior",
                    "question_count": 4,
                    "interview_mode": "behavioral",
                    "status": "completed",
                    "overall_score": 78,
                    "created_at": current_time,
                    "updated_at": current_time,
                    "created_by": user_id
                }
            ]

            # Insert role-specific data
            await self.database.candidate_profiles.insert_one(candidate_profile)
            await self.database.candidate_progress.insert_one(candidate_progress)

            for interview in sample_interviews:
                await self.database.interviews.insert_one(interview)

        elif role == UserRole.RECRUITER:
            # Create recruiter profile
            recruiter_profile = {
                "user_id": user_id,
                "company": "Test Company",
                "job_title": "Technical Recruiter",
                "specializations": ["Software Engineering", "Product Management"],
                "experience_years": 3,
                "hiring_goals": {
                    "monthly_hires": 5,
                    "target_roles": ["Software Engineer", "Product Manager"],
                    "preferred_candidates": []
                },
                "statistics": {
                    "total_interviews_conducted": 0,
                    "candidates_hired": 0,
                    "average_candidate_score": 0,
                    "success_rate": 0
                },
                "created_at": current_time,
                "updated_at": current_time
            }

            # Create recruiter analytics
            recruiter_analytics = {
                "user_id": user_id,
                "monthly_stats": [],
                "top_performing_candidates": [],
                "interview_trends": [],
                "created_at": current_time,
                "updated_at": current_time
            }

            # Create sample interviews created by recruiter
            sample_interviews = [
                {
                    "user_id": "sample_candidate_1",  # Mock candidate ID
                    "job_title": "Frontend Developer",
                    "job_description": "React development position",
                    "experience_level": "junior",
                    "question_count": 3,
                    "interview_mode": "technical",
                    "status": "pending",
                    "created_at": current_time,
                    "updated_at": current_time,
                    "created_by": user_id
                }
            ]

            # Insert role-specific data
            await self.database.recruiter_profiles.insert_one(recruiter_profile)
            await self.database.recruiter_analytics.insert_one(recruiter_analytics)

            for interview in sample_interviews:
                await self.database.interviews.insert_one(interview)

        elif role == UserRole.ADMIN:
            # Create admin audit log entry
            admin_audit_entry = {
                "user_id": user_id,
                "action": "account_created",
                "resource": "user",
                "resource_id": user_id,
                "details": {"role": "admin", "auto_created": True},
                "timestamp": current_time,
                "ip_address": "system"
            }

            await self.database.admin_audit_logs.insert_one(admin_audit_entry)

    async def _create_default_data(self):
        """Create default application data."""
        logger.info("Creating default application data...")

        # Create sample interview templates
        interview_templates = [
            {
                "name": "Software Engineer Interview",
                "description": "Technical interview for software engineering positions",
                "job_title": "Software Engineer",
                "experience_level": "mid",
                "question_count": 5,
                "interview_mode": "technical",
                "questions": [
                    "Explain the difference between REST and GraphQL",
                    "How do you handle state management in a React application?",
                    "Describe your approach to testing",
                    "How do you optimize database queries?",
                    "Explain a complex problem you solved"
                ],
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "name": "Product Manager Interview",
                "description": "Behavioral interview for product management positions",
                "job_title": "Product Manager",
                "experience_level": "senior",
                "question_count": 4,
                "interview_mode": "behavioral",
                "questions": [
                    "Tell me about a product you launched",
                    "How do you prioritize features?",
                    "Describe a time you dealt with conflicting stakeholder requirements",
                    "How do you measure product success?"
                ],
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]

        for template in interview_templates:
            # Check if template already exists
            existing = await self.database.interview_templates.find_one({"name": template["name"]})
            if not existing:
                await self.database.interview_templates.insert_one(template)
                logger.info(f"Created interview template: {template['name']}")

    async def reset_user_data(self, user_id: str, preserve_auth: bool = True):
        """Reset user data while preserving authentication info."""
        logger.info(f"Resetting data for user {user_id}")

        # Get user role to determine what collections to clean up
        user_doc = await self.database.users.find_one({"_id": user_id})
        if not user_doc:
            logger.warning(f"User {user_id} not found, cannot reset data")
            return

        user = User.from_mongo(user_doc)
        user_role = user.role

        # Delete user's interviews (but keep the user account)
        await self.database.interviews.delete_many({"user_id": user_id})

        # Delete user's resumes
        await self.database.resumes.delete_many({"user_id": user_id})

        # Delete user's live interviews
        await self.database.live_interviews.delete_many({
            "$or": [
                {"candidate_id": user_id},
                {"interviewer_id": user_id},
                {"created_by": user_id}
            ]
        })

        # Delete role-specific data
        if user_role == UserRole.CANDIDATE:
            await self.database.candidate_profiles.delete_many({"user_id": user_id})
            await self.database.candidate_progress.delete_many({"user_id": user_id})
            await self.database.candidate_analytics.delete_many({"user_id": user_id})
        elif user_role == UserRole.RECRUITER:
            await self.database.recruiter_profiles.delete_many({"user_id": user_id})
            await self.database.recruiter_analytics.delete_many({"user_id": user_id})
        elif user_role == UserRole.ADMIN:
            # Don't delete admin audit logs - they should be preserved for compliance
            pass

        # Reset user stats but keep auth info
        if preserve_auth:
            update_data = {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": None,
                "updated_at": datetime.now(timezone.utc)
            }
            await self.database.users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )

        # Recreate default data for the user
        await self._create_user_default_data(user_id, user_role)

        logger.info(f"User data reset completed for {user_id}")

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if self.database is None:
            return {"error": "Database not connected"}

        stats = {}

        # Collection counts
        collections = ["users", "interviews", "resumes", "live_interviews", "interview_templates"]
        for collection in collections:
            try:
                count = await self.database[collection].count_documents({})
                stats[f"{collection}_count"] = count
            except:
                stats[f"{collection}_count"] = 0

        # Database size (approximate)
        try:
            db_stats = await self.database.command("dbStats")
            stats["database_size_mb"] = db_stats.get("dataSize", 0) / (1024 * 1024)
        except:
            stats["database_size_mb"] = 0

        return stats

    async def backup_database(self, backup_name: str) -> Dict[str, Any]:
        """Create database backup (simplified version)."""
        logger.info(f"Creating database backup: {backup_name}")

        # In a real implementation, this would use mongodump or similar
        # For now, just export key collections to JSON

        backup_data = {
            "name": backup_name,
            "timestamp": datetime.now(timezone.utc),
            "collections": {}
        }

        collections_to_backup = ["users", "interviews", "interview_templates"]

        for collection in collections_to_backup:
            try:
                documents = await self.database[collection].find({}).to_list(length=None)
                backup_data["collections"][collection] = documents
                logger.info(f"Backed up {len(documents)} documents from {collection}")
            except Exception as e:
                logger.error(f"Failed to backup collection {collection}: {e}")
                backup_data["collections"][collection] = {"error": str(e)}

        # Store backup metadata (in real implementation, save to file or cloud storage)
        backup_metadata = {
            "name": backup_name,
            "timestamp": backup_data["timestamp"],
            "collections_count": len(backup_data["collections"]),
            "total_documents": sum(len(docs) if isinstance(docs, list) else 0
                                 for docs in backup_data["collections"].values())
        }

        await self.database.backups.insert_one(backup_metadata)

        logger.info(f"Database backup completed: {backup_name}")
        return backup_metadata

# Global database manager instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize database with default data."""
    await db_manager.connect()
    await db_manager.initialize_database()

async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager

async def reset_database():
    """Reset database to initial state (dangerous operation)."""
    logger.warning("Resetting database to initial state...")

    # This is a dangerous operation - only allow in development
    if not settings.DEBUG:
        raise Exception("Database reset only allowed in development mode")

    # Clear all collections except system collections
    collections_to_clear = [
        "users", "interviews", "resumes", "live_interviews",
        "interview_templates", "backups"
    ]

    for collection in collections_to_clear:
        await db_manager.database[collection].delete_many({})

    # Reinitialize
    await db_manager.initialize_database()

    logger.warning("Database reset completed")

# Utility functions for user management
async def create_test_user(email: str, full_name: str, role: UserRole = UserRole.CANDIDATE) -> str:
    """Create a test user and return the user ID."""
    user_data = {
        "email": email,
        "full_name": full_name,
        "password": "Test123!",
        "role": role,
        "status": UserStatus.ACTIVE,
        "email_verified": True
    }

    # Check if user exists
    existing = await db_manager.database.users.find_one({"email": email})
    if existing:
        return str(existing["_id"])

    # Create user
    user_dict = {
        **user_data,
        "password_hash": get_password_hash(user_data["password"]),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    del user_dict["password"]

    result = await db_manager.database.users.insert_one(user_dict)

    # Create default data
    await db_manager._create_user_default_data(str(result.inserted_id), role)

    return str(result.inserted_id)

async def delete_user_data(user_id: str, current_user_role: UserRole) -> bool:
    """Delete user data with role-based permissions."""
    if current_user_role != UserRole.ADMIN:
        # Only admins can delete data
        return False

    # Delete user's data
    await db_manager.reset_user_data(user_id, preserve_auth=False)

    # Mark user as inactive instead of deleting
    await db_manager.database.users.update_one(
        {"_id": user_id},
        {"$set": {
            "status": UserStatus.INACTIVE,
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    return True

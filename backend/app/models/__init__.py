"""
Database models and connection utilities.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
from app.config import settings

# Global database clients
db_client: AsyncIOMotorClient = None
redis_client: redis.Redis = None

async def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if db_client is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Database not available. Check database connection."
        )
    return db_client[settings.MONGODB_DATABASE]

async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    if redis_client is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Redis not available. Check Redis connection."
        )
    return redis_client

def init_database(client: AsyncIOMotorClient):
    """Initialize database client."""
    global db_client
    db_client = client

def init_redis(client: redis.Redis):
    """Initialize Redis client."""
    global redis_client
    redis_client = client

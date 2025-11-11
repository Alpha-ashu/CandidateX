"""
Test Database Setup and Configuration
Provides proper database initialization for integration tests.
"""
import pytest
import asyncio
import os
import motor.motor_asyncio
import redis.asyncio as redis
from typing import AsyncGenerator, Optional
from app.config import settings
from app.models import init_database, init_redis
from app.utils.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Test database configuration
TEST_MONGODB_URL = os.getenv(
    "TEST_MONGODB_URL", 
    "mongodb://localhost:27017/candidatex_test"
)
TEST_REDIS_URL = os.getenv(
    "TEST_REDIS_URL", 
    "redis://localhost:6379/1"
)
TEST_DATABASE_NAME = "candidatex_test"


class TestDatabaseSetup:
    """Manages test database setup and teardown."""
    
    def __init__(self):
        self.mongodb_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.db_initialized = False
    
    async def setup_test_database(self):
        """Set up test database with proper connections."""
        logger.info("Setting up test database...")
        
        try:
            # Initialize MongoDB connection
            self.mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(TEST_MONGODB_URL)
            # Test connection
            await self.mongodb_client.admin.command('ping')
            
            # Initialize global database client
            init_database(self.mongodb_client)
            
            # Initialize Redis connection (optional, may fail in test environment)
            try:
                self.redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=1,
                    decode_responses=True
                )
                await self.redis_client.ping()
                init_redis(self.redis_client)
                logger.info("Redis connected for tests")
            except Exception as redis_error:
                logger.warning(f"Redis not available for tests: {redis_error}")
                self.redis_client = None
            
            # Initialize database with test data
            await db_manager.connect()
            await db_manager.initialize_database()
            
            self.db_initialized = True
            logger.info("Test database setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup test database: {e}")
            raise
    
    async def cleanup_test_database(self):
        """Clean up test database."""
        logger.info("Cleaning up test database...")
        
        try:
            if self.db_initialized:
                # Disconnect database manager
                await db_manager.disconnect()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            # Close MongoDB connection
            if self.mongodb_client:
                self.mongodb_client.close()
            
            logger.info("Test database cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during test database cleanup: {e}")
    
    async def reset_test_database(self):
        """Reset test database to clean state."""
        if not self.db_initialized:
            await self.setup_test_database()
            return
        
        try:
            # Drop all test collections
            db = self.mongodb_client[TEST_DATABASE_NAME]
            collections = await db.list_collection_names()
            
            for collection_name in collections:
                if not collection_name.startswith('system.'):
                    await db[collection_name].delete_many({})
            
            # Reinitialize with fresh data
            await db_manager.initialize_database()
            
            logger.info("Test database reset completed")
            
        except Exception as e:
            logger.error(f"Failed to reset test database: {e}")


# Global test database setup instance
test_db_setup = TestDatabaseSetup()


@pytest.fixture(scope="session")
async def test_database():
    """Session-scoped test database setup and teardown."""
    try:
        await test_db_setup.setup_test_database()
        yield test_db_setup
    finally:
        await test_db_setup.cleanup_test_database()


@pytest.fixture
async def test_db_reset(test_database):
    """Reset test database for each test."""
    await test_db_setup.reset_test_database()
    yield
    # Cleanup after each test
    await test_db_setup.reset_test_database()


@pytest.fixture
async def test_database_no_reset(test_database):
    """Test database without automatic reset (for performance)."""
    yield test_db_setup


# Utility functions for test data management
async def create_test_user_in_db(email: str, full_name: str, role: str = "candidate", password: str = "Test123!"):
    """Create a test user directly in the database."""
    if not test_db_setup.db_initialized:
        await test_db_setup.setup_test_database()
    
    from app.utils.database import create_test_user
    return await create_test_user(email, full_name, role)


async def cleanup_test_user_from_db(user_id: str, role: str):
    """Clean up a test user from the database."""
    if not test_db_setup.db_initialized:
        return
    
    from app.utils.database import delete_user_data
    from app.models.user import UserRole
    
    role_mapping = {
        "candidate": UserRole.CANDIDATE,
        "recruiter": UserRole.RECRUITER,
        "admin": UserRole.ADMIN
    }
    
    user_role = role_mapping.get(role, UserRole.CANDIDATE)
    await delete_user_data(user_id, user_role)


# Database availability checks
async def check_test_database_availability():
    """Check if test database is available."""
    try:
        # Test MongoDB connection
        test_client = motor.motor_asyncio.AsyncIOMotorClient(TEST_MONGODB_URL)
        await test_client.admin.command('ping')
        test_client.close()
        
        # Test Redis connection (optional)
        try:
            test_redis = redis.Redis(host="localhost", port=6379, db=1)
            await test_redis.ping()
            await test_redis.close()
            redis_available = True
        except:
            redis_available = False
        
        return {
            "mongodb": True,
            "redis": redis_available
        }
        
    except Exception as e:
        logger.warning(f"Test database not available: {e}")
        return {
            "mongodb": False,
            "redis": False
        }


@pytest.fixture
async def database_available():
    """Check database availability and skip tests if not available."""
    availability = await check_test_database_availability()
    
    if not availability["mongodb"]:
        pytest.skip("MongoDB not available for integration tests")
    
    if not availability["redis"]:
        pytest.skip("Redis not available for integration tests")
    
    yield availability


# Mark tests that require database
def pytest_configure(config):
    """Configure pytest markers for database tests."""
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "no_db: mark test as not requiring database"
    )
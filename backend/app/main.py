"""
Main FastAPI application for CandidateX platform.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import logging
from typing import AsyncGenerator

from app.config import settings
from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.interviews.routes import router as interviews_router
from app.dashboard.routes import router as dashboard_router
from app.admin.routes import router as admin_router
from app.ai.routes import router as ai_router
from app.feedback.routes import router as feedback_router
from app.websocket.routes import router as websocket_router
from app.utils.database import init_database, db_manager
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    InputValidationMiddleware,
    IPFilterMiddleware,
    APIVersioningMiddleware,
    MaintenanceModeMiddleware,
    create_cors_middleware,
    create_trusted_host_middleware,
    create_rate_limit_middleware,
    rate_limit_exceeded_handler,
    http_exception_handler,
    general_exception_handler,
    limiter
)
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

# Configure logging
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
}
logging.basicConfig(
    level=log_level_map.get(settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global database clients
db_client: AsyncIOMotorClient = None
redis_client: redis.Redis = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    global db_client, redis_client

    # Startup
    logger.info("Starting CandidateX backend...")

    # Check if we're in test environment
    import sys
    is_testing = any("pytest" in arg or "test" in arg.lower() for arg in sys.argv)

    if not is_testing:
        try:
            # Initialize database and create default data
            await init_database()
            db_client = db_manager.db_client
            redis_client = db_manager.redis_client

            # Initialize the global database client for dependency injection
            from app.models import init_database as init_db_client
            init_db_client(db_client)

            logger.info("Database initialized with default data")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise during startup - let the app start without database
            # This allows testing without full database setup
            logger.warning("Starting application without database initialization")
    else:
        logger.info("Test environment detected - skipping database initialization")

    yield

    # Shutdown
    logger.info("Shutting down CandidateX backend...")
    if not is_testing:
        await db_manager.disconnect()

# Create FastAPI application
app = FastAPI(
    title="CandidateX API",
    description="AI-powered mock interview and hiring platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize limiter on app state for SlowAPI middleware
app.state.limiter = limiter

# Add security middleware (order matters!)
app.add_middleware(MaintenanceModeMiddleware, maintenance_mode=False)
app.add_middleware(IPFilterMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(APIVersioningMiddleware)
app.add_middleware(CORSMiddleware, **create_cors_middleware())

# Only add TrustedHostMiddleware if not in test environment
import sys
is_testing = any("pytest" in arg or "test" in arg.lower() for arg in sys.argv)
if not is_testing:
    app.add_middleware(TrustedHostMiddleware, **create_trusted_host_middleware())

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    interviews_router,
    prefix="/api/v1/interviews",
    tags=["Interviews"]
)

app.include_router(
    dashboard_router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Administration"]
)

app.include_router(
    ai_router,
    prefix="/api/v1/ai",
    tags=["AI Assistant"]
)

app.include_router(
    feedback_router,
    prefix="/api/v1/feedback",
    tags=["Feedback"]
)

app.include_router(
    websocket_router,
    prefix="/api/v1/ws",
    tags=["WebSocket"]
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected" if db_client else "disconnected",
        "redis": "connected" if redis_client else "disconnected"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to CandidateX API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Simple test endpoint
@app.get("/test", tags=["Test"])
async def test_endpoint():
    """Simple test endpoint."""
    return {"message": "Test endpoint works!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

"""
Security middleware for FastAPI application.
"""
import logging
import re
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' wss: https:; "
            "media-src 'self' blob:; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # HSTS (HTTP Strict Transport Security) - only in production
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = datetime.now(timezone.utc)

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'} "
            f"user-agent: {request.headers.get('user-agent', 'unknown')}"
        )

        try:
            response = await call_next(request)
            process_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"status: {response.status_code} "
                f"time: {process_time:.2f}ms"
            )

            return response

        except Exception as e:
            process_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error: {str(e)} time: {process_time:.2f}ms"
            )
            raise

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize input data."""

    def __init__(self, app):
        super().__init__(app)
        # Common SQL injection patterns
        self.sql_patterns = [
            r';\s*--',  # SQL comment
            r';\s*/\*',  # SQL comment block start
            r'union\s+select',  # Union select
            r'/\*.*\*/',  # SQL comment blocks
        ]

        # XSS patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
        ]

        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./',  # Directory traversal
            r'\.\.\\',  # Windows directory traversal
            r'%2e%2e%2f',  # URL encoded ../
            r'%2e%2e%5c',  # URL encoded ..\
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request path
        if self._contains_malicious_patterns(request.url.path, self.path_traversal_patterns):
            logger.warning(f"Path traversal attempt detected: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request path"}
            )

        # Validate query parameters
        for key, value in request.query_params.items():
            if self._contains_malicious_patterns(str(value), self.sql_patterns + self.xss_patterns):
                logger.warning(f"Malicious query parameter detected: {key}={value}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request parameters"}
                )

        # For POST/PUT/PATCH requests, we'll validate body in the endpoint
        # since FastAPI handles JSON parsing

        response = await call_next(request)
        return response

    def _contains_malicious_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text contains malicious patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

class IPFilterMiddleware(BaseHTTPMiddleware):
    """Middleware to filter requests based on IP addresses."""

    def __init__(self, app, allowed_ips: Optional[List[str]] = None, blocked_ips: Optional[List[str]] = None):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips or [])
        self.blocked_ips = set(blocked_ips or [])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else None

        if not client_ip:
            return await call_next(request)

        # Check blocked IPs
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )

        # Check allowed IPs (if whitelist is enabled)
        if self.allowed_ips and client_ip not in self.allowed_ips:
            logger.warning(f"Non-whitelisted IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )

        return await call_next(request)

class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check API version
        path = request.url.path

        if path.startswith("/api/"):
            # Extract version from path
            path_parts = path.split("/")
            if len(path_parts) >= 3 and path_parts[2].startswith("v"):
                version = path_parts[2]
                # Add version to request state
                request.state.api_version = version
            else:
                # Default to v1
                request.state.api_version = "v1"

        response = await call_next(request)
        return response

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """Middleware to handle maintenance mode."""

    def __init__(self, app, maintenance_mode: bool = False):
        super().__init__(app)
        self.maintenance_mode = maintenance_mode

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self.maintenance_mode:
            # Allow health checks and admin access during maintenance
            if not (
                request.url.path.startswith("/health") or
                request.url.path.startswith("/api/v1/admin") or
                request.url.path.startswith("/docs") or
                request.url.path.startswith("/redoc") or
                request.url.path.startswith("/openapi.json")
            ):
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "detail": "Service is currently under maintenance",
                        "estimated_downtime": "2 hours"
                    }
                )

        response = await call_next(request)
        return response

def create_cors_middleware() -> dict:
    """Create CORS middleware configuration."""
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
        ],
        "max_age": 86400,  # 24 hours
    }

def create_trusted_host_middleware() -> dict:
    """Create trusted host middleware configuration."""
    allowed_hosts = settings.ALLOWED_HOSTS.copy()
    # Add testserver for testing
    if "testserver" not in allowed_hosts:
        allowed_hosts.append("testserver")
    return {
        "allowed_hosts": allowed_hosts
    }

def create_rate_limit_middleware() -> SlowAPIMiddleware:
    """Create rate limiting middleware."""
    return SlowAPIMiddleware()

# Rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Handle rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'}: {request.url.path}")

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )

# Custom exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Security utility functions
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS attacks."""
    if not text:
        return text

    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove javascript: URLs
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)

    # Remove event handlers
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

    return text

def validate_email_format(email: str) -> bool:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_password_strength(password: str) -> Dict[str, bool]:
    """Validate password strength requirements."""
    return {
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r'[A-Z]', password)),
        "lowercase": bool(re.search(r'[a-z]', password)),
        "digit": bool(re.search(r'\d', password)),
        "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }

def is_suspicious_request(request: Request) -> bool:
    """Check if request appears suspicious."""
    user_agent = request.headers.get("user-agent", "").lower()

    # Check for common bot patterns
    suspicious_patterns = [
        "bot", "crawler", "spider", "scraper",
        "python-requests", "curl", "wget"
    ]

    for pattern in suspicious_patterns:
        if pattern in user_agent:
            return True

    return False

# Security monitoring
class SecurityMonitor:
    """Monitor security events and anomalies."""

    def __init__(self):
        self.failed_login_attempts = {}
        self.suspicious_ips = set()
        self.blocked_ips = set()

    def record_failed_login(self, ip_address: str, email: str):
        """Record failed login attempt."""
        key = f"{ip_address}:{email}"
        if key not in self.failed_login_attempts:
            self.failed_login_attempts[key] = {"count": 0, "first_attempt": datetime.now(timezone.utc)}

        self.failed_login_attempts[key]["count"] += 1
        self.failed_login_attempts[key]["last_attempt"] = datetime.now(timezone.utc)

        # Check if should be blocked
        if self.failed_login_attempts[key]["count"] >= 5:
            self.suspicious_ips.add(ip_address)
            logger.warning(f"Suspicious login activity from IP: {ip_address}")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked."""
        return ip_address in self.blocked_ips

    def block_ip(self, ip_address: str, reason: str = "Security violation"):
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP blocked: {ip_address} - Reason: {reason}")

    def unblock_ip(self, ip_address: str):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip_address)
        logger.info(f"IP unblocked: {ip_address}")

    def get_security_stats(self) -> Dict[str, int]:
        """Get security statistics."""
        return {
            "suspicious_ips": len(self.suspicious_ips),
            "blocked_ips": len(self.blocked_ips),
            "active_failed_attempts": len(self.failed_login_attempts)
        }

# Global security monitor instance
security_monitor = SecurityMonitor()

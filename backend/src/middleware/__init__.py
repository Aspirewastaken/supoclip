"""
Middleware package for SupoClip backend
"""
from .quota_check import QuotaChecker, QuotaExceededError, check_quota_middleware
from .auth import get_current_user, get_current_user_optional, verify_resource_ownership
from .rate_limit import (
    RateLimiter,
    rate_limiter,
    rate_limit_dependency,
    video_processing_rate_limit,
    api_rate_limit
)
from .security_headers import SecurityHeadersMiddleware, CORSSecurityMiddleware

__all__ = [
    "QuotaChecker",
    "QuotaExceededError",
    "check_quota_middleware",
    "get_current_user",
    "get_current_user_optional",
    "verify_resource_ownership",
    "RateLimiter",
    "rate_limiter",
    "rate_limit_dependency",
    "video_processing_rate_limit",
    "api_rate_limit",
    "SecurityHeadersMiddleware",
    "CORSSecurityMiddleware",
]

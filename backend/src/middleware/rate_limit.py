"""
Rate Limiting Middleware
Simple token bucket rate limiter using Redis
"""
from fastapi import HTTPException, Request
from typing import Optional
import time
import logging
import redis.asyncio as redis

from ..config import Config

logger = logging.getLogger(__name__)
config = Config()


class RateLimiter:
    """Token bucket rate limiter using Redis"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self.redis_client is None:
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                decode_responses=True
            )
        return self.redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit using sliding window.

        Args:
            key: Unique identifier for the rate limit (e.g., user_id:endpoint)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        redis_client = await self.get_redis()
        now = time.time()
        window_start = now - window_seconds

        try:
            # Remove old entries outside the window
            await redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            current_count = await redis_client.zcard(key)

            if current_count < max_requests:
                # Add current request
                await redis_client.zadd(key, {str(now): now})
                # Set expiry for automatic cleanup
                await redis_client.expire(key, window_seconds)
                remaining = max_requests - current_count - 1
                return True, remaining
            else:
                remaining = 0
                return False, remaining

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, max_requests


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_dependency(
    request: Request,
    user_id: Optional[str] = None,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """
    FastAPI dependency for rate limiting.

    Args:
        request: FastAPI request object
        user_id: Optional user ID (if None, uses IP address)
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    # Use user_id if available, otherwise use IP address
    identifier = user_id if user_id else request.client.host if request.client else "unknown"
    key = f"rate_limit:{identifier}:{request.url.path}"

    allowed, remaining = await rate_limiter.check_rate_limit(
        key, max_requests, window_seconds
    )

    if not allowed:
        logger.warning(f"Rate limit exceeded for {identifier} on {request.url.path}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
            headers={
                "Retry-After": str(window_seconds),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + window_seconds)
            }
        )

    # Add rate limit headers to response (this would need middleware to add to response)
    logger.debug(f"Rate limit check passed for {identifier}: {remaining} remaining")


async def video_processing_rate_limit(request: Request, user_id: str):
    """
    Stricter rate limit for video processing endpoints.
    10 requests per hour per user.
    """
    await rate_limit_dependency(
        request=request,
        user_id=user_id,
        max_requests=10,
        window_seconds=3600  # 1 hour
    )


async def api_rate_limit(request: Request, user_id: Optional[str] = None):
    """
    Standard rate limit for API endpoints.
    100 requests per minute.
    """
    await rate_limit_dependency(
        request=request,
        user_id=user_id,
        max_requests=100,
        window_seconds=60  # 1 minute
    )

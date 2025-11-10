"""
Error recovery mechanisms and patterns.

Provides utilities for graceful degradation and recovery from failures.
"""

import logging
import asyncio
from typing import Callable, TypeVar, Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta

from .custom_exceptions import (
    BaseSupoClipException,
    is_retryable_error,
    is_non_retryable_error,
)
from .circuit_breaker import CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorRecoveryStrategy:
    """
    Defines recovery strategies for different error types.

    Strategies:
    - RETRY: Retry the operation with exponential backoff
    - FALLBACK: Use a fallback method or default value
    - CIRCUIT_BREAK: Open circuit breaker and fast-fail
    - LOG_AND_CONTINUE: Log error and continue with degraded functionality
    - FAIL_FAST: Immediately propagate the error
    """

    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    LOG_AND_CONTINUE = "log_and_continue"
    FAIL_FAST = "fail_fast"


class RecoveryContext:
    """Context for error recovery attempts."""

    def __init__(self):
        self.attempts: List[Dict[str, Any]] = []
        self.last_error: Optional[Exception] = None
        self.recovered: bool = False
        self.recovery_method: Optional[str] = None
        self.started_at: datetime = datetime.now()
        self.completed_at: Optional[datetime] = None

    def record_attempt(self, error: Exception, strategy: str):
        """Record a recovery attempt."""
        self.attempts.append({
            "timestamp": datetime.now(),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "strategy": strategy
        })
        self.last_error = error

    def mark_recovered(self, method: str):
        """Mark recovery as successful."""
        self.recovered = True
        self.recovery_method = method
        self.completed_at = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """Get recovery summary."""
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()

        return {
            "recovered": self.recovered,
            "recovery_method": self.recovery_method,
            "attempts": len(self.attempts),
            "duration_seconds": duration,
            "errors": [
                {
                    "type": attempt["error_type"],
                    "message": attempt["error_message"]
                }
                for attempt in self.attempts
            ]
        }


async def retry_with_recovery(
    func: Callable[..., T],
    *args,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    fallback: Optional[Callable[..., T]] = None,
    fallback_value: Optional[T] = None,
    **kwargs
) -> T:
    """
    Execute function with retry and recovery logic.

    Args:
        func: Function to execute
        *args: Positional arguments
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        backoff_factor: Backoff multiplier
        fallback: Fallback function to use if all retries fail
        fallback_value: Default value to return if all recovery fails
        **kwargs: Keyword arguments

    Returns:
        Result from successful execution or fallback

    Raises:
        Exception: If all recovery attempts fail and no fallback
    """
    context = RecoveryContext()
    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            context.mark_recovered("direct_success")
            return result

        except CircuitBreakerOpenError as e:
            # Circuit is open, try fallback immediately
            context.record_attempt(e, ErrorRecoveryStrategy.CIRCUIT_BREAK)
            logger.warning(
                f"Circuit breaker open for {func.__name__}. Attempting fallback.",
                extra={"retry_after": e.retry_after}
            )

            if fallback:
                try:
                    result = await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                    context.mark_recovered("fallback")
                    logger.info(f"Recovered using fallback for {func.__name__}")
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")

            if fallback_value is not None:
                context.mark_recovered("default_value")
                return fallback_value

            raise

        except Exception as e:
            context.record_attempt(e, ErrorRecoveryStrategy.RETRY)

            # Check if error is retryable
            if is_non_retryable_error(e):
                logger.error(
                    f"Non-retryable error in {func.__name__}: {e}",
                    exc_info=True
                )
                raise

            # Last attempt - try fallback
            if attempt == max_attempts:
                logger.error(
                    f"All retry attempts failed for {func.__name__}",
                    extra={"attempts": attempt, "summary": context.get_summary()}
                )

                # Try fallback
                if fallback:
                    try:
                        result = await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                        context.mark_recovered("fallback")
                        logger.info(f"Recovered using fallback for {func.__name__}")
                        return result
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}")

                # Use default value
                if fallback_value is not None:
                    context.mark_recovered("default_value")
                    return fallback_value

                raise

            # Log retry
            logger.warning(
                f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.1f}s...",
                extra={"error_type": e.__class__.__name__}
            )

            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)


def with_fallback(fallback_func: Optional[Callable] = None, fallback_value: Any = None):
    """
    Decorator to add fallback recovery to a function.

    Usage:
        @with_fallback(fallback_func=get_cached_result)
        async def fetch_data():
            # May fail
            pass

        @with_fallback(fallback_value=[])
        async def get_clips():
            # May fail, returns [] if it does
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed: {e}. Attempting recovery.",
                    exc_info=True
                )

                # Try fallback function
                if fallback_func:
                    try:
                        logger.info(f"Using fallback function for {func.__name__}")
                        if asyncio.iscoroutinefunction(fallback_func):
                            return await fallback_func(*args, **kwargs)
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback function also failed: {fallback_error}")

                # Use fallback value
                if fallback_value is not None:
                    logger.info(f"Using fallback value for {func.__name__}")
                    return fallback_value

                # No recovery possible
                raise

        return wrapper
    return decorator


async def with_timeout_recovery(
    func: Callable[..., T],
    *args,
    timeout: float = 30.0,
    fallback: Optional[Callable[..., T]] = None,
    fallback_value: Optional[T] = None,
    **kwargs
) -> T:
    """
    Execute function with timeout and recovery.

    Args:
        func: Function to execute
        *args: Positional arguments
        timeout: Timeout in seconds
        fallback: Fallback function
        fallback_value: Default value
        **kwargs: Keyword arguments

    Returns:
        Result or fallback
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        else:
            # For sync functions, run in executor with timeout
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=timeout
            )

    except asyncio.TimeoutError as e:
        logger.error(
            f"Function {func.__name__} timed out after {timeout}s",
            exc_info=True
        )

        # Try fallback
        if fallback:
            try:
                logger.info(f"Using fallback for timed-out {func.__name__}")
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                return fallback(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

        # Use default value
        if fallback_value is not None:
            return fallback_value

        raise


class GracefulDegradation:
    """
    Context manager for graceful degradation.

    Allows operations to continue with reduced functionality on errors.

    Usage:
        with GracefulDegradation(log_errors=True) as gd:
            # Critical operation
            result = await critical_function()

        if gd.degraded:
            # Operation failed, use degraded mode
            result = default_value
    """

    def __init__(self, log_errors: bool = True, suppress_exceptions: bool = True):
        self.log_errors = log_errors
        self.suppress_exceptions = suppress_exceptions
        self.degraded = False
        self.error: Optional[Exception] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.degraded = True
            self.error = exc_val

            if self.log_errors:
                logger.warning(
                    f"Operation degraded due to error: {exc_val}",
                    exc_info=(exc_type, exc_val, exc_tb)
                )

            # Suppress exception if requested
            return self.suppress_exceptions

        return False


# Example recovery functions

async def cached_fallback(cache_key: str, fetch_func: Callable, *args, **kwargs):
    """
    Fallback to cached data if fetch fails.

    Usage:
        result = await retry_with_recovery(
            fetch_fresh_data,
            fallback=lambda: cached_fallback("my_key", fetch_fresh_data)
        )
    """
    # This is a placeholder - implement with your cache backend (Redis, etc.)
    logger.info(f"Using cached fallback for key: {cache_key}")
    # return await cache.get(cache_key)
    return None


def log_and_continue_recovery(error: Exception, context: Dict[str, Any] = None):
    """
    Log error and continue with degraded functionality.

    Usage:
        try:
            # Optional feature
            await send_analytics()
        except Exception as e:
            log_and_continue_recovery(e, {"feature": "analytics"})
    """
    logger.warning(
        "Non-critical operation failed, continuing with degradation",
        extra={
            "error": str(error),
            "error_type": error.__class__.__name__,
            "context": context or {}
        }
    )

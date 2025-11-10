"""
Circuit breaker pattern implementation for external service calls.

Prevents cascade failures by temporarily blocking calls to failing services.
"""

import time
import asyncio
import logging
from enum import Enum
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failure threshold exceeded, requests blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: list = field(default_factory=list)

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls

    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, requests are blocked
    - HALF_OPEN: Testing recovery, limited requests allowed

    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=RequestException
        )

        @breaker
        async def call_external_api():
            # API call here
            pass
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        half_open_max_calls: int = 3,
        name: str = None
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            half_open_max_calls: Max calls allowed in half-open state
            name: Name for this circuit breaker instance
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls
        self.name = name or f"CircuitBreaker-{id(self)}"

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get statistics."""
        return self._stats

    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state."""
        old_state = self._state
        self._state = new_state

        self._stats.state_changes.append({
            "timestamp": datetime.now(),
            "from": old_state.value,
            "to": new_state.value
        })

        logger.info(
            f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "failure_count": self._failure_count,
            }
        )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            self._failure_count = 0
            self._stats.successful_calls += 1
            self._stats.last_success_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                # Recovered successfully
                self._change_state(CircuitState.CLOSED)
                self._half_open_calls = 0
                logger.info(f"Circuit breaker '{self.name}' recovered successfully")

    async def _on_failure(self, error: Exception):
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._stats.failed_calls += 1
            self._stats.last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                # Recovery failed
                self._change_state(CircuitState.OPEN)
                logger.warning(
                    f"Circuit breaker '{self.name}' recovery failed",
                    extra={
                        "circuit_breaker": self.name,
                        "error": str(error),
                    }
                )

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    # Threshold exceeded, open circuit
                    self._change_state(CircuitState.OPEN)
                    logger.error(
                        f"Circuit breaker '{self.name}' opened after {self._failure_count} failures",
                        extra={
                            "circuit_breaker": self.name,
                            "failure_count": self._failure_count,
                            "threshold": self.failure_threshold,
                        }
                    )

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        self._stats.total_calls += 1

        # Check state before calling
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                async with self._lock:
                    self._change_state(CircuitState.HALF_OPEN)
                    self._half_open_calls = 0
            else:
                # Circuit is open, reject call
                retry_after = int(self.recovery_timeout - (time.time() - self._last_failure_time))
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. Service unavailable.",
                    retry_after=max(retry_after, 0)
                )

        # Limit calls in half-open state
        if self._state == CircuitState.HALF_OPEN:
            async with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is in half-open state. Max test calls exceeded.",
                        retry_after=int(self.recovery_timeout)
                    )
                self._half_open_calls += 1

        # Make the call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except self.expected_exception as e:
            await self._on_failure(e)
            raise

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for protecting functions with circuit breaker.

        Usage:
            @circuit_breaker
            async def call_api():
                pass
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)

        return wrapper

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._change_state(CircuitState.CLOSED)
            self._failure_count = 0
            self._half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset")


# Global circuit breakers for common services
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception
) -> CircuitBreaker:
    """
    Get or create a named circuit breaker.

    Usage:
        breaker = get_circuit_breaker("assemblyai", failure_threshold=3)
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name
        )

    return _circuit_breakers[name]


# Pre-configured circuit breakers for SupoClip services
assemblyai_breaker = get_circuit_breaker(
    "assemblyai",
    failure_threshold=5,
    recovery_timeout=120.0,  # 2 minutes
)

llm_breaker = get_circuit_breaker(
    "llm",
    failure_threshold=5,
    recovery_timeout=60.0,  # 1 minute
)

youtube_breaker = get_circuit_breaker(
    "youtube",
    failure_threshold=3,
    recovery_timeout=30.0,  # 30 seconds
)

database_breaker = get_circuit_breaker(
    "database",
    failure_threshold=10,  # Higher threshold for database
    recovery_timeout=10.0,  # Shorter recovery time
)


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers."""
    return {
        name: {
            "state": breaker.state.value,
            "stats": {
                "total_calls": breaker.stats.total_calls,
                "successful_calls": breaker.stats.successful_calls,
                "failed_calls": breaker.stats.failed_calls,
                "success_rate": breaker.stats.success_rate(),
                "failure_rate": breaker.stats.failure_rate(),
            }
        }
        for name, breaker in _circuit_breakers.items()
    }

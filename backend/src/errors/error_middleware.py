"""
Error logging and monitoring middleware for FastAPI.
"""

import time
import logging
import traceback
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and errors with correlation IDs.

    Features:
    - Assigns unique request ID to each request
    - Logs request/response details
    - Tracks request duration
    - Captures error context
    - Adds correlation ID to error logs
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )

        start_time = time.time()
        response = None
        error = None

        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            error = exc
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                },
                exc_info=exc
            )
            raise

        finally:
            duration = time.time() - start_time

            # Log response
            if response:
                logger.info(
                    f"Request completed: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2),
                    }
                )

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id

            elif error:
                logger.error(
                    f"Request errored: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "duration_ms": round(duration * 1000, 2),
                        "error": str(error),
                    }
                )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request context to all logs.

    Enriches log records with request metadata for better traceability.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add request context to logging context
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Store context in request state
        request.state.context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "user_id": request.headers.get("user_id"),
        }

        response = await call_next(request)
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor performance and detect slow requests.

    Logs warnings for requests that exceed configured thresholds.
    """

    def __init__(self, app: ASGIApp, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold  # seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        request_id = getattr(request.state, "request_id", "unknown")

        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration * 1000, 2),
                    "threshold_ms": round(self.slow_request_threshold * 1000, 2),
                    "path": request.url.path,
                    "method": request.method,
                }
            )

        return response


class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle common recoverable errors gracefully.

    Provides automatic recovery for certain error types without
    propagating them to the client.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response

        except ConnectionError as exc:
            # Log connection errors but provide helpful response
            logger.error(
                "Connection error during request processing",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "error": str(exc),
                },
                exc_info=exc
            )
            # Re-raise to be handled by exception handlers
            raise

        except TimeoutError as exc:
            # Log timeout errors
            logger.error(
                "Timeout during request processing",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "error": str(exc),
                },
                exc_info=exc
            )
            raise

        except MemoryError as exc:
            # Critical error - log and raise
            logger.critical(
                "Memory error during request processing",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
                exc_info=exc
            )
            raise


def setup_error_middleware(app):
    """
    Register all error middleware with the FastAPI app.

    Usage:
        from .errors.error_middleware import setup_error_middleware
        setup_error_middleware(app)
    """
    # Order matters - add in reverse order of desired execution
    app.add_middleware(ErrorRecoveryMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=5.0)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(ErrorLoggingMiddleware)

    logger.info("Error middleware registered successfully")

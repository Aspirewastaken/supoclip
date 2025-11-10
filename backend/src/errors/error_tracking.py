"""
Error tracking and monitoring integration (Sentry).

Provides centralized error tracking, performance monitoring, and alerting.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ErrorTracker:
    """
    Error tracking wrapper for Sentry integration.

    Handles initialization, error capture, and context management.
    """

    def __init__(self):
        self.enabled = False
        self.sentry = None
        self._initialized = False

    def initialize(
        self,
        dsn: Optional[str] = None,
        environment: str = "production",
        release: Optional[str] = None,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
        enable_tracing: bool = True
    ):
        """
        Initialize Sentry error tracking.

        Args:
            dsn: Sentry DSN (will use SENTRY_DSN env var if not provided)
            environment: Environment name (production, staging, development)
            release: Release version
            traces_sample_rate: Percentage of transactions to trace (0.0-1.0)
            profiles_sample_rate: Percentage of transactions to profile (0.0-1.0)
            enable_tracing: Enable performance tracing
        """
        if self._initialized:
            logger.warning("Error tracker already initialized")
            return

        # Get DSN from environment or parameter
        dsn = dsn or os.getenv("SENTRY_DSN")

        if not dsn:
            logger.info("Sentry DSN not configured. Error tracking disabled.")
            self.enabled = False
            return

        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            # Configure Sentry
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                release=release or os.getenv("APP_VERSION", "unknown"),
                traces_sample_rate=traces_sample_rate,
                profiles_sample_rate=profiles_sample_rate,
                enable_tracing=enable_tracing,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,  # Capture info and above as breadcrumbs
                        event_level=logging.ERROR  # Send errors as events
                    ),
                ],
                # Additional options
                send_default_pii=False,  # Don't send personally identifiable information
                attach_stacktrace=True,
                max_breadcrumbs=50,
                before_send=self._before_send,
            )

            self.sentry = sentry_sdk
            self.enabled = True
            self._initialized = True

            logger.info(
                f"Sentry error tracking initialized: environment={environment}, "
                f"release={release}, tracing={enable_tracing}"
            )

        except ImportError:
            logger.warning(
                "Sentry SDK not installed. Install with: pip install sentry-sdk"
            )
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)
            self.enabled = False

    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter or modify events before sending to Sentry.

        Can be used to:
        - Remove sensitive data
        - Filter out specific errors
        - Add additional context
        """
        # Filter out specific exceptions that shouldn't be tracked
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]

            # Don't track certain validation errors
            if exc_type.__name__ in ["ValidationError", "RequestValidationError"]:
                return None

            # Don't track 404 errors
            if exc_type.__name__ == "HTTPException" and hasattr(exc_value, "status_code"):
                if exc_value.status_code == 404:
                    return None

        return event

    def capture_exception(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error",
        fingerprint: Optional[list] = None
    ):
        """
        Capture an exception and send to Sentry.

        Args:
            error: Exception to capture
            context: Additional context data
            level: Error level (error, warning, info, debug)
            fingerprint: Custom fingerprint for grouping errors
        """
        if not self.enabled:
            return

        try:
            with self.sentry.push_scope() as scope:
                # Add context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)

                # Set level
                scope.level = level

                # Set custom fingerprint for grouping
                if fingerprint:
                    scope.fingerprint = fingerprint

                # Capture exception
                self.sentry.capture_exception(error)

        except Exception as e:
            logger.error(f"Failed to capture exception in Sentry: {e}", exc_info=True)

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Capture a message and send to Sentry.

        Args:
            message: Message to capture
            level: Message level (error, warning, info, debug)
            context: Additional context data
        """
        if not self.enabled:
            return

        try:
            with self.sentry.push_scope() as scope:
                # Add context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)

                # Set level
                scope.level = level

                # Capture message
                self.sentry.capture_message(message)

        except Exception as e:
            logger.error(f"Failed to capture message in Sentry: {e}", exc_info=True)

    def set_user(self, user_id: str, email: Optional[str] = None, username: Optional[str] = None):
        """
        Set user context for error tracking.

        Args:
            user_id: User ID
            email: User email (optional)
            username: Username (optional)
        """
        if not self.enabled:
            return

        try:
            self.sentry.set_user({
                "id": user_id,
                "email": email,
                "username": username
            })
        except Exception as e:
            logger.error(f"Failed to set user context: {e}", exc_info=True)

    def set_tag(self, key: str, value: str):
        """
        Set a tag for filtering errors.

        Args:
            key: Tag key
            value: Tag value
        """
        if not self.enabled:
            return

        try:
            self.sentry.set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to set tag: {e}", exc_info=True)

    def set_context(self, key: str, value: Dict[str, Any]):
        """
        Set additional context for errors.

        Args:
            key: Context key
            value: Context data
        """
        if not self.enabled:
            return

        try:
            self.sentry.set_context(key, value)
        except Exception as e:
            logger.error(f"Failed to set context: {e}", exc_info=True)

    @contextmanager
    def configure_scope(self):
        """
        Context manager for configuring error scope.

        Usage:
            with error_tracker.configure_scope() as scope:
                scope.set_tag("video_id", "abc123")
                # ... code that might raise errors
        """
        if not self.enabled:
            yield None
            return

        try:
            with self.sentry.configure_scope() as scope:
                yield scope
        except Exception as e:
            logger.error(f"Failed to configure scope: {e}", exc_info=True)
            yield None

    def start_transaction(self, name: str, op: str = "task") -> Optional[Any]:
        """
        Start a performance transaction.

        Args:
            name: Transaction name
            op: Operation type (task, http, db, etc.)

        Returns:
            Transaction object or None if disabled
        """
        if not self.enabled:
            return None

        try:
            return self.sentry.start_transaction(name=name, op=op)
        except Exception as e:
            logger.error(f"Failed to start transaction: {e}", exc_info=True)
            return None

    def add_breadcrumb(
        self,
        message: str,
        category: str = "custom",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Add a breadcrumb for error context.

        Args:
            message: Breadcrumb message
            category: Category (navigation, http, db, custom, etc.)
            level: Level (debug, info, warning, error)
            data: Additional data
        """
        if not self.enabled:
            return

        try:
            self.sentry.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data or {}
            )
        except Exception as e:
            logger.error(f"Failed to add breadcrumb: {e}", exc_info=True)


# Global error tracker instance
error_tracker = ErrorTracker()


def initialize_error_tracking(
    dsn: Optional[str] = None,
    environment: str = None,
    release: Optional[str] = None
):
    """
    Initialize error tracking.

    Usage:
        from .errors.error_tracking import initialize_error_tracking
        initialize_error_tracking(environment="production")
    """
    # Determine environment
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "production")

    error_tracker.initialize(
        dsn=dsn,
        environment=environment,
        release=release
    )


# Convenience functions
def capture_exception(error: Exception, **kwargs):
    """Capture an exception."""
    error_tracker.capture_exception(error, **kwargs)


def capture_message(message: str, **kwargs):
    """Capture a message."""
    error_tracker.capture_message(message, **kwargs)


def set_user(user_id: str, **kwargs):
    """Set user context."""
    error_tracker.set_user(user_id, **kwargs)


def add_breadcrumb(message: str, **kwargs):
    """Add a breadcrumb."""
    error_tracker.add_breadcrumb(message, **kwargs)

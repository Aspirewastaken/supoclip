"""
Error handling module for SupoClip.

Provides:
- Custom exception classes with error codes
- FastAPI exception handlers
- Error logging middleware
- Circuit breaker pattern for external services
- Sentry integration for error tracking
- Retry utilities with exponential backoff
"""

# Custom exceptions
from .custom_exceptions import (
    # Base
    BaseSupoClipException,
    ErrorCode,

    # Video processing
    VideoProcessingError,
    VideoDownloadError,
    VideoNotFoundError,
    VideoFormatError,
    VideoTooLargeError,
    VideoTooShortError,
    VideoCorruptedError,
    ClipGenerationError,

    # Transcription
    TranscriptionError,
    AssemblyAIError,
    TranscriptionTimeoutError,
    TranscriptionRateLimitError,
    TranscriptionQuotaError,

    # AI/LLM
    AIError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMQuotaError,
    InvalidAIResponseError,

    # Database
    DatabaseError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
    RecordNotFoundError,
    DuplicateRecordError,

    # External services
    ExternalServiceError,
    YouTubeAPIError,
    StorageError,
    NetworkError,
    ServiceUnavailableError,

    # Workers
    WorkerError,
    QueueError,
    TaskTimeoutError,
    TaskCancelledError,
    TaskNotFoundError,

    # Files
    FileError,
    FileNotFoundError,
    FileReadError,
    FileWriteError,
    StorageFullError,
    InvalidFileTypeError,

    # Users/Auth
    UserError,
    UserNotFoundError,
    InvalidCredentialsError,
    SessionExpiredError,
    PermissionDeniedError,

    # Utility functions
    is_retryable_error,
    is_non_retryable_error,
    RETRYABLE_EXCEPTIONS,
    NON_RETRYABLE_EXCEPTIONS,
)

# Error handlers
from .error_handlers import (
    register_error_handlers,
    create_error_response,
)

# Middleware
from .error_middleware import (
    setup_error_middleware,
    ErrorLoggingMiddleware,
    RequestContextMiddleware,
    PerformanceMonitoringMiddleware,
    ErrorRecoveryMiddleware,
)

# Circuit breaker
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    get_all_circuit_breaker_stats,
    # Pre-configured breakers
    assemblyai_breaker,
    llm_breaker,
    youtube_breaker,
    database_breaker,
)

# Error tracking
from .error_tracking import (
    error_tracker,
    initialize_error_tracking,
    capture_exception,
    capture_message,
    set_user,
    add_breadcrumb,
)

__all__ = [
    # Exceptions
    "BaseSupoClipException",
    "ErrorCode",
    "VideoProcessingError",
    "VideoDownloadError",
    "VideoNotFoundError",
    "VideoFormatError",
    "VideoTooLargeError",
    "VideoTooShortError",
    "VideoCorruptedError",
    "ClipGenerationError",
    "TranscriptionError",
    "AssemblyAIError",
    "TranscriptionTimeoutError",
    "TranscriptionRateLimitError",
    "TranscriptionQuotaError",
    "AIError",
    "LLMAPIError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMQuotaError",
    "InvalidAIResponseError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseTimeoutError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "ExternalServiceError",
    "YouTubeAPIError",
    "StorageError",
    "NetworkError",
    "ServiceUnavailableError",
    "WorkerError",
    "QueueError",
    "TaskTimeoutError",
    "TaskCancelledError",
    "TaskNotFoundError",
    "FileError",
    "FileNotFoundError",
    "FileReadError",
    "FileWriteError",
    "StorageFullError",
    "InvalidFileTypeError",
    "UserError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "SessionExpiredError",
    "PermissionDeniedError",
    "is_retryable_error",
    "is_non_retryable_error",
    "RETRYABLE_EXCEPTIONS",
    "NON_RETRYABLE_EXCEPTIONS",

    # Handlers
    "register_error_handlers",
    "create_error_response",

    # Middleware
    "setup_error_middleware",
    "ErrorLoggingMiddleware",
    "RequestContextMiddleware",
    "PerformanceMonitoringMiddleware",
    "ErrorRecoveryMiddleware",

    # Circuit breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "get_all_circuit_breaker_stats",
    "assemblyai_breaker",
    "llm_breaker",
    "youtube_breaker",
    "database_breaker",

    # Error tracking
    "error_tracker",
    "initialize_error_tracking",
    "capture_exception",
    "capture_message",
    "set_user",
    "add_breadcrumb",
]

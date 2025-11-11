"""
Custom exception classes for SupoClip application.
Provides structured error handling with error codes and context.
"""

from typing import Any, Dict, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Enumeration of error codes for the application."""

    # General errors (1000-1099)
    INTERNAL_SERVER_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    NOT_FOUND = "ERR_1002"
    UNAUTHORIZED = "ERR_1003"
    FORBIDDEN = "ERR_1004"
    BAD_REQUEST = "ERR_1005"
    CONFLICT = "ERR_1006"

    # Video processing errors (2000-2099)
    VIDEO_DOWNLOAD_FAILED = "ERR_2000"
    VIDEO_PROCESSING_FAILED = "ERR_2001"
    VIDEO_NOT_FOUND = "ERR_2002"
    VIDEO_FORMAT_UNSUPPORTED = "ERR_2003"
    VIDEO_TOO_LARGE = "ERR_2004"
    VIDEO_TOO_SHORT = "ERR_2005"
    VIDEO_CORRUPTED = "ERR_2006"
    CLIP_GENERATION_FAILED = "ERR_2007"

    # Transcription errors (3000-3099)
    TRANSCRIPTION_FAILED = "ERR_3000"
    ASSEMBLYAI_API_ERROR = "ERR_3001"
    TRANSCRIPTION_TIMEOUT = "ERR_3002"
    TRANSCRIPTION_RATE_LIMITED = "ERR_3003"
    TRANSCRIPTION_QUOTA_EXCEEDED = "ERR_3004"

    # AI/LLM errors (4000-4099)
    AI_ANALYSIS_FAILED = "ERR_4000"
    LLM_API_ERROR = "ERR_4001"
    LLM_TIMEOUT = "ERR_4002"
    LLM_RATE_LIMITED = "ERR_4003"
    LLM_QUOTA_EXCEEDED = "ERR_4004"
    INVALID_AI_RESPONSE = "ERR_4005"

    # Database errors (5000-5099)
    DATABASE_ERROR = "ERR_5000"
    DATABASE_CONNECTION_ERROR = "ERR_5001"
    DATABASE_TIMEOUT = "ERR_5002"
    RECORD_NOT_FOUND = "ERR_5003"
    DUPLICATE_RECORD = "ERR_5004"

    # External service errors (6000-6099)
    EXTERNAL_SERVICE_ERROR = "ERR_6000"
    YOUTUBE_API_ERROR = "ERR_6001"
    STORAGE_ERROR = "ERR_6002"
    NETWORK_ERROR = "ERR_6003"
    SERVICE_UNAVAILABLE = "ERR_6004"

    # Worker/Queue errors (7000-7099)
    WORKER_ERROR = "ERR_7000"
    QUEUE_ERROR = "ERR_7001"
    TASK_TIMEOUT = "ERR_7002"
    TASK_CANCELLED = "ERR_7003"
    TASK_NOT_FOUND = "ERR_7004"

    # File/Storage errors (8000-8099)
    FILE_NOT_FOUND = "ERR_8000"
    FILE_READ_ERROR = "ERR_8001"
    FILE_WRITE_ERROR = "ERR_8002"
    STORAGE_FULL = "ERR_8003"
    INVALID_FILE_TYPE = "ERR_8004"

    # User/Auth errors (9000-9099)
    USER_NOT_FOUND = "ERR_9000"
    INVALID_CREDENTIALS = "ERR_9001"
    SESSION_EXPIRED = "ERR_9002"
    PERMISSION_DENIED = "ERR_9003"


class BaseSupoClipException(Exception):
    """
    Base exception class for all SupoClip exceptions.

    Attributes:
        error_code: Unique error code for this exception type
        message: Human-readable error message
        details: Additional context or details about the error
        retry_after: Optional number of seconds to wait before retrying
        http_status: HTTP status code to return to client
    """

    error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR
    http_status: int = 500

    def __init__(
        self,
        message: str,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.error_code
        self.details = details or {}
        self.retry_after = retry_after
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "type": self.__class__.__name__
            }
        }

        if self.details:
            result["error"]["details"] = self.details

        if self.retry_after:
            result["error"]["retry_after"] = self.retry_after

        return result

    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"


# ============================================================================
# Video Processing Exceptions
# ============================================================================

class VideoProcessingError(BaseSupoClipException):
    """Base class for video processing errors."""
    error_code = ErrorCode.VIDEO_PROCESSING_FAILED
    http_status = 422


class VideoDownloadError(VideoProcessingError):
    """Error downloading video from source."""
    error_code = ErrorCode.VIDEO_DOWNLOAD_FAILED


class VideoNotFoundError(VideoProcessingError):
    """Video file or resource not found."""
    error_code = ErrorCode.VIDEO_NOT_FOUND
    http_status = 404


class VideoFormatError(VideoProcessingError):
    """Unsupported video format."""
    error_code = ErrorCode.VIDEO_FORMAT_UNSUPPORTED


class VideoTooLargeError(VideoProcessingError):
    """Video file exceeds size limits."""
    error_code = ErrorCode.VIDEO_TOO_LARGE
    http_status = 413


class VideoTooShortError(VideoProcessingError):
    """Video is too short to process."""
    error_code = ErrorCode.VIDEO_TOO_SHORT


class VideoCorruptedError(VideoProcessingError):
    """Video file is corrupted or unreadable."""
    error_code = ErrorCode.VIDEO_CORRUPTED


class ClipGenerationError(VideoProcessingError):
    """Error generating video clips."""
    error_code = ErrorCode.CLIP_GENERATION_FAILED


# ============================================================================
# Transcription Exceptions
# ============================================================================

class TranscriptionError(BaseSupoClipException):
    """Base class for transcription errors."""
    error_code = ErrorCode.TRANSCRIPTION_FAILED
    http_status = 422


class AssemblyAIError(TranscriptionError):
    """Error from AssemblyAI API."""
    error_code = ErrorCode.ASSEMBLYAI_API_ERROR


class TranscriptionTimeoutError(TranscriptionError):
    """Transcription request timed out."""
    error_code = ErrorCode.TRANSCRIPTION_TIMEOUT
    http_status = 504


class TranscriptionRateLimitError(TranscriptionError):
    """AssemblyAI rate limit exceeded."""
    error_code = ErrorCode.TRANSCRIPTION_RATE_LIMITED
    http_status = 429


class TranscriptionQuotaError(TranscriptionError):
    """AssemblyAI quota exceeded."""
    error_code = ErrorCode.TRANSCRIPTION_QUOTA_EXCEEDED
    http_status = 429


# ============================================================================
# AI/LLM Exceptions
# ============================================================================

class AIError(BaseSupoClipException):
    """Base class for AI/LLM errors."""
    error_code = ErrorCode.AI_ANALYSIS_FAILED
    http_status = 422


class LLMAPIError(AIError):
    """Error from LLM API."""
    error_code = ErrorCode.LLM_API_ERROR


class LLMTimeoutError(AIError):
    """LLM request timed out."""
    error_code = ErrorCode.LLM_TIMEOUT
    http_status = 504


class LLMRateLimitError(AIError):
    """LLM rate limit exceeded."""
    error_code = ErrorCode.LLM_RATE_LIMITED
    http_status = 429


class LLMQuotaError(AIError):
    """LLM quota exceeded."""
    error_code = ErrorCode.LLM_QUOTA_EXCEEDED
    http_status = 429


class InvalidAIResponseError(AIError):
    """AI returned invalid or unparseable response."""
    error_code = ErrorCode.INVALID_AI_RESPONSE


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseError(BaseSupoClipException):
    """Base class for database errors."""
    error_code = ErrorCode.DATABASE_ERROR
    http_status = 500


class DatabaseConnectionError(DatabaseError):
    """Database connection failed."""
    error_code = ErrorCode.DATABASE_CONNECTION_ERROR
    http_status = 503


class DatabaseTimeoutError(DatabaseError):
    """Database query timed out."""
    error_code = ErrorCode.DATABASE_TIMEOUT
    http_status = 504


class RecordNotFoundError(DatabaseError):
    """Database record not found."""
    error_code = ErrorCode.RECORD_NOT_FOUND
    http_status = 404


class DuplicateRecordError(DatabaseError):
    """Duplicate record exists."""
    error_code = ErrorCode.DUPLICATE_RECORD
    http_status = 409


# ============================================================================
# External Service Exceptions
# ============================================================================

class ExternalServiceError(BaseSupoClipException):
    """Base class for external service errors."""
    error_code = ErrorCode.EXTERNAL_SERVICE_ERROR
    http_status = 502


class YouTubeAPIError(ExternalServiceError):
    """Error from YouTube API or yt-dlp."""
    error_code = ErrorCode.YOUTUBE_API_ERROR


class StorageError(ExternalServiceError):
    """Error accessing storage system."""
    error_code = ErrorCode.STORAGE_ERROR


class NetworkError(ExternalServiceError):
    """Network connectivity error."""
    error_code = ErrorCode.NETWORK_ERROR
    http_status = 503


class ServiceUnavailableError(ExternalServiceError):
    """External service is unavailable."""
    error_code = ErrorCode.SERVICE_UNAVAILABLE
    http_status = 503


# ============================================================================
# Worker/Queue Exceptions
# ============================================================================

class WorkerError(BaseSupoClipException):
    """Base class for worker errors."""
    error_code = ErrorCode.WORKER_ERROR
    http_status = 500


class QueueError(WorkerError):
    """Error with job queue."""
    error_code = ErrorCode.QUEUE_ERROR


class TaskTimeoutError(WorkerError):
    """Worker task timed out."""
    error_code = ErrorCode.TASK_TIMEOUT
    http_status = 504


class TaskCancelledError(WorkerError):
    """Worker task was cancelled."""
    error_code = ErrorCode.TASK_CANCELLED
    http_status = 499


class TaskNotFoundError(WorkerError):
    """Worker task not found."""
    error_code = ErrorCode.TASK_NOT_FOUND
    http_status = 404


# ============================================================================
# File/Storage Exceptions
# ============================================================================

class FileError(BaseSupoClipException):
    """Base class for file errors."""
    error_code = ErrorCode.FILE_NOT_FOUND
    http_status = 500


class FileNotFoundError(FileError):
    """File not found."""
    error_code = ErrorCode.FILE_NOT_FOUND
    http_status = 404


class FileReadError(FileError):
    """Error reading file."""
    error_code = ErrorCode.FILE_READ_ERROR


class FileWriteError(FileError):
    """Error writing file."""
    error_code = ErrorCode.FILE_WRITE_ERROR


class StorageFullError(FileError):
    """Storage capacity exceeded."""
    error_code = ErrorCode.STORAGE_FULL
    http_status = 507


class InvalidFileTypeError(FileError):
    """Invalid file type."""
    error_code = ErrorCode.INVALID_FILE_TYPE
    http_status = 415


# ============================================================================
# User/Auth Exceptions
# ============================================================================

class UserError(BaseSupoClipException):
    """Base class for user/auth errors."""
    error_code = ErrorCode.USER_NOT_FOUND
    http_status = 401


class UserNotFoundError(UserError):
    """User not found."""
    error_code = ErrorCode.USER_NOT_FOUND
    http_status = 404


class InvalidCredentialsError(UserError):
    """Invalid login credentials."""
    error_code = ErrorCode.INVALID_CREDENTIALS


class SessionExpiredError(UserError):
    """User session expired."""
    error_code = ErrorCode.SESSION_EXPIRED


class PermissionDeniedError(UserError):
    """User lacks required permissions."""
    error_code = ErrorCode.PERMISSION_DENIED
    http_status = 403


class ValidationError(BaseSupoClipException):
    """Input validation error."""
    error_code = ErrorCode.VALIDATION_ERROR
    http_status = 400


# ============================================================================
# Retryable vs Non-Retryable Classification
# ============================================================================

# Retryable errors - can be retried with exponential backoff
RETRYABLE_EXCEPTIONS = (
    NetworkError,
    ServiceUnavailableError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
    TranscriptionTimeoutError,
    LLMTimeoutError,
    TaskTimeoutError,
    TranscriptionRateLimitError,
    LLMRateLimitError,
)

# Non-retryable errors - should not be retried
NON_RETRYABLE_EXCEPTIONS = (
    VideoNotFoundError,
    VideoFormatError,
    VideoCorruptedError,
    InvalidCredentialsError,
    PermissionDeniedError,
    RecordNotFoundError,
    InvalidAIResponseError,
    ValidationError,
)


def is_retryable_error(error: Exception) -> bool:
    """Check if an error should be retried."""
    return isinstance(error, RETRYABLE_EXCEPTIONS)


def is_non_retryable_error(error: Exception) -> bool:
    """Check if an error should NOT be retried."""
    return isinstance(error, NON_RETRYABLE_EXCEPTIONS)

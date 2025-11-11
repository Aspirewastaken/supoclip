"""
Error Scenario Tests for SupoClip
Tests various failure conditions and error handling mechanisms.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.errors import (
    VideoDownloadError,
    YouTubeAPIError,
    VideoNotFoundError,
    VideoTooLargeError,
    TranscriptionError,
    AssemblyAIError,
    TranscriptionQuotaError,
    LLMAPIError,
    LLMRateLimitError,
    DatabaseConnectionError,
    StorageFullError,
    CircuitBreakerOpenError,
    youtube_breaker,
    llm_breaker,
    assemblyai_breaker,
    database_breaker,
)


class TestYouTubeErrors:
    """Test YouTube download error scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_youtube_url(self):
        """Test that invalid URLs raise VideoNotFoundError."""
        from src.youtube_utils import download_youtube_video

        with pytest.raises(VideoNotFoundError) as exc_info:
            await download_youtube_video("https://youtube.com/watch?v=invalid")

        assert exc_info.value.error_code.value == "ERR_2002"
        assert "Could not extract video ID" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_video_too_long(self):
        """Test that videos exceeding duration limit raise VideoTooLargeError."""
        from src.youtube_utils import download_youtube_video

        # Mock get_youtube_video_info to return a 2-hour video
        with patch('src.youtube_utils.get_youtube_video_info') as mock_info:
            mock_info.return_value = {
                'id': 'test123',
                'title': 'Very Long Video',
                'duration': 7200,  # 2 hours
            }

            with pytest.raises(VideoTooLargeError) as exc_info:
                await download_youtube_video("https://youtube.com/watch?v=test123")

            assert exc_info.value.error_code.value == "ERR_2004"
            assert "exceeds 1 hour limit" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_youtube_api_failure(self):
        """Test YouTube API failure handling."""
        from src.youtube_utils import get_youtube_video_info
        import yt_dlp

        # Mock yt_dlp to raise DownloadError
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.extract_info.side_effect = \
                yt_dlp.utils.DownloadError("HTTP 403: Forbidden")

            with pytest.raises(YouTubeAPIError) as exc_info:
                await get_youtube_video_info("https://youtube.com/watch?v=test123")

            assert exc_info.value.error_code.value == "ERR_6001"

    @pytest.mark.asyncio
    async def test_youtube_circuit_breaker_opens(self):
        """Test that circuit breaker opens after threshold failures."""
        from src.youtube_utils import download_youtube_video

        # Reset circuit breaker
        youtube_breaker.reset()

        # Simulate multiple failures
        with patch('src.youtube_utils.get_youtube_video_info') as mock_info:
            mock_info.side_effect = YouTubeAPIError("Service unavailable")

            # Cause failures to exceed threshold (3 for youtube_breaker)
            for _ in range(3):
                try:
                    await download_youtube_video("https://youtube.com/watch?v=test")
                except:
                    pass

            # Circuit should now be open
            assert youtube_breaker.state.value == "open"

            # Next call should fail fast with CircuitBreakerOpenError
            with pytest.raises(CircuitBreakerOpenError):
                await download_youtube_video("https://youtube.com/watch?v=test")


class TestTranscriptionErrors:
    """Test transcription error scenarios."""

    def test_assemblyai_quota_exceeded(self):
        """Test AssemblyAI quota exceeded error."""
        from src.errors import TranscriptionQuotaError

        error = TranscriptionQuotaError(
            message="Monthly transcription quota exceeded",
            details={"quota_used": 1000, "quota_limit": 1000},
            retry_after=3600
        )

        assert error.error_code.value == "ERR_3004"
        assert error.http_status == 429
        assert error.retry_after == 3600

    def test_assemblyai_rate_limit(self):
        """Test AssemblyAI rate limiting."""
        from src.errors import TranscriptionRateLimitError

        error = TranscriptionRateLimitError(
            message="Rate limit exceeded, try again later",
            retry_after=60
        )

        assert error.error_code.value == "ERR_3003"
        assert error.http_status == 429
        assert error.retry_after == 60

    @pytest.mark.asyncio
    async def test_transcription_circuit_breaker(self):
        """Test circuit breaker for transcription service."""
        # Reset circuit breaker
        assemblyai_breaker.reset()

        # Simulate failures
        async def failing_transcribe():
            raise AssemblyAIError("Service unavailable")

        # Exceed threshold (5 for assemblyai_breaker)
        for _ in range(5):
            try:
                await assemblyai_breaker.call(failing_transcribe)
            except:
                pass

        # Circuit should be open
        assert assemblyai_breaker.state.value == "open"


class TestLLMErrors:
    """Test LLM/AI error scenarios."""

    def test_llm_rate_limit(self):
        """Test LLM rate limit error."""
        from src.errors import LLMRateLimitError

        error = LLMRateLimitError(
            message="OpenRouter rate limit exceeded",
            details={"requests_per_minute": 60, "retry_after": 30},
            retry_after=30
        )

        assert error.error_code.value == "ERR_4003"
        assert error.http_status == 429

    def test_invalid_ai_response(self):
        """Test invalid AI response handling."""
        from src.errors import InvalidAIResponseError

        error = InvalidAIResponseError(
            message="AI returned unparseable response",
            details={"raw_response": "invalid json"}
        )

        assert error.error_code.value == "ERR_4005"

    @pytest.mark.asyncio
    async def test_llm_circuit_breaker(self):
        """Test circuit breaker for LLM service."""
        # Reset circuit breaker
        llm_breaker.reset()

        async def failing_llm_call():
            raise LLMAPIError("Model timeout")

        # Exceed threshold (5 for llm_breaker)
        for _ in range(5):
            try:
                await llm_breaker.call(failing_llm_call)
            except:
                pass

        # Circuit should be open
        assert llm_breaker.state.value == "open"


class TestDatabaseErrors:
    """Test database error scenarios."""

    def test_connection_error(self):
        """Test database connection error."""
        from src.errors import DatabaseConnectionError

        error = DatabaseConnectionError(
            message="Could not connect to PostgreSQL",
            details={"host": "localhost", "port": 5432}
        )

        assert error.error_code.value == "ERR_5001"
        assert error.http_status == 503

    def test_duplicate_record(self):
        """Test duplicate record error."""
        from src.errors import DuplicateRecordError

        error = DuplicateRecordError(
            message="User with this email already exists",
            details={"field": "email", "value": "test@example.com"}
        )

        assert error.error_code.value == "ERR_5004"
        assert error.http_status == 409

    @pytest.mark.asyncio
    async def test_database_circuit_breaker(self):
        """Test circuit breaker for database."""
        # Reset circuit breaker
        database_breaker.reset()

        async def failing_query():
            raise DatabaseConnectionError("Connection timeout")

        # Exceed threshold (10 for database_breaker)
        for _ in range(10):
            try:
                await database_breaker.call(failing_query)
            except:
                pass

        # Circuit should be open
        assert database_breaker.state.value == "open"


class TestStorageErrors:
    """Test storage/file error scenarios."""

    def test_storage_full(self):
        """Test storage full error."""
        from src.errors import StorageFullError

        error = StorageFullError(
            message="Disk space exhausted, cannot save clips",
            details={"available_mb": 0, "required_mb": 500}
        )

        assert error.error_code.value == "ERR_8003"
        assert error.http_status == 507

    def test_file_not_found(self):
        """Test file not found error."""
        from src.errors import FileNotFoundError as SupoClipFileNotFoundError

        error = SupoClipFileNotFoundError(
            message="Video file not found",
            details={"path": "/tmp/missing.mp4"}
        )

        assert error.error_code.value == "ERR_8000"
        assert error.http_status == 404


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry with exponential backoff."""
        from src.errors.error_recovery import retry_with_recovery

        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await retry_with_recovery(
            flaky_function,
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=2.0
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        """Test fallback mechanism when function fails."""
        from src.errors.error_recovery import retry_with_recovery

        async def always_fails():
            raise Exception("Always fails")

        async def fallback_func():
            return "fallback_value"

        result = await retry_with_recovery(
            always_fails,
            max_attempts=2,
            initial_delay=0.1,
            fallback=fallback_func
        )

        assert result == "fallback_value"

    @pytest.mark.asyncio
    async def test_default_value_recovery(self):
        """Test default value when all recovery fails."""
        from src.errors.error_recovery import retry_with_recovery

        async def always_fails():
            raise Exception("Always fails")

        result = await retry_with_recovery(
            always_fails,
            max_attempts=2,
            initial_delay=0.1,
            fallback_value="default"
        )

        assert result == "default"


class TestStructuredErrors:
    """Test structured error responses."""

    def test_error_to_dict(self):
        """Test error serialization to dict."""
        from src.errors import VideoDownloadError

        error = VideoDownloadError(
            message="Download failed",
            details={"video_id": "abc123", "attempt": 3},
            retry_after=30
        )

        error_dict = error.to_dict()

        assert error_dict["error"]["code"] == "ERR_2000"
        assert error_dict["error"]["message"] == "Download failed"
        assert error_dict["error"]["type"] == "VideoDownloadError"
        assert error_dict["error"]["details"]["video_id"] == "abc123"
        assert error_dict["error"]["retry_after"] == 30

    def test_retryable_classification(self):
        """Test retryable error classification."""
        from src.errors import (
            is_retryable_error,
            is_non_retryable_error,
            NetworkError,
            VideoNotFoundError,
            TranscriptionTimeoutError,
            InvalidAIResponseError,
        )

        # Retryable errors
        assert is_retryable_error(NetworkError("Network issue"))
        assert is_retryable_error(TranscriptionTimeoutError("Timeout"))

        # Non-retryable errors
        assert is_non_retryable_error(VideoNotFoundError("Not found"))
        assert is_non_retryable_error(InvalidAIResponseError("Bad response"))


class TestCircuitBreakerRecovery:
    """Test circuit breaker recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_half_open_recovery(self):
        """Test circuit breaker recovery from HALF_OPEN state."""
        from src.errors.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.5,  # Short timeout for testing
            half_open_max_calls=2,
            name="test_breaker"
        )

        # Cause failures to open circuit
        async def failing_func():
            raise Exception("Failure")

        for _ in range(2):
            try:
                await breaker.call(failing_func)
            except:
                pass

        assert breaker.state.value == "open"

        # Wait for recovery timeout
        await asyncio.sleep(0.6)

        # Next call should transition to HALF_OPEN
        try:
            await breaker.call(failing_func)
        except:
            pass

        assert breaker.state.value == "half_open" or breaker.state.value == "open"

    @pytest.mark.asyncio
    async def test_successful_recovery(self):
        """Test successful recovery closes circuit."""
        from src.errors.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.5,
            name="test_recovery"
        )

        # Cause failures
        async def failing_func():
            raise Exception("Failure")

        for _ in range(2):
            try:
                await breaker.call(failing_func)
            except:
                pass

        assert breaker.state.value == "open"

        # Wait for recovery
        await asyncio.sleep(0.6)

        # Successful call should close circuit
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state.value == "closed"


# Integration test markers
@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for full error scenarios (requires external services)."""

    @pytest.mark.asyncio
    async def test_full_video_processing_error_flow(self):
        """Test complete error flow from download to clip generation.

        This test requires:
        - Running backend server
        - Valid API keys
        - Network connectivity
        """
        # This is a placeholder for full integration testing
        # In practice, use staging environment with test data
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

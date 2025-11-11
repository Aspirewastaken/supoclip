# Error Handling Quick Reference Card

## Import Error Types

```python
from errors import (
    # Video errors
    VideoDownloadError,
    VideoNotFoundError,
    VideoTooLargeError,
    ClipGenerationError,

    # Transcription errors
    TranscriptionError,
    AssemblyAIError,
    TranscriptionQuotaError,
    TranscriptionRateLimitError,

    # AI/LLM errors
    LLMAPIError,
    LLMRateLimitError,
    InvalidAIResponseError,

    # Database errors
    DatabaseConnectionError,
    DatabaseTimeoutError,
    RecordNotFoundError,

    # Storage errors
    StorageFullError,
    FileNotFoundError,
    FileWriteError,

    # Circuit breakers
    youtube_breaker,
    assemblyai_breaker,
    llm_breaker,
    database_breaker,
    CircuitBreakerOpenError,

    # Utilities
    add_breadcrumb,
    capture_exception,
    set_user,
)
```

## Raise Custom Exceptions

```python
# Video not found
raise VideoNotFoundError(
    message="Video not found or invalid URL",
    details={"url": url, "video_id": video_id}
)

# Download failed
raise VideoDownloadError(
    message="Failed to download video after 3 attempts",
    details={"url": url, "attempts": 3, "last_error": str(e)},
    cause=e
)

# Video too large
raise VideoTooLargeError(
    message="Video duration exceeds 1 hour limit",
    details={"duration": duration, "limit": 3600}
)

# Rate limit with retry
raise LLMRateLimitError(
    message="OpenRouter rate limit exceeded",
    details={"model": model},
    retry_after=60  # Seconds to wait
)

# Disk full
raise StorageFullError(
    message="Cannot save clips, disk space exhausted",
    details={"available_mb": 0, "required_mb": 500}
)
```

## Use Circuit Breakers

```python
# Protect YouTube downloads
async def download_video(url: str):
    async def _download():
        # Download logic here
        return video_path

    try:
        return await youtube_breaker.call(_download)
    except CircuitBreakerOpenError as e:
        # Service unavailable, use fallback or inform user
        logger.warning(f"YouTube unavailable, retry after {e.retry_after}s")
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable. Retry after {e.retry_after}s"
        )

# Protect LLM calls
async def call_llm(prompt: str):
    async def _call():
        # LLM API call here
        return response

    return await llm_breaker.call(_call)

# Protect AssemblyAI calls
async def transcribe_video(video_path: str):
    async def _transcribe():
        # Transcription logic here
        return transcript

    return await assemblyai_breaker.call(_transcribe)
```

## Structured Logging

```python
# Log with context
logger.info(
    "Processing video clip",
    extra={
        "task_id": task.id,
        "user_id": user_id,
        "clip_number": 1,
        "start_time": 10.5,
        "end_time": 25.3
    }
)

# Log error with details
logger.error(
    "Download failed",
    extra={
        "video_id": video_id,
        "attempt": attempt,
        "error": str(e)
    },
    exc_info=True  # Include stack trace
)

# Log warning
logger.warning(
    "Video duration exceeds recommended limit",
    extra={
        "video_id": video_id,
        "duration": duration
    }
)
```

## Add Breadcrumbs (for Sentry)

```python
# Track operation steps
add_breadcrumb(
    message="Starting video download",
    category="youtube",
    data={"video_id": video_id, "url": url}
)

add_breadcrumb(
    message="Transcription started",
    category="transcription",
    data={"video_path": video_path}
)

add_breadcrumb(
    message="Generated clip",
    category="clip_generation",
    data={"clip_number": 1, "duration": 15.5}
)
```

## Error Response Format

All errors return structured JSON:

```json
{
  "error": {
    "code": "ERR_2000",
    "message": "User-friendly error message",
    "type": "VideoDownloadError",
    "details": {
      "video_id": "abc123",
      "additional": "context"
    }
  },
  "retry_after": 30  // Optional, for rate limits
}
```

## Error Code Ranges

| Range | Category |
|-------|----------|
| 1000-1099 | General errors (validation, not found, etc.) |
| 2000-2099 | Video processing errors |
| 3000-3099 | Transcription errors (AssemblyAI) |
| 4000-4099 | AI/LLM errors |
| 5000-5099 | Database errors |
| 6000-6099 | External service errors |
| 7000-7099 | Worker/queue errors |
| 8000-8099 | File/storage errors |
| 9000-9099 | User/auth errors |

## Common Error Codes

| Code | Error | HTTP Status |
|------|-------|-------------|
| ERR_2000 | Video download failed | 422 |
| ERR_2002 | Video not found | 404 |
| ERR_2004 | Video too large | 413 |
| ERR_3000 | Transcription failed | 422 |
| ERR_3003 | Transcription rate limited | 429 |
| ERR_3004 | Transcription quota exceeded | 429 |
| ERR_4001 | LLM API error | 422 |
| ERR_4003 | LLM rate limited | 429 |
| ERR_5001 | Database connection error | 503 |
| ERR_6001 | YouTube API error | 502 |
| ERR_8003 | Storage full | 507 |

## Check Circuit Breaker Health

```bash
# HTTP endpoint
curl http://localhost:8000/health/circuit-breakers

# In Python
from errors import get_all_circuit_breaker_stats
stats = get_all_circuit_breaker_stats()
```

## Circuit Breaker States

- **CLOSED**: Normal operation (all requests pass through)
- **OPEN**: Service failing (requests blocked, fast-fail)
- **HALF_OPEN**: Testing recovery (limited requests allowed)

## Retry with Fallback

```python
from errors.error_recovery import retry_with_recovery

# With fallback function
result = await retry_with_recovery(
    risky_operation,
    max_attempts=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    fallback=get_cached_result
)

# With default value
result = await retry_with_recovery(
    risky_operation,
    max_attempts=3,
    fallback_value=[]
)
```

## Test Error Scenarios

```bash
# Invalid YouTube URL
curl -X POST http://localhost:8000/start \
  -H "user_id: test" \
  -H "Content-Type: application/json" \
  -d '{"source": {"url": "https://youtube.com/watch?v=invalid"}}'

# Missing user ID
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{"source": {"url": "https://youtube.com/watch?v=valid"}}'
```

## Run Tests

```bash
# All error tests
pytest tests/test_error_scenarios.py -v

# Specific test class
pytest tests/test_error_scenarios.py::TestYouTubeErrors -v

# Specific test
pytest tests/test_error_scenarios.py::TestYouTubeErrors::test_invalid_youtube_url -v
```

## Monitor Logs

```bash
# Watch logs
tail -f logs/backend.log

# Filter by request ID
grep "550e8400-e29b-41d4-a716-446655440000" logs/backend.log

# Filter by error level
grep "ERROR" logs/backend.log

# Filter by module
grep "youtube_utils" logs/backend.log
```

## Environment Variables

Add to `.env`:

```bash
# Error Tracking (Optional)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
ENVIRONMENT=production
APP_VERSION=1.0.0
```

## Best Practices

1. **Always use typed exceptions** instead of generic Exception
2. **Add context to logs** with `extra={}` parameter
3. **Use breadcrumbs** for complex multi-step operations
4. **Handle circuit breaker errors** with fallbacks
5. **Set user context** at request start with `set_user()`
6. **Include stack traces** with `exc_info=True` for errors
7. **Use retry_after** for rate limit errors
8. **Test error scenarios** before deploying

## Common Patterns

### Pattern 1: Protected External API Call

```python
from errors import youtube_breaker, YouTubeAPIError, add_breadcrumb

async def fetch_from_youtube(url: str):
    add_breadcrumb("Fetching YouTube data", "youtube", {"url": url})

    async def _fetch():
        try:
            return await youtube_api.get(url)
        except Exception as e:
            logger.error(f"YouTube API failed: {e}", exc_info=True)
            raise YouTubeAPIError(
                message="Failed to fetch YouTube data",
                details={"url": url, "error": str(e)},
                cause=e
            )

    return await youtube_breaker.call(_fetch)
```

### Pattern 2: Retry with Logging

```python
from errors.error_recovery import retry_with_recovery

async def risky_operation():
    result = await retry_with_recovery(
        actual_operation,
        max_attempts=3,
        initial_delay=1.0,
        backoff_factor=2.0
    )
    return result
```

### Pattern 3: Graceful Degradation

```python
from errors.error_recovery import with_fallback

@with_fallback(fallback_value=[])
async def get_recommended_clips(video_id: str):
    # May fail, returns [] if it does
    return await ai_service.recommend(video_id)
```

## Quick Links

- **Full Documentation**: `/backend/ERROR_HANDLING_GUIDE.md`
- **Implementation Summary**: `/backend/ERROR_HANDLING_IMPLEMENTATION_SUMMARY.md`
- **Test Suite**: `/backend/tests/test_error_scenarios.py`
- **Error Module**: `/backend/src/errors/`

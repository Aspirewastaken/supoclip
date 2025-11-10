# SupoClip Error Handling System

## Overview

Comprehensive error handling architecture for SupoClip with structured exceptions, circuit breakers, retry logic, error tracking, and recovery mechanisms.

## Features

### 1. **Structured Exception System**
- ✅ Custom exception classes with error codes
- ✅ HTTP status code mapping
- ✅ Contextual error details
- ✅ Error categorization (retryable vs non-retryable)
- ✅ Consistent error response format

### 2. **Circuit Breaker Pattern**
- ✅ Prevents cascade failures
- ✅ Auto-recovery testing
- ✅ Pre-configured for external services (YouTube, AssemblyAI, LLM)
- ✅ State monitoring and statistics
- ✅ Configurable failure thresholds and recovery timeouts

### 3. **Retry Logic**
- ✅ Exponential backoff
- ✅ Configurable max attempts
- ✅ Exception-specific retry policies
- ✅ Integration with circuit breakers

### 4. **Error Tracking (Sentry)**
- ✅ Centralized error logging
- ✅ Performance monitoring
- ✅ User context tracking
- ✅ Breadcrumb trails for debugging
- ✅ Alert notifications

### 5. **Error Recovery**
- ✅ Fallback strategies
- ✅ Graceful degradation
- ✅ Timeout handling
- ✅ Default value fallbacks
- ✅ Cached data fallbacks

### 6. **Request Middleware**
- ✅ Request/response logging
- ✅ Correlation IDs
- ✅ Performance monitoring
- ✅ Slow request detection
- ✅ Error context enrichment

## Architecture

```
errors/
├── __init__.py                 # Public API exports
├── custom_exceptions.py        # Exception class definitions
├── error_handlers.py           # FastAPI exception handlers
├── error_middleware.py         # Request/response middleware
├── circuit_breaker.py          # Circuit breaker implementation
├── error_tracking.py           # Sentry integration
├── error_recovery.py           # Recovery strategies
├── README.md                   # This file
├── INTEGRATION_GUIDE.md        # Integration instructions
└── EXAMPLES.md                 # Usage examples
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
uv add sentry-sdk[fastapi]
uv sync
```

### 2. Configure Environment

Add to `.env`:

```bash
# Optional: Sentry error tracking
SENTRY_DSN=https://your-dsn@sentry.io/project
ENVIRONMENT=production
APP_VERSION=1.0.0
```

### 3. Integrate into main.py

```python
from .errors import (
    register_error_handlers,
    setup_error_middleware,
    initialize_error_tracking,
)

# Initialize in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Sentry
    initialize_error_tracking()

    await init_db()
    yield
    await close_db()

app = FastAPI(lifespan=lifespan)

# Register error handlers and middleware
register_error_handlers(app)
setup_error_middleware(app)

# Add other middleware
app.add_middleware(CORSMiddleware, ...)
```

### 4. Use in Your Code

```python
from ..errors import (
    VideoDownloadError,
    youtube_breaker,
    capture_exception,
)
from ..utils.retry_utils import async_retry

@youtube_breaker  # Circuit breaker protection
@async_retry(max_attempts=3, delay=2)  # Retry with backoff
async def download_video(url: str) -> str:
    try:
        return await yt_dlp.download(url)
    except Exception as e:
        raise VideoDownloadError(
            message=f"Download failed: {url}",
            details={"url": url},
            cause=e
        )
```

## Error Codes

All errors include structured error codes for easy identification:

| Code Range | Category | Examples |
|------------|----------|----------|
| `ERR_1000-1099` | General | Internal server error, validation error, not found |
| `ERR_2000-2099` | Video Processing | Download failed, format unsupported, clip generation |
| `ERR_3000-3099` | Transcription | AssemblyAI error, timeout, rate limited |
| `ERR_4000-4099` | AI/LLM | Analysis failed, timeout, quota exceeded |
| `ERR_5000-5099` | Database | Connection error, timeout, record not found |
| `ERR_6000-6099` | External Services | YouTube API, storage error, network error |
| `ERR_7000-7099` | Workers/Queue | Worker error, task timeout, task cancelled |
| `ERR_8000-8099` | Files/Storage | File not found, read/write error, storage full |
| `ERR_9000-9099` | Users/Auth | User not found, invalid credentials, session expired |

## Error Response Format

All API errors return consistent JSON structure:

```json
{
  "error": {
    "code": "ERR_2000",
    "message": "Failed to download video",
    "type": "VideoDownloadError",
    "details": {
      "url": "https://youtube.com/watch?v=...",
      "error": "HTTP 403 Forbidden"
    }
  }
}
```

For rate-limited errors:

```json
{
  "error": {
    "code": "ERR_4003",
    "message": "LLM rate limit exceeded",
    "type": "LLMRateLimitError",
    "retry_after": 60
  }
}
```

## Circuit Breakers

### Pre-configured Breakers

```python
from ..errors import (
    assemblyai_breaker,  # AssemblyAI transcription
    llm_breaker,         # LLM/AI analysis
    youtube_breaker,     # YouTube downloads
    database_breaker,    # Database operations
)

@assemblyai_breaker
async def transcribe(video_path: str):
    # Protected by circuit breaker
    return await assemblyai.transcribe(video_path)
```

### Circuit Breaker States

- **CLOSED** (Normal): All requests pass through
- **OPEN** (Failing): Requests are blocked, fast-fail
- **HALF_OPEN** (Testing): Limited requests allowed to test recovery

### Monitoring Circuit Breakers

```bash
# API endpoint to check circuit breaker health
GET /health/circuit-breakers

# Response
{
  "assemblyai": {
    "state": "closed",
    "stats": {
      "total_calls": 150,
      "successful_calls": 148,
      "failed_calls": 2,
      "success_rate": 0.987,
      "failure_rate": 0.013
    }
  }
}
```

## Retry Strategies

### Automatic Retry

```python
from ..utils.retry_utils import async_retry

@async_retry(
    max_attempts=3,      # Retry up to 3 times
    delay=2.0,           # Initial delay: 2 seconds
    backoff=2.0,         # Multiply delay by 2 each time
    exceptions=(NetworkError, TimeoutError)  # Only retry these
)
async def fetch_data(url: str):
    # Will automatically retry on NetworkError or TimeoutError
    return await httpx.get(url)
```

### Retry with Recovery

```python
from ..errors.error_recovery import retry_with_recovery

async def fetch_with_fallback(url: str):
    return await retry_with_recovery(
        fetch_data,
        url,
        max_attempts=3,
        initial_delay=1.0,
        fallback=lambda: get_cached_data(url),  # Fallback function
        fallback_value={}  # Default value if all fails
    )
```

## Error Recovery Patterns

### 1. Fallback Function

```python
from ..errors.error_recovery import with_fallback

@with_fallback(fallback_func=get_cached_result)
async def expensive_operation():
    # If this fails, automatically call get_cached_result()
    return await compute_expensive_result()
```

### 2. Default Value

```python
@with_fallback(fallback_value=[])
async def get_recommendations():
    # If this fails, return []
    return await ai_recommendations()
```

### 3. Graceful Degradation

```python
from ..errors.error_recovery import GracefulDegradation

async def process_video():
    clips = await generate_clips()  # Must succeed

    # Optional feature - can fail gracefully
    with GracefulDegradation() as gd:
        thumbnails = await generate_thumbnails(clips)

    if gd.degraded:
        logger.warning("Thumbnails unavailable, continuing without them")

    return clips
```

### 4. Timeout with Fallback

```python
from ..errors.error_recovery import with_timeout_recovery

async def process_with_timeout():
    return await with_timeout_recovery(
        slow_processing,
        timeout=30.0,  # 30 second timeout
        fallback=quick_fallback  # Use this if timeout
    )
```

## Sentry Integration

### Setup

```python
from ..errors import (
    initialize_error_tracking,
    capture_exception,
    capture_message,
    set_user,
    add_breadcrumb,
)

# Initialize (in lifespan or startup)
initialize_error_tracking(
    environment="production",
    release="1.0.0"
)
```

### Capture Exceptions

```python
try:
    result = await risky_operation()
except Exception as e:
    capture_exception(
        e,
        context={
            "operation": "risky_operation",
            "additional_data": "custom info"
        },
        level="error"
    )
    raise
```

### Add Breadcrumbs

```python
# Add context for debugging
add_breadcrumb("Downloading video", category="video", data={"url": url})
add_breadcrumb("Processing complete", category="video", level="info")
```

### Set User Context

```python
# Track errors by user
set_user(user_id="user_123", email="user@example.com")
```

## Best Practices

### 1. Use Specific Exceptions

❌ **Bad:**
```python
raise Exception("Video not found")
```

✅ **Good:**
```python
raise VideoNotFoundError(
    message="Video file not found",
    details={"path": video_path}
)
```

### 2. Add Context to Errors

❌ **Bad:**
```python
raise VideoDownloadError("Download failed")
```

✅ **Good:**
```python
raise VideoDownloadError(
    message="Failed to download YouTube video",
    details={
        "url": url,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    },
    cause=e  # Include original exception
)
```

### 3. Use Circuit Breakers for External Services

❌ **Bad:**
```python
async def transcribe(video):
    return await assemblyai.transcribe(video)  # No protection
```

✅ **Good:**
```python
@assemblyai_breaker  # Circuit breaker
@async_retry(max_attempts=3)  # Retry
async def transcribe(video):
    return await assemblyai.transcribe(video)
```

### 4. Provide Fallbacks for Non-Critical Features

❌ **Bad:**
```python
# Fails entire process if thumbnails fail
thumbnails = await generate_thumbnails(clips)
```

✅ **Good:**
```python
# Continue without thumbnails if generation fails
with GracefulDegradation() as gd:
    thumbnails = await generate_thumbnails(clips)

if gd.degraded:
    logger.warning("Proceeding without thumbnails")
```

### 5. Set User Context

```python
@app.middleware("http")
async def set_user_context(request: Request, call_next):
    user_id = request.headers.get("user_id")
    if user_id:
        set_user(user_id)  # Track errors by user

    return await call_next(request)
```

## Testing

### Test Circuit Breaker

```python
import pytest
from ..errors import youtube_breaker, CircuitBreakerOpenError

async def test_circuit_breaker():
    # Reset breaker
    youtube_breaker.reset()

    # Simulate failures
    for _ in range(5):
        with pytest.raises(Exception):
            await youtube_breaker.call(failing_function)

    # Circuit should be open
    assert youtube_breaker.state == CircuitState.OPEN

    # Calls should be blocked
    with pytest.raises(CircuitBreakerOpenError):
        await youtube_breaker.call(any_function)
```

### Test Custom Exceptions

```python
def test_custom_exception():
    error = VideoNotFoundError(
        message="Video not found",
        details={"video_id": "abc123"}
    )

    # Check error code
    assert error.error_code == ErrorCode.VIDEO_NOT_FOUND

    # Check HTTP status
    assert error.http_status == 404

    # Check serialization
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "ERR_2002"
    assert error_dict["error"]["message"] == "Video not found"
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Error Rate**: Percentage of failed requests
2. **Circuit Breaker State**: Open/closed state of critical services
3. **Retry Attempts**: Average number of retries per operation
4. **Error Types**: Distribution of error codes
5. **Response Times**: 95th/99th percentile response times

### Sentry Alerts

Configure alerts in Sentry for:
- Error rate exceeds threshold
- Critical errors (ERR_5xxx database, ERR_6xxx external services)
- Circuit breakers opening
- Slow requests (>5s)

## Migration Guide

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for step-by-step migration instructions.

## Examples

See [EXAMPLES.md](./EXAMPLES.md) for comprehensive usage examples including:
- Basic exception handling
- Circuit breaker patterns
- Retry strategies
- Error recovery
- Worker error handling
- API endpoint patterns
- Sentry integration

## Support

For issues or questions:
1. Check [EXAMPLES.md](./EXAMPLES.md) for common patterns
2. Review [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for setup
3. Check circuit breaker stats: `GET /health/circuit-breakers`
4. Review Sentry dashboard for production errors

## License

Part of the SupoClip project. See project LICENSE for details.

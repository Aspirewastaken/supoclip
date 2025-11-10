# Error Handling Integration Guide

## Overview

This guide shows how to integrate the comprehensive error handling system into your SupoClip application.

## 1. Update main.py

Add error handling initialization to your FastAPI app:

```python
from .errors import (
    register_error_handlers,
    setup_error_middleware,
    initialize_error_tracking,
    get_all_circuit_breaker_stats,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize error tracking (Sentry)
        initialize_error_tracking(
            environment=os.getenv("ENVIRONMENT", "production")
        )

        await init_db()
        yield
    finally:
        await close_db()

app = FastAPI(
    title="SupoClip API",
    description="Python-based backend for SupoClip",
    version="0.1.0",
    lifespan=lifespan
)

# Setup error handling (ORDER MATTERS!)
# 1. Register exception handlers first
register_error_handlers(app)

# 2. Setup middleware
setup_error_middleware(app)

# 3. Add CORS and other middleware
app.add_middleware(CORSMiddleware, ...)

# Add circuit breaker stats endpoint
@app.get("/health/circuit-breakers")
async def get_circuit_breaker_health():
    """Get circuit breaker statistics."""
    return get_all_circuit_breaker_stats()
```

## 2. Update services to use custom exceptions

### Example: video_utils.py

```python
from ..errors import (
    VideoDownloadError,
    VideoNotFoundError,
    VideoProcessingError,
    youtube_breaker,  # Pre-configured circuit breaker
)
from ..utils.retry_utils import async_retry

# Use circuit breaker for external API calls
@youtube_breaker
@async_retry(max_attempts=3, delay=2, backoff=2)
async def download_youtube_video(url: str) -> str:
    """Download YouTube video with circuit breaker protection."""
    try:
        # Your download logic here
        result = yt_dlp.download(url)
        return result
    except yt_dlp.DownloadError as e:
        raise VideoDownloadError(
            message=f"Failed to download video: {url}",
            details={"url": url, "error": str(e)},
            cause=e
        )
    except Exception as e:
        raise VideoProcessingError(
            message="Unexpected error during video download",
            details={"url": url},
            cause=e
        )
```

### Example: ai.py

```python
from ..errors import (
    AIError,
    LLMAPIError,
    InvalidAIResponseError,
    llm_breaker,
)
from ..utils.retry_utils import async_retry

@llm_breaker
@async_retry(max_attempts=3, delay=2, backoff=2)
async def get_most_relevant_parts_by_transcript(transcript: str):
    """Analyze transcript with circuit breaker and retry logic."""
    try:
        result = await transcript_agent.run(f"Analyze: {transcript}")

        if not result.data:
            raise InvalidAIResponseError(
                message="AI returned empty response",
                details={"transcript_length": len(transcript)}
            )

        return result.data

    except Exception as e:
        if "rate limit" in str(e).lower():
            raise LLMRateLimitError(
                message="LLM rate limit exceeded",
                retry_after=60,
                cause=e
            )
        raise LLMAPIError(
            message="Failed to analyze transcript",
            details={"error": str(e)},
            cause=e
        )
```

## 3. Update API endpoints to use custom exceptions

```python
from ..errors import (
    UserNotFoundError,
    VideoNotFoundError,
    create_error_response,
    ErrorCode,
    capture_exception,
    set_user,
)

@app.post("/start")
async def start_task(request: Request):
    """Start a new task with proper error handling."""
    data = await request.json()
    user_id = request.headers.get("user_id")

    # Set user context for error tracking
    if user_id:
        set_user(user_id)

    # Validate user
    if not user_id:
        raise UserNotFoundError(
            message="User authentication required",
            details={"header": "user_id"}
        )

    # Check if user exists
    async with AsyncSessionLocal() as db:
        user_exists = await db.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        if not user_exists.fetchone():
            raise UserNotFoundError(
                message=f"User not found: {user_id}",
                details={"user_id": user_id}
            )

    try:
        # Your processing logic
        result = await process_video(data)
        return result

    except Exception as e:
        # Capture unexpected errors
        capture_exception(e, context={
            "endpoint": "start_task",
            "user_id": user_id,
            "data": data
        })
        raise
```

## 4. Update workers to use structured error handling

### Example: workers/tasks.py

```python
from ..errors import (
    TaskTimeoutError,
    WorkerError,
    capture_exception,
    add_breadcrumb,
)

async def process_video_task(ctx, task_id: str, ...):
    """Worker task with structured error handling."""

    # Add breadcrumbs for debugging
    add_breadcrumb(f"Starting task {task_id}", category="worker")

    try:
        # Download video
        add_breadcrumb("Downloading video", category="worker")
        video_path = await download_video(url)

        # Process video
        add_breadcrumb("Processing video", category="worker")
        result = await process_video(video_path)

        add_breadcrumb(f"Task {task_id} completed", category="worker")
        return result

    except TimeoutError as e:
        raise TaskTimeoutError(
            message=f"Task {task_id} timed out",
            details={"task_id": task_id, "timeout": ctx.get("timeout")},
            cause=e
        )
    except Exception as e:
        # Capture error with context
        capture_exception(e, context={
            "task_id": task_id,
            "worker": "process_video_task"
        })

        raise WorkerError(
            message=f"Worker task failed: {task_id}",
            details={"task_id": task_id, "error": str(e)},
            cause=e
        )
```

## 5. Environment Variables

Add to your `.env` file:

```bash
# Error Tracking (Optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production  # or staging, development
APP_VERSION=1.0.0

# Circuit Breaker Settings (Optional - defaults are provided)
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

## 6. Install Dependencies

Update `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "sentry-sdk[fastapi]>=1.40.0",  # Optional but recommended
]
```

Then run:

```bash
cd backend
uv sync
```

## 7. Testing Error Handling

```python
# Test circuit breaker
from ..errors import youtube_breaker, CircuitBreakerOpenError

try:
    result = await youtube_breaker.call(download_video, url)
except CircuitBreakerOpenError as e:
    print(f"Circuit is open, retry after {e.retry_after} seconds")

# Test custom exceptions
from ..errors import VideoNotFoundError

try:
    raise VideoNotFoundError(
        message="Video not found",
        details={"video_id": "abc123"}
    )
except VideoNotFoundError as e:
    print(e.to_dict())
    # {
    #   "error": {
    #     "code": "ERR_2002",
    #     "message": "Video not found",
    #     "type": "VideoNotFoundError",
    #     "details": {"video_id": "abc123"}
    #   }
    # }
```

## 8. Error Response Format

All errors now return consistent JSON:

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

## 9. Monitoring Circuit Breakers

Access circuit breaker statistics:

```bash
curl http://localhost:8000/health/circuit-breakers
```

Response:

```json
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
  },
  "llm": {
    "state": "half_open",
    "stats": {
      "total_calls": 50,
      "successful_calls": 45,
      "failed_calls": 5,
      "success_rate": 0.9,
      "failure_rate": 0.1
    }
  }
}
```

## 10. Best Practices

1. **Always use custom exceptions** instead of generic `Exception` or `HTTPException`
2. **Add context** to exceptions with the `details` parameter
3. **Use circuit breakers** for all external API calls (YouTube, AssemblyAI, LLMs)
4. **Use retry decorators** with exponential backoff for transient failures
5. **Set user context** at the start of each request for better error tracking
6. **Add breadcrumbs** in long-running tasks for debugging
7. **Monitor circuit breaker stats** to detect service degradation early
8. **Use Sentry** in production for centralized error tracking and alerting

## Next Steps

1. Migrate existing error handling to use custom exceptions
2. Add circuit breakers to all external service calls
3. Add retry logic to transient failure points
4. Configure Sentry for production error tracking
5. Add monitoring dashboards for circuit breaker health

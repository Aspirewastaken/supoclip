# Error Handling & Logging Enhancement Guide

## Overview

SupoClip now includes comprehensive error handling and logging infrastructure designed to:
- **Prevent cascade failures** using circuit breakers
- **Provide structured error responses** with error codes
- **Track errors centrally** via Sentry integration
- **Improve debugging** with structured logging and request IDs
- **Gracefully handle failures** with retry logic and fallbacks

## Architecture

### Components

1. **Custom Exceptions** (`backend/src/errors/custom_exceptions.py`)
   - Structured error codes (ERR_1000-ERR_9099)
   - Domain-specific exception classes
   - HTTP status code mapping
   - Retryable vs non-retryable classification

2. **Error Handlers** (`backend/src/errors/error_handlers.py`)
   - FastAPI exception handlers
   - Structured JSON error responses
   - SQLAlchemy error translation
   - Validation error formatting

3. **Error Middleware** (`backend/src/errors/error_middleware.py`)
   - Request ID generation (X-Request-ID header)
   - Performance monitoring (slow request detection)
   - Request/response logging
   - Error context enrichment

4. **Circuit Breakers** (`backend/src/errors/circuit_breaker.py`)
   - Pre-configured breakers for external services:
     - `assemblyai_breaker` - Transcription API (5 failures, 120s recovery)
     - `llm_breaker` - AI/LLM APIs (5 failures, 60s recovery)
     - `youtube_breaker` - YouTube downloads (3 failures, 30s recovery)
     - `database_breaker` - Database queries (10 failures, 10s recovery)
   - Three states: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing)
   - Automatic recovery attempts

5. **Error Tracking** (`backend/src/errors/error_tracking.py`)
   - Sentry integration for centralized monitoring
   - Performance tracing
   - User context tracking
   - Breadcrumb trails for debugging

6. **Error Recovery** (`backend/src/errors/error_recovery.py`)
   - Retry with exponential backoff
   - Fallback mechanisms
   - Graceful degradation
   - Timeout recovery

## Error Codes

### Categories

- **1000-1099**: General errors (validation, not found, unauthorized, etc.)
- **2000-2099**: Video processing errors
- **3000-3099**: Transcription errors (AssemblyAI)
- **4000-4099**: AI/LLM errors
- **5000-5099**: Database errors
- **6000-6099**: External service errors
- **7000-7099**: Worker/queue errors
- **8000-8099**: File/storage errors
- **9000-9099**: User/auth errors

### Example Error Response

```json
{
  "error": {
    "code": "ERR_2000",
    "message": "Failed to download video after 3 attempts",
    "type": "VideoDownloadError",
    "details": {
      "video_id": "dQw4w9WgXcQ",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "attempts": 3,
      "last_error": "HTTP 403: Forbidden"
    }
  },
  "retry_after": 30
}
```

## Circuit Breaker Usage

### Checking Status

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
      "success_rate": 0.9867,
      "failure_rate": 0.0133
    }
  },
  "llm": {
    "state": "closed",
    "stats": {
      "total_calls": 200,
      "successful_calls": 195,
      "failed_calls": 5,
      "success_rate": 0.975,
      "failure_rate": 0.025
    }
  },
  "youtube": {
    "state": "open",
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

### How Circuit Breakers Work

1. **CLOSED State** (Normal Operation)
   - All requests pass through
   - Failures are counted
   - When failure threshold exceeded → Opens

2. **OPEN State** (Blocking Requests)
   - Requests are immediately rejected with `CircuitBreakerOpenError`
   - Includes `retry_after` header
   - After recovery timeout → Transitions to HALF_OPEN

3. **HALF_OPEN State** (Testing Recovery)
   - Limited requests allowed (3 by default)
   - If successful → Returns to CLOSED
   - If failed → Returns to OPEN

### Example: YouTube Download with Circuit Breaker

```python
from errors import youtube_breaker, VideoDownloadError

async def download_video(url: str):
    try:
        path = await download_youtube_video(url)
        return path
    except CircuitBreakerOpenError as e:
        # Circuit is open, service unavailable
        logger.warning(f"YouTube service unavailable, retry after {e.retry_after}s")
        # Use fallback or inform user
        raise HTTPException(
            status_code=503,
            detail=f"YouTube service temporarily unavailable. Retry after {e.retry_after} seconds"
        )
    except VideoDownloadError as e:
        # Download failed after retries
        logger.error(f"Download failed: {e.message}")
        raise HTTPException(status_code=422, detail=e.message)
```

## Structured Logging

### Features

- **Request IDs**: Every request gets a unique ID (UUID)
- **Context Enrichment**: Logs include task_id, user_id, operation
- **Performance Tracking**: Request duration in milliseconds
- **Slow Request Detection**: Warnings for requests > 5 seconds

### Log Format

```
2025-11-10 15:30:45 - app.main - INFO - [uuid-request-id] - Request started: POST /start
2025-11-10 15:30:45 - app.youtube_utils - INFO - [uuid-request-id] - Starting YouTube download: https://youtube.com/watch?v=abc123
2025-11-10 15:30:50 - app.youtube_utils - INFO - [uuid-request-id] - Download successful: abc123.mp4 (125MB)
2025-11-10 15:31:20 - app.main - INFO - [uuid-request-id] - Request completed: POST /start (duration: 35000ms)
```

### Using Structured Logging

```python
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
```

## Sentry Integration

### Configuration

Add to your `.env` file:

```bash
# Error Tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production  # or staging, development
APP_VERSION=1.0.0
```

### Features Enabled

- **Error Capture**: All unhandled exceptions
- **Performance Monitoring**: Transaction traces (10% sample rate)
- **User Tracking**: Automatic user context from request headers
- **Breadcrumbs**: Trail of events leading to errors
- **Release Tracking**: Version-based error grouping
- **Integrations**:
  - FastAPI (endpoint transactions)
  - SQLAlchemy (database queries)
  - Redis (cache operations)
  - Logging (breadcrumbs from logs)

### Filtered Events

The following are NOT sent to Sentry to reduce noise:
- Validation errors (RequestValidationError)
- 404 Not Found errors
- Normal user errors (bad input, etc.)

## Error Scenarios & Testing

### 1. YouTube Download Fails

**Scenario**: YouTube blocks requests or video is unavailable

**Expected Behavior**:
```
1. First attempt fails → Retry with 1s backoff
2. Second attempt fails → Retry with 2s backoff
3. Third attempt fails → Circuit breaker opens
4. Returns VideoDownloadError (ERR_2000)
5. Client receives 422 with structured error
```

**Test**:
```bash
# Use invalid YouTube URL
curl -X POST http://localhost:8000/start \
  -H "user_id: test-user" \
  -H "Content-Type: application/json" \
  -d '{"source": {"url": "https://youtube.com/watch?v=invalid"}}'
```

**Expected Response**:
```json
{
  "error": {
    "code": "ERR_2002",
    "message": "Invalid YouTube URL",
    "type": "VideoNotFoundError",
    "details": {
      "url": "https://youtube.com/watch?v=invalid",
      "reason": "Could not extract video ID"
    }
  }
}
```

### 2. OpenRouter/LLM API Fails

**Scenario**: LLM API is down or rate limited

**Expected Behavior**:
```
1. Request hits LLM API
2. Timeout after 30s or receives 429/503
3. Circuit breaker opens after 5 failures
4. Returns LLMAPIError (ERR_4001) or LLMRateLimitError (ERR_4003)
5. Subsequent requests fail fast with 503
```

**Test**:
```bash
# Simulate by temporarily removing API key
unset OPENROUTER_API_KEY

# Make request
curl -X POST http://localhost:8000/start \
  -H "user_id: test-user" \
  -H "Content-Type: application/json" \
  -d '{"source": {"url": "https://youtube.com/watch?v=valid-video"}}'
```

### 3. Disk Full

**Scenario**: Storage is full, cannot save clips

**Expected Behavior**:
```
1. Video downloads successfully
2. Clip generation starts
3. File write fails with disk full error
4. Returns StorageFullError (ERR_8003)
5. Task marked as "error" status
6. Partial files cleaned up
```

**Simulate**:
```bash
# Create a small temporary partition (Linux)
# Not recommended for production testing - use staging/dev only
```

### 4. Out of Memory

**Scenario**: Processing very large video causes OOM

**Expected Behavior**:
```
1. Video processing starts
2. Memory usage grows
3. Python MemoryError raised
4. Error middleware catches and logs critical error
5. Returns InternalServerError (ERR_1000)
6. Process potentially restarts (depends on deployment)
```

**Prevention**:
- Video duration limits (max 1 hour)
- Clip count limits (max 10 clips)
- Process monitoring and alerts

### 5. AssemblyAI Quota Exceeded

**Scenario**: Monthly transcription quota exhausted

**Expected Behavior**:
```
1. Transcription request sent
2. AssemblyAI returns 429 quota exceeded
3. Returns TranscriptionQuotaError (ERR_3004)
4. Circuit breaker opens after threshold
5. Client receives 429 with retry_after
```

**Response**:
```json
{
  "error": {
    "code": "ERR_3004",
    "message": "AssemblyAI quota exceeded",
    "type": "TranscriptionQuotaError"
  },
  "retry_after": 3600
}
```

### 6. Database Connection Lost

**Scenario**: PostgreSQL connection drops

**Expected Behavior**:
```
1. Database query fails
2. DatabaseConnectionError (ERR_5001)
3. Automatic retry (SQLAlchemy pool)
4. If persistent → Circuit breaker opens
5. Returns 503 Service Unavailable
6. Connection pool attempts reconnection
```

## Best Practices

### 1. Always Use Typed Exceptions

❌ **Bad**:
```python
if not user_id:
    raise Exception("User not found")
```

✅ **Good**:
```python
if not user_id:
    raise UserNotFoundError(
        message="User not found",
        details={"user_id": user_id}
    )
```

### 2. Add Context to Logs

❌ **Bad**:
```python
logger.error("Download failed")
```

✅ **Good**:
```python
logger.error(
    "Download failed",
    extra={
        "video_id": video_id,
        "url": url,
        "attempt": attempt,
        "error": str(e)
    },
    exc_info=True  # Include stack trace
)
```

### 3. Use Breadcrumbs for Complex Operations

```python
from errors import add_breadcrumb

add_breadcrumb(
    message="Starting video processing",
    category="video",
    data={"task_id": task_id, "video_path": str(path)}
)

# ... processing steps ...

add_breadcrumb(
    message="Generated clips",
    category="video",
    data={"clip_count": len(clips)}
)
```

### 4. Handle Circuit Breaker Errors

```python
from errors import CircuitBreakerOpenError

try:
    result = await some_external_api_call()
except CircuitBreakerOpenError as e:
    # Service is down, use fallback
    logger.warning(f"Circuit breaker open, using fallback")
    result = get_cached_result()
```

### 5. Set User Context for Tracking

```python
from errors import set_user

# In request handler
set_user(user_id=user_id, email=user_email)
```

## Monitoring & Alerts

### Key Metrics to Track

1. **Error Rate by Type**
   - Video processing errors (ERR_2xxx)
   - External service errors (ERR_6xxx)
   - Database errors (ERR_5xxx)

2. **Circuit Breaker States**
   - Services frequently in OPEN state
   - Recovery patterns
   - Failure thresholds

3. **Performance**
   - Slow requests (>5s)
   - Request duration percentiles (p50, p95, p99)
   - Circuit breaker call duration

4. **Error Patterns**
   - Spike in specific error codes
   - Error rate by endpoint
   - User-specific error patterns

### Sentry Dashboard

View in Sentry:
- Real-time error stream
- Error frequency charts
- Performance bottlenecks
- User impact analysis
- Release comparisons

### Circuit Breaker Health

```bash
# Check status
curl http://localhost:8000/health/circuit-breakers

# Watch for changes (Linux/Mac)
watch -n 5 'curl -s http://localhost:8000/health/circuit-breakers | jq'
```

## Troubleshooting

### Circuit Breaker Stuck Open

**Problem**: Circuit breaker won't close even when service recovered

**Solutions**:
1. Check service health directly
2. Review failure threshold configuration
3. Manually reset (development only):
   ```python
   from errors import youtube_breaker
   youtube_breaker.reset()
   ```

### High Error Rate

**Problem**: Sudden spike in errors

**Investigation Steps**:
1. Check Sentry for error grouping
2. Review circuit breaker states
3. Check external service status (AssemblyAI, OpenRouter, YouTube)
4. Review recent deployments
5. Check system resources (CPU, memory, disk)

### Logs Not Showing Request IDs

**Problem**: Logs missing `[request_id]`

**Cause**: Logger not using structured format

**Solution**:
```python
logger.info(
    "Message",
    extra={"request_id": request.state.request_id}
)
```

## Configuration Reference

### Environment Variables

```bash
# Error Tracking
SENTRY_DSN=                    # Optional: Sentry DSN for error tracking
ENVIRONMENT=production         # Environment name (production/staging/development)
APP_VERSION=1.0.0             # Application version for release tracking

# Service Limits
MAX_VIDEO_DURATION=3600       # Max video length in seconds (1 hour)
MAX_CLIPS=10                  # Max clips per video

# Timeouts
ASSEMBLY_AI_TIMEOUT=300       # AssemblyAI transcription timeout (5 min)
LLM_TIMEOUT=60                # LLM request timeout (1 min)
YOUTUBE_DOWNLOAD_TIMEOUT=600  # YouTube download timeout (10 min)
```

### Circuit Breaker Configuration

Located in `backend/src/errors/circuit_breaker.py`:

```python
# AssemblyAI
assemblyai_breaker = CircuitBreaker(
    failure_threshold=5,        # Open after 5 failures
    recovery_timeout=120.0,     # Try recovery after 2 minutes
    half_open_max_calls=3       # Allow 3 test calls in HALF_OPEN
)

# LLM
llm_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,      # Try recovery after 1 minute
    half_open_max_calls=3
)

# YouTube
youtube_breaker = CircuitBreaker(
    failure_threshold=3,        # More aggressive - open after 3 failures
    recovery_timeout=30.0,      # Quick recovery attempt (30 seconds)
    half_open_max_calls=3
)

# Database
database_breaker = CircuitBreaker(
    failure_threshold=10,       # Higher threshold (critical service)
    recovery_timeout=10.0,      # Quick recovery (10 seconds)
    half_open_max_calls=5
)
```

## Further Reading

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/why.html)

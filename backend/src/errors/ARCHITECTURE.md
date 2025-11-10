# Error Handling Architecture

## System Overview

The SupoClip error handling system is built on several key principles:

1. **Fail Fast, Recover Smart**: Detect errors quickly but provide intelligent recovery
2. **Structured Errors**: All errors carry context and metadata
3. **Circuit Protection**: Prevent cascade failures with circuit breakers
4. **Graceful Degradation**: Maintain core functionality even when optional features fail
5. **Observable**: Comprehensive logging and monitoring

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  - Request validation                                        │
│  - User authentication                                       │
│  - Request/Response logging                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Error Middleware                          │
│  - ErrorLoggingMiddleware (request tracking)                │
│  - RequestContextMiddleware (context enrichment)            │
│  - PerformanceMonitoringMiddleware (slow request detection) │
│  - ErrorRecoveryMiddleware (recoverable error handling)     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Service Layer                              │
│  - Business logic                                            │
│  - Custom exceptions with context                           │
│  - Circuit breaker decorators                               │
│  - Retry decorators                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 External Services                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐        │
│  │  YouTube    │  │  AssemblyAI  │  │  LLM APIs   │        │
│  │  (yt-dlp)   │  │              │  │             │        │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘        │
│         │                │                  │               │
│  ┌──────▼────────────────▼──────────────────▼──────┐        │
│  │          Circuit Breakers                       │        │
│  │  - youtube_breaker                              │        │
│  │  - assemblyai_breaker                           │        │
│  │  - llm_breaker                                  │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Error Handlers                              │
│  - BaseSupoClipException → Structured JSON                  │
│  - RequestValidationError → Validation details              │
│  - HTTPException → Standard HTTP errors                     │
│  - SQLAlchemyError → Database errors                        │
│  - Exception → Generic error handler                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│               Error Tracking (Sentry)                        │
│  - Error aggregation and alerting                           │
│  - User context tracking                                    │
│  - Breadcrumb trails                                        │
│  - Performance monitoring                                   │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Custom Exception Hierarchy

```
BaseSupoClipException
├── VideoProcessingError
│   ├── VideoDownloadError
│   ├── VideoNotFoundError
│   ├── VideoFormatError
│   ├── VideoTooLargeError
│   ├── VideoTooShortError
│   ├── VideoCorruptedError
│   └── ClipGenerationError
├── TranscriptionError
│   ├── AssemblyAIError
│   ├── TranscriptionTimeoutError
│   ├── TranscriptionRateLimitError
│   └── TranscriptionQuotaError
├── AIError
│   ├── LLMAPIError
│   ├── LLMTimeoutError
│   ├── LLMRateLimitError
│   ├── LLMQuotaError
│   └── InvalidAIResponseError
├── DatabaseError
│   ├── DatabaseConnectionError
│   ├── DatabaseTimeoutError
│   ├── RecordNotFoundError
│   └── DuplicateRecordError
├── ExternalServiceError
│   ├── YouTubeAPIError
│   ├── StorageError
│   ├── NetworkError
│   └── ServiceUnavailableError
├── WorkerError
│   ├── QueueError
│   ├── TaskTimeoutError
│   ├── TaskCancelledError
│   └── TaskNotFoundError
├── FileError
│   ├── FileNotFoundError
│   ├── FileReadError
│   ├── FileWriteError
│   ├── StorageFullError
│   └── InvalidFileTypeError
└── UserError
    ├── UserNotFoundError
    ├── InvalidCredentialsError
    ├── SessionExpiredError
    └── PermissionDeniedError
```

Each exception includes:
- **Error Code**: Unique identifier (e.g., `ERR_2000`)
- **Message**: Human-readable description
- **Details**: Contextual data (dict)
- **HTTP Status**: Appropriate HTTP status code
- **Cause**: Original exception (if applicable)
- **Retry After**: Seconds to wait before retrying (for rate limits)

### 2. Circuit Breaker State Machine

```
                    ┌──────────┐
                    │  CLOSED  │ ◄─── Normal operation
                    └─────┬────┘
                          │
                    Failures ≥ Threshold
                          │
                          ▼
                    ┌──────────┐
                    │   OPEN   │ ◄─── Fast-fail state
                    └─────┬────┘
                          │
                  Timeout Elapsed
                          │
                          ▼
                 ┌────────────────┐
                 │   HALF_OPEN    │ ◄─── Testing recovery
                 └────┬──────┬────┘
                      │      │
                Success      Failure
                      │      │
                      ▼      ▼
                  CLOSED   OPEN
```

**States:**
- **CLOSED**: All requests pass through. Track failures.
- **OPEN**: Block all requests. Fast-fail to prevent cascade.
- **HALF_OPEN**: Allow limited requests to test if service recovered.

**Configuration:**
- `failure_threshold`: Number of failures before opening (default: 5)
- `recovery_timeout`: Seconds before attempting recovery (default: 60)
- `half_open_max_calls`: Max calls in half-open state (default: 3)

### 3. Retry Strategy Flow

```
┌─────────────┐
│  Attempt 1  │
└──────┬──────┘
       │
    Success? ──Yes──► Return Result
       │
       No
       │
    Retryable? ──No──► Raise Exception
       │
       Yes
       │
    Wait (delay × backoff^attempt)
       │
       ▼
┌─────────────┐
│  Attempt 2  │
└──────┬──────┘
       │
       ...
       │
┌─────────────┐
│  Attempt N  │ (max_attempts)
└──────┬──────┘
       │
    Success? ──Yes──► Return Result
       │
       No
       │
    Fallback? ──Yes──► Call Fallback
       │
       No
       │
    Default? ──Yes──► Return Default
       │
       No
       │
   Raise Exception
```

**Configuration:**
- `max_attempts`: Maximum retry attempts (default: 3)
- `delay`: Initial delay in seconds (default: 2)
- `backoff`: Delay multiplier per attempt (default: 2)
- `exceptions`: Tuple of exceptions to retry

**Delays:**
- Attempt 1: Immediate
- Attempt 2: 2 seconds
- Attempt 3: 4 seconds
- Attempt 4: 8 seconds
- etc.

### 4. Error Recovery Decision Tree

```
                    ┌──────────────┐
                    │ Error Occurs │
                    └──────┬───────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────▼──────┐              ┌────────▼────────┐
    │  Retryable  │              │  Non-Retryable  │
    │   Error?    │              │     Error?      │
    └──────┬──────┘              └────────┬────────┘
           │                               │
          Yes                             No
           │                               │
    ┌──────▼───────┐                      │
    │ Retry with   │                      │
    │  Backoff     │                      │
    └──────┬───────┘                      │
           │                               │
     All retries                           │
       failed?                             │
           │                               │
          Yes                              │
           │                               │
           └───────────────┬───────────────┘
                           │
                  ┌────────▼────────┐
                  │   Fallback      │
                  │   Available?    │
                  └────────┬────────┘
                           │
                  ┌────────┴────────┐
                 Yes               No
                  │                 │
         ┌────────▼────────┐       │
         │  Call Fallback  │       │
         │   Function      │       │
         └────────┬────────┘       │
                  │                 │
            Success?               │
                  │                 │
         ┌────────┴────────┐       │
        Yes               No        │
         │                 │        │
    Return Result          │        │
                           │        │
                  ┌────────▼────────▼────┐
                  │   Default Value      │
                  │    Available?        │
                  └────────┬─────────────┘
                           │
                  ┌────────┴────────┐
                 Yes               No
                  │                 │
         Return Default    Raise Exception
```

### 5. Request Flow with Error Handling

```
Client Request
      │
      ▼
┌──────────────────────┐
│  CORS Middleware     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Error Logging        │ ◄─── Add request ID
│ Middleware           │      Log request
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Request Context      │ ◄─── Enrich context
│ Middleware           │      Set user context
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Performance          │ ◄─── Track timing
│ Monitoring           │      Detect slow requests
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ API Endpoint         │
│ (Route Handler)      │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
  Success       Error
    │             │
    ▼             ▼
┌───────┐  ┌──────────────────┐
│Return │  │ Exception        │
│ 200   │  │ Handlers         │
└───┬───┘  └──────┬───────────┘
    │             │
    │             ▼
    │      ┌──────────────────┐
    │      │ BaseSupoClip     │──► Structured JSON
    │      │ Exception?       │
    │      └──────┬───────────┘
    │             │
    │             ▼
    │      ┌──────────────────┐
    │      │ Validation       │──► 422 + details
    │      │ Error?           │
    │      └──────┬───────────┘
    │             │
    │             ▼
    │      ┌──────────────────┐
    │      │ HTTP             │──► Standard HTTP
    │      │ Exception?       │
    │      └──────┬───────────┘
    │             │
    │             ▼
    │      ┌──────────────────┐
    │      │ Database         │──► 500/503
    │      │ Error?           │
    │      └──────┬───────────┘
    │             │
    │             ▼
    │      ┌──────────────────┐
    │      │ Generic          │──► 500
    │      │ Exception        │
    │      └──────┬───────────┘
    │             │
    └─────────────┴────────────
           │
           ▼
    ┌──────────────────┐
    │ Error Tracking   │ ◄─── Send to Sentry
    │ (Sentry)         │
    └──────┬───────────┘
           ▼
    Client Response
```

## Error Propagation Strategy

### Layer 1: External Service Calls

**Responsibility**: Convert external errors to domain exceptions

```python
# External service layer
@youtube_breaker  # Circuit breaker
@async_retry(max_attempts=3)  # Retry
async def download_youtube_video(url: str) -> str:
    try:
        return await yt_dlp.download(url)
    except yt_dlp.DownloadError as e:
        # Convert to domain exception
        raise VideoDownloadError(
            message=f"YouTube download failed: {url}",
            details={"url": url, "error": str(e)},
            cause=e
        )
```

### Layer 2: Business Logic

**Responsibility**: Add business context and recovery

```python
# Service layer
async def process_video(url: str) -> dict:
    # Download with fallback
    video_path = await retry_with_recovery(
        download_youtube_video,
        url,
        fallback=lambda: get_cached_video(url),
        fallback_value=None
    )

    if not video_path:
        raise VideoProcessingError(
            message="Unable to obtain video",
            details={"url": url, "tried_cache": True}
        )

    return await process_video_file(video_path)
```

### Layer 3: API Endpoints

**Responsibility**: Handle errors and return appropriate responses

```python
# API layer
@app.post("/process")
async def process_endpoint(request: Request):
    try:
        result = await process_video(url)
        return {"status": "success", "result": result}

    except VideoDownloadError as e:
        # Let error handler convert to JSON response
        raise

    except Exception as e:
        # Capture unexpected errors
        capture_exception(e)
        raise
```

### Layer 4: Error Handlers

**Responsibility**: Convert exceptions to HTTP responses

```python
# Error handler
async def base_exception_handler(request, exc: BaseSupoClipException):
    # Log with context
    logger.error(f"Error: {exc.message}", extra={...})

    # Return structured response
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )
```

## Monitoring & Observability

### Metrics to Track

1. **Error Metrics**
   - Error rate by endpoint
   - Error rate by type
   - Error rate by user

2. **Circuit Breaker Metrics**
   - State changes
   - Failure rate per service
   - Recovery success rate

3. **Retry Metrics**
   - Average retry attempts
   - Retry success rate
   - Time spent retrying

4. **Performance Metrics**
   - Request duration (p50, p95, p99)
   - Slow request count
   - Timeout count

### Logging Strategy

**Structured Logging Format:**

```json
{
  "timestamp": "2025-11-10T12:34:56Z",
  "level": "ERROR",
  "message": "Video download failed",
  "request_id": "abc-123-def",
  "user_id": "user_456",
  "error_code": "ERR_2000",
  "error_type": "VideoDownloadError",
  "details": {
    "url": "https://youtube.com/watch?v=...",
    "attempt": 3
  },
  "trace_id": "span_789"
}
```

**Log Levels:**
- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages (request started, completed)
- **WARNING**: Retries, degraded functionality, slow requests
- **ERROR**: Errors that affect user requests
- **CRITICAL**: System-level failures

## Security Considerations

1. **Error Message Sanitization**
   - Never expose internal paths in production
   - Sanitize database connection strings
   - Remove sensitive query parameters from URLs

2. **Rate Limit Information**
   - Don't expose internal service limits
   - Provide reasonable `retry_after` values
   - Aggregate error details to prevent information leakage

3. **User Context**
   - Only track necessary user information
   - Comply with GDPR/privacy regulations
   - Allow opt-out of error tracking

## Performance Impact

**Circuit Breakers:**
- Overhead: ~0.1ms per call
- Memory: ~1KB per breaker instance

**Retry Logic:**
- Overhead: Minimal (only on errors)
- Latency: Increases with retries (configurable)

**Error Tracking (Sentry):**
- Overhead: ~1-2ms per error
- Async sending: No blocking
- Sampling: Configurable (default: 10% of transactions)

**Middleware:**
- Request logging: ~0.2ms per request
- Context enrichment: ~0.1ms per request
- Performance monitoring: ~0.1ms per request

**Total overhead:** ~0.5-1ms per successful request, acceptable for most use cases.

## Scalability

The error handling system is designed to scale:

1. **Stateless Circuit Breakers**: Can be shared across workers
2. **Async Logging**: Non-blocking error capture
3. **Sentry Sampling**: Prevents overwhelming error tracking
4. **Connection Pooling**: Reuses database/HTTP connections

## Testing Strategy

1. **Unit Tests**: Test individual exception classes
2. **Integration Tests**: Test circuit breakers with mock services
3. **Load Tests**: Verify performance under error conditions
4. **Chaos Engineering**: Randomly inject failures to test recovery

## Future Enhancements

1. **Distributed Tracing**: Add OpenTelemetry integration
2. **Error Budgets**: Define SLOs and track error budgets
3. **Auto-Recovery**: Automatic remediation for known issues
4. **ML-Based Prediction**: Predict failures before they occur
5. **Error Replay**: Replay failed requests after fixes

## Conclusion

This error handling architecture provides:
- ✅ **Reliability**: Circuit breakers prevent cascade failures
- ✅ **Resilience**: Automatic retries and fallbacks
- ✅ **Observability**: Comprehensive logging and monitoring
- ✅ **Maintainability**: Structured errors with context
- ✅ **Scalability**: Minimal overhead, async operations

The system is designed to handle errors gracefully while providing excellent visibility into what went wrong and why.

# Error Handling Examples

## Table of Contents

1. [Basic Exception Handling](#basic-exception-handling)
2. [Circuit Breaker Pattern](#circuit-breaker-pattern)
3. [Retry with Exponential Backoff](#retry-with-exponential-backoff)
4. [Error Recovery Strategies](#error-recovery-strategies)
5. [Worker Error Handling](#worker-error-handling)
6. [API Endpoint Error Handling](#api-endpoint-error-handling)
7. [Sentry Integration](#sentry-integration)

---

## Basic Exception Handling

### Raising Custom Exceptions

```python
from ..errors import VideoNotFoundError, VideoDownloadError

def process_video(video_path: str):
    """Process video with proper error handling."""

    if not Path(video_path).exists():
        raise VideoNotFoundError(
            message=f"Video file not found: {video_path}",
            details={
                "video_path": video_path,
                "checked_at": datetime.now().isoformat()
            }
        )

    try:
        # Process video
        result = video_processor.process(video_path)
        return result

    except MemoryError as e:
        raise VideoProcessingError(
            message="Insufficient memory to process video",
            details={
                "video_path": video_path,
                "file_size": Path(video_path).stat().st_size
            },
            cause=e
        )
```

### Catching and Converting Exceptions

```python
from ..errors import YouTubeAPIError, VideoDownloadError
import yt_dlp

def download_youtube_video(url: str) -> str:
    """Download YouTube video with error conversion."""

    try:
        ydl_opts = {
            'outtmpl': '%(id)s.%(ext)s',
            'format': 'best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    except yt_dlp.utils.DownloadError as e:
        # Convert yt-dlp error to our custom error
        error_msg = str(e)

        if "403" in error_msg or "Forbidden" in error_msg:
            raise YouTubeAPIError(
                message="YouTube blocked the download request",
                details={
                    "url": url,
                    "error": error_msg,
                    "suggestion": "Try updating yt-dlp or use a different extractor"
                },
                cause=e
            )

        raise VideoDownloadError(
            message=f"Failed to download YouTube video",
            details={"url": url, "error": error_msg},
            cause=e
        )
```

---

## Circuit Breaker Pattern

### Using Pre-configured Circuit Breakers

```python
from ..errors import (
    assemblyai_breaker,
    llm_breaker,
    youtube_breaker,
    CircuitBreakerOpenError,
    AssemblyAIError,
)

# AssemblyAI with circuit breaker
@assemblyai_breaker
async def transcribe_video(video_path: str) -> str:
    """Transcribe video with circuit breaker protection."""

    try:
        import assemblyai as aai

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_path)

        if transcript.status == aai.TranscriptStatus.error:
            raise AssemblyAIError(
                message="Transcription failed",
                details={"error": transcript.error}
            )

        return transcript.text

    except Exception as e:
        raise AssemblyAIError(
            message="AssemblyAI API error",
            cause=e
        )

# Handling circuit breaker open state
async def safe_transcribe(video_path: str) -> Optional[str]:
    """Transcribe with circuit breaker handling."""

    try:
        return await transcribe_video(video_path)

    except CircuitBreakerOpenError as e:
        logger.warning(
            f"Transcription circuit breaker is open. "
            f"Retry after {e.retry_after} seconds"
        )
        # Return None or use cached/fallback result
        return None
```

### Creating Custom Circuit Breakers

```python
from ..errors import CircuitBreaker, get_circuit_breaker

# Create custom circuit breaker
custom_api_breaker = get_circuit_breaker(
    name="custom_api",
    failure_threshold=3,  # Open after 3 failures
    recovery_timeout=30.0,  # Try recovery after 30s
)

@custom_api_breaker
async def call_custom_api(data: dict) -> dict:
    """Call external API with circuit breaker."""
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.example.com", json=data)
        response.raise_for_status()
        return response.json()

# Using circuit breaker directly
async def call_with_breaker():
    """Call function with circuit breaker protection."""
    breaker = get_circuit_breaker("my_service")

    try:
        result = await breaker.call(my_function, arg1, arg2, kwarg="value")
        return result

    except CircuitBreakerOpenError as e:
        logger.warning(f"Circuit is open, retry after {e.retry_after}s")
        # Handle degraded state
        return default_value
```

---

## Retry with Exponential Backoff

### Using Retry Decorator

```python
from ..utils.retry_utils import async_retry
from ..errors import LLMAPIError, LLMRateLimitError

@async_retry(
    max_attempts=3,
    delay=2.0,
    backoff=2.0,
    exceptions=(LLMAPIError,)  # Only retry these
)
async def analyze_transcript(transcript: str) -> dict:
    """Analyze transcript with automatic retries."""

    try:
        result = await llm_api.analyze(transcript)
        return result

    except RateLimitException as e:
        raise LLMRateLimitError(
            message="LLM rate limit exceeded",
            retry_after=60,
            cause=e
        )
```

### Manual Retry with Recovery

```python
from ..errors.error_recovery import retry_with_recovery

async def fetch_with_fallback(url: str) -> dict:
    """Fetch data with retry and fallback."""

    # Primary fetch function
    async def primary_fetch():
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    # Fallback function
    async def fallback_fetch():
        # Try alternative endpoint or cached data
        return await cache.get(f"cached:{url}")

    return await retry_with_recovery(
        primary_fetch,
        max_attempts=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        fallback=fallback_fetch,
        fallback_value={"status": "degraded"}
    )
```

---

## Error Recovery Strategies

### Fallback Pattern

```python
from ..errors.error_recovery import with_fallback

@with_fallback(fallback_value=[])
async def get_recommended_clips(video_id: str) -> List[dict]:
    """Get recommendations with fallback to empty list."""

    # This may fail, but will return [] instead of raising
    return await ai_service.get_recommendations(video_id)

@with_fallback(fallback_func=get_cached_result)
async def fetch_analysis(data: dict) -> dict:
    """Fetch analysis with fallback to cached data."""

    return await expensive_ai_analysis(data)

def get_cached_result(data: dict) -> dict:
    """Fallback function to get cached result."""
    cache_key = hash(str(data))
    return cache.get(cache_key, {})
```

### Graceful Degradation

```python
from ..errors.error_recovery import GracefulDegradation

async def process_with_optional_features(video_path: str):
    """Process video with optional features that can fail."""

    # Critical processing (must succeed)
    clips = await generate_clips(video_path)

    # Optional: Add AI titles (can fail gracefully)
    with GracefulDegradation() as gd:
        titles = await generate_ai_titles(clips)
        for clip, title in zip(clips, titles):
            clip["title"] = title

    if gd.degraded:
        logger.warning("AI titles unavailable, using defaults")
        for clip in clips:
            clip["title"] = f"Clip {clip['index']}"

    # Optional: Add thumbnails (can fail gracefully)
    with GracefulDegradation() as gd:
        thumbnails = await generate_thumbnails(clips)

    if gd.degraded:
        logger.warning("Thumbnail generation failed")

    return clips
```

### Timeout with Recovery

```python
from ..errors.error_recovery import with_timeout_recovery

async def process_with_timeout(video_path: str) -> dict:
    """Process video with timeout and fallback."""

    async def slow_processing():
        # This might take too long
        return await expensive_processing(video_path)

    async def quick_fallback():
        # Faster, lower-quality processing
        return await quick_processing(video_path)

    return await with_timeout_recovery(
        slow_processing,
        timeout=30.0,  # 30 second timeout
        fallback=quick_fallback
    )
```

---

## Worker Error Handling

### Worker Task with Full Error Handling

```python
from ..errors import (
    WorkerError,
    TaskTimeoutError,
    VideoProcessingError,
    capture_exception,
    add_breadcrumb,
)

async def process_video_task(
    ctx: dict,
    task_id: str,
    url: str,
    user_id: str
) -> dict:
    """
    Worker task with comprehensive error handling.
    """

    # Add breadcrumb for debugging
    add_breadcrumb(
        message=f"Starting video task {task_id}",
        category="worker",
        data={"task_id": task_id, "url": url}
    )

    try:
        # Update task status
        await update_task_status(task_id, "processing")
        add_breadcrumb("Task status updated to processing", category="worker")

        # Download video with retry and circuit breaker
        add_breadcrumb("Downloading video", category="worker")
        try:
            video_path = await download_video_with_retry(url)
        except Exception as e:
            raise VideoDownloadError(
                message=f"Failed to download video for task {task_id}",
                details={"task_id": task_id, "url": url},
                cause=e
            )

        add_breadcrumb(f"Video downloaded: {video_path}", category="worker")

        # Process video with timeout
        add_breadcrumb("Processing video", category="worker")
        try:
            result = await with_timeout_recovery(
                process_video,
                video_path,
                timeout=300.0,  # 5 minute timeout
            )
        except asyncio.TimeoutError as e:
            raise TaskTimeoutError(
                message=f"Task {task_id} timed out during processing",
                details={"task_id": task_id, "timeout": 300},
                cause=e
            )

        # Update task status
        await update_task_status(task_id, "completed")
        add_breadcrumb("Task completed successfully", category="worker")

        return result

    except TaskTimeoutError:
        # Don't retry timeouts
        await update_task_status(task_id, "timeout")
        raise

    except VideoDownloadError:
        # Don't retry download errors (might be invalid URL)
        await update_task_status(task_id, "failed")
        raise

    except Exception as e:
        # Capture unexpected errors
        capture_exception(e, context={
            "worker": "process_video_task",
            "task_id": task_id,
            "user_id": user_id,
        })

        await update_task_status(task_id, "error")

        raise WorkerError(
            message=f"Worker task {task_id} failed",
            details={"task_id": task_id, "error": str(e)},
            cause=e
        )

    finally:
        # Cleanup
        add_breadcrumb("Task cleanup", category="worker")
        await cleanup_temp_files(task_id)
```

---

## API Endpoint Error Handling

### Endpoint with Full Error Handling

```python
from fastapi import Request, Depends
from ..errors import (
    UserNotFoundError,
    VideoNotFoundError,
    capture_exception,
    set_user,
    add_breadcrumb,
)

@app.post("/process-video")
async def process_video_endpoint(
    request: Request,
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Process video endpoint with full error handling."""

    user_id = request.headers.get("user_id")

    # Set user context for error tracking
    if user_id:
        set_user(user_id)

    # Validate user
    if not user_id:
        raise UserNotFoundError(
            message="User authentication required",
            details={"missing_header": "user_id"}
        )

    # Add breadcrumb
    add_breadcrumb(
        f"Processing video {video_id}",
        category="api",
        data={"video_id": video_id, "user_id": user_id}
    )

    try:
        # Get video from database
        video = await db.execute(
            text("SELECT * FROM videos WHERE id = :id"),
            {"id": video_id}
        )
        video_data = video.fetchone()

        if not video_data:
            raise VideoNotFoundError(
                message=f"Video not found: {video_id}",
                details={"video_id": video_id}
            )

        # Process video with circuit breaker and retry
        result = await process_with_circuit_breaker(video_data.path)

        return {
            "status": "success",
            "video_id": video_id,
            "result": result
        }

    except (UserNotFoundError, VideoNotFoundError):
        # Let these propagate to error handler
        raise

    except Exception as e:
        # Capture unexpected errors
        capture_exception(e, context={
            "endpoint": "process_video",
            "video_id": video_id,
            "user_id": user_id
        })

        # Re-raise as generic error (will be handled by error handler)
        raise
```

---

## Sentry Integration

### Initialize Sentry

```python
# In main.py
from .errors import initialize_error_tracking

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Sentry
    initialize_error_tracking(
        environment=os.getenv("ENVIRONMENT", "production")
    )

    yield
```

### Capture Exceptions

```python
from ..errors import capture_exception, capture_message, add_breadcrumb

async def risky_operation():
    """Operation with Sentry tracking."""

    # Add breadcrumb for context
    add_breadcrumb(
        "Starting risky operation",
        category="operation",
        data={"timestamp": datetime.now().isoformat()}
    )

    try:
        result = await perform_operation()

        # Capture informational message
        capture_message(
            "Operation completed successfully",
            level="info",
            context={"result_count": len(result)}
        )

        return result

    except Exception as e:
        # Capture exception with context
        capture_exception(
            e,
            context={
                "operation": "risky_operation",
                "additional_info": "custom data"
            },
            level="error"
        )

        raise
```

### User Context

```python
from ..errors import set_user

@app.middleware("http")
async def track_user_middleware(request: Request, call_next):
    """Middleware to set user context for error tracking."""

    user_id = request.headers.get("user_id")

    if user_id:
        # Set user context for Sentry
        set_user(
            user_id=user_id,
            # Optional: add more user info if available
            # email=user.email,
            # username=user.username
        )

    response = await call_next(request)
    return response
```

---

## Complete Example: Video Processing Service

```python
from ..errors import (
    VideoProcessingError,
    VideoDownloadError,
    TranscriptionError,
    AIError,
    youtube_breaker,
    assemblyai_breaker,
    llm_breaker,
    capture_exception,
    add_breadcrumb,
)
from ..utils.retry_utils import async_retry
from ..errors.error_recovery import retry_with_recovery

class VideoProcessingService:
    """Video processing service with full error handling."""

    @youtube_breaker  # Circuit breaker
    @async_retry(max_attempts=3, delay=2, backoff=2)  # Retry
    async def download_video(self, url: str) -> str:
        """Download video with circuit breaker and retry."""

        add_breadcrumb(f"Downloading video: {url}", category="video")

        try:
            video_path = await yt_dlp_download(url)
            return video_path

        except Exception as e:
            raise VideoDownloadError(
                message=f"Failed to download video",
                details={"url": url},
                cause=e
            )

    @assemblyai_breaker
    async def transcribe_video(self, video_path: str) -> str:
        """Transcribe video with circuit breaker."""

        add_breadcrumb(f"Transcribing: {video_path}", category="transcription")

        try:
            transcript = await assemblyai.transcribe(video_path)
            return transcript

        except Exception as e:
            raise TranscriptionError(
                message="Transcription failed",
                details={"video_path": video_path},
                cause=e
            )

    @llm_breaker
    async def analyze_transcript(self, transcript: str) -> dict:
        """Analyze transcript with circuit breaker."""

        add_breadcrumb("Analyzing transcript", category="ai")

        try:
            analysis = await llm.analyze(transcript)
            return analysis

        except Exception as e:
            raise AIError(
                message="AI analysis failed",
                details={"transcript_length": len(transcript)},
                cause=e
            )

    async def process_complete_video(self, url: str) -> dict:
        """
        Complete video processing pipeline with error handling.
        """

        try:
            # Download (with circuit breaker + retry)
            video_path = await self.download_video(url)

            # Transcribe (with circuit breaker + fallback)
            transcript = await retry_with_recovery(
                self.transcribe_video,
                video_path,
                max_attempts=3,
                fallback_value=""  # Empty transcript if fails
            )

            # Analyze (with circuit breaker + fallback)
            if transcript:
                analysis = await retry_with_recovery(
                    self.analyze_transcript,
                    transcript,
                    max_attempts=2,
                    fallback_value={"segments": []}
                )
            else:
                analysis = {"segments": []}

            return {
                "video_path": video_path,
                "transcript": transcript,
                "analysis": analysis
            }

        except VideoDownloadError as e:
            # Download failed - can't continue
            capture_exception(e, context={"url": url})
            raise

        except Exception as e:
            # Unexpected error
            capture_exception(e, context={"url": url, "step": "unknown"})

            raise VideoProcessingError(
                message="Video processing failed",
                details={"url": url},
                cause=e
            )
```

This comprehensive example shows how to combine circuit breakers, retries, fallbacks, and error tracking in a real service.

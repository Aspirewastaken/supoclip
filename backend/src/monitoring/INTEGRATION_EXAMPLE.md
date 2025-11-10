# Monitoring Integration Example

This document shows how to integrate the monitoring module into your FastAPI application.

## Basic Integration (Recommended)

Add these lines to `backend/src/main.py`:

```python
from .monitoring import setup_monitoring

# After creating the FastAPI app
app = FastAPI(
    title="SupoClip API",
    version="1.0.0",
    lifespan=lifespan
)

# Setup monitoring - adds middleware, /metrics, and /health endpoints
setup_monitoring(app, version="1.0.0")
```

That's it! The `setup_monitoring()` function automatically:
- Adds Prometheus middleware to track requests
- Creates `/metrics` endpoint for Prometheus
- Creates `/health` endpoint for health checks

## Manual Integration (Advanced)

If you need more control, you can manually add components:

```python
from fastapi import FastAPI, Depends, Response
from .monitoring import (
    PrometheusMiddleware,
    get_metrics,
    get_metrics_content_type,
    get_health_status,
    app_info,
    app_uptime_seconds
)
from .database import get_db
import time

app = FastAPI(...)

# 1. Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# 2. Set application info
app_info.info({
    'version': '1.0.0',
    'name': 'SupoClip Backend'
})

# Track app start time
_app_start_time = time.time()

# 3. Add metrics endpoint
@app.get("/metrics")
async def metrics():
    # Update uptime before exporting metrics
    app_uptime_seconds.set(time.time() - _app_start_time)

    metrics_data = get_metrics()
    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type()
    )

# 4. Add health check endpoint
@app.get("/health")
async def health(db = Depends(get_db)):
    health_status = await get_health_status(db)
    return health_status
```

## Using Metrics in Your Code

### Track Video Processing Stages

```python
from .monitoring import track_video_processing_stage

async def process_video(video_url: str):
    # Automatically times and records the download stage
    with track_video_processing_stage("download"):
        video_path = await download_video(video_url)

    with track_video_processing_stage("transcribe"):
        transcript = await transcribe_video(video_path)

    with track_video_processing_stage("analyze"):
        segments = await analyze_transcript(transcript)

    with track_video_processing_stage("clip_generation"):
        clips = await generate_clips(video_path, segments)

    return clips
```

### Track Success/Failure

```python
from .monitoring import video_processing_total, clips_generated_total

async def process_video(video_url: str):
    try:
        clips = await generate_clips(video_url)

        # Record success
        video_processing_total.labels(status="success").inc()
        clips_generated_total.labels(source_type="youtube").inc(len(clips))

        return clips

    except Exception as e:
        # Record failure
        video_processing_total.labels(status="failed").inc()
        raise
```

### Track Worker Tasks

```python
from .monitoring import track_worker_task

@track_worker_task(queue_name="video_processing", task_type="clip_generation")
async def process_video_task(ctx, video_url: str):
    """This decorator automatically tracks task duration and status"""
    result = await process_video(video_url)
    return result
```

### Update Queue Depth

```python
from .monitoring import worker_queue_depth

async def update_queue_metrics():
    """Periodically update queue depth metrics"""
    queue_size = await redis.llen("video_processing_queue")
    worker_queue_depth.labels(queue_name="video_processing").set(queue_size)
```

### Track Database Queries

```python
from .monitoring import track_db_query

async def get_user_tasks(user_id: str, db):
    with track_db_query("get_user_tasks"):
        result = await db.execute(
            text("SELECT * FROM tasks WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
    return result.fetchall()
```

### Track Video Processing in Progress

```python
from .monitoring import video_processing_in_progress

async def process_video(video_url: str):
    # Increment counter
    video_processing_in_progress.inc()

    try:
        result = await do_processing(video_url)
        return result
    finally:
        # Always decrement, even on error
        video_processing_in_progress.dec()
```

### Track Errors

```python
from .monitoring import errors_total, exceptions_total

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Track exception
    exceptions_total.labels(
        exception_type=type(exc).__name__,
        endpoint=request.url.path
    ).inc()

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Complete Example

Here's a complete example integrating all monitoring features:

```python
# backend/src/main.py
from fastapi import FastAPI, HTTPException, Depends
from .monitoring import (
    setup_monitoring,
    track_video_processing_stage,
    video_processing_total,
    video_processing_in_progress,
    clips_generated_total,
    exceptions_total
)

app = FastAPI(title="SupoClip API", version="1.0.0")

# Setup monitoring
setup_monitoring(app, version="1.0.0")

# Add exception handler for tracking
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    exceptions_total.labels(
        exception_type=type(exc).__name__,
        endpoint=request.url.path
    ).inc()
    raise

@app.post("/process-video")
async def process_video_endpoint(video_url: str):
    video_processing_in_progress.inc()

    try:
        # Download
        with track_video_processing_stage("download"):
            video_path = await download_video(video_url)

        # Transcribe
        with track_video_processing_stage("transcribe"):
            transcript = await transcribe(video_path)

        # Analyze
        with track_video_processing_stage("analyze"):
            segments = await analyze(transcript)

        # Generate clips
        with track_video_processing_stage("clip_generation"):
            clips = await create_clips(video_path, segments)

        # Record success
        video_processing_total.labels(status="success").inc()
        clips_generated_total.labels(source_type="youtube").inc(len(clips))

        return {"clips": clips}

    except Exception as e:
        video_processing_total.labels(status="failed").inc()
        raise

    finally:
        video_processing_in_progress.dec()
```

## Verifying Integration

After integrating monitoring, verify it works:

### 1. Check Metrics Endpoint

```bash
curl http://localhost:8000/metrics | grep supoclip
```

Should show metrics like:
```
supoclip_http_requests_total{endpoint="/",method="GET",status="200"} 42.0
supoclip_video_processing_in_progress 2.0
supoclip_memory_usage_percent 54.2
```

### 2. Check Health Endpoint

```bash
curl http://localhost:8000/health | jq
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "response_time_ms": 5.2
    },
    ...
  ]
}
```

### 3. Verify in Prometheus

1. Open http://localhost:9090
2. Go to Status → Targets
3. `supoclip-backend` should show "UP"
4. Query: `supoclip_http_requests_total`

### 4. View in Grafana

1. Open http://localhost:3001
2. Go to Dashboards → SupoClip Overview
3. Should see real-time metrics

## Troubleshooting

### Metrics not appearing

Make sure you've:
1. Installed dependencies: `uv sync`
2. Called `setup_monitoring(app)`
3. Started Prometheus: `docker-compose -f docker-compose.monitoring.yml up -d`

### Health check fails

Check:
1. Database is running
2. Database connection string is correct
3. `get_db` dependency is properly configured

### ModuleNotFoundError

Ensure monitoring module exists:
```bash
ls backend/src/monitoring/
# Should show: __init__.py, metrics.py, health.py, integration.py
```

## Best Practices

1. **Always use context managers** for timed operations
   ```python
   with track_video_processing_stage("stage_name"):
       # Your code here
   ```

2. **Track both success and failure**
   ```python
   try:
       result = process()
       counter.labels(status="success").inc()
   except:
       counter.labels(status="failed").inc()
       raise
   ```

3. **Use meaningful label values**
   ```python
   # Good
   clips_generated_total.labels(source_type="youtube").inc()

   # Bad (too many unique values)
   clips_generated_total.labels(video_url=url).inc()
   ```

4. **Don't track sensitive data in labels**
   ```python
   # Bad - exposes user data
   metric.labels(user_id=user_id, email=email)

   # Good - no PII
   metric.labels(user_type=user_type)
   ```

## Next Steps

- Review [MONITORING.md](../../../MONITORING.md) for full documentation
- Check [QUICK_START.md](../../../monitoring/QUICK_START.md) for setup
- Explore Grafana dashboards
- Configure alerting for your needs

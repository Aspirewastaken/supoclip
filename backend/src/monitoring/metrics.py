"""
Prometheus Metrics for SupoClip Backend

This module provides comprehensive metrics tracking for:
- Request latency by endpoint
- Worker queue depth
- Video processing time
- Error rates
- Memory/CPU usage
- Disk space
"""

import time
import psutil
import shutil
from pathlib import Path
from typing import Callable
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

# Create custom registry (optional, can use default)
registry = CollectorRegistry()

# =============================================================================
# REQUEST METRICS
# =============================================================================

# HTTP request counter
http_requests_total = Counter(
    'supoclip_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# HTTP request duration
http_request_duration_seconds = Histogram(
    'supoclip_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0, float('inf')),
    registry=registry
)

# HTTP requests in progress
http_requests_in_progress = Gauge(
    'supoclip_http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# =============================================================================
# VIDEO PROCESSING METRICS
# =============================================================================

# Video processing duration
video_processing_duration_seconds = Histogram(
    'supoclip_video_processing_duration_seconds',
    'Video processing duration in seconds',
    ['stage'],  # stages: download, transcribe, analyze, clip_generation
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0, float('inf')),
    registry=registry
)

# Video processing counter
video_processing_total = Counter(
    'supoclip_video_processing_total',
    'Total number of videos processed',
    ['status'],  # status: success, failed, cancelled
    registry=registry
)

# Clips generated counter
clips_generated_total = Counter(
    'supoclip_clips_generated_total',
    'Total number of clips generated',
    ['source_type'],  # source_type: youtube, uploaded
    registry=registry
)

# Current video processing tasks
video_processing_in_progress = Gauge(
    'supoclip_video_processing_in_progress',
    'Number of video processing tasks in progress',
    registry=registry
)

# =============================================================================
# WORKER QUEUE METRICS
# =============================================================================

# Worker queue depth
worker_queue_depth = Gauge(
    'supoclip_worker_queue_depth',
    'Number of tasks in worker queue',
    ['queue_name'],
    registry=registry
)

# Worker queue processing time
worker_queue_processing_time_seconds = Histogram(
    'supoclip_worker_queue_processing_time_seconds',
    'Time spent processing tasks from queue',
    ['queue_name', 'task_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0, float('inf')),
    registry=registry
)

# Worker queue tasks processed
worker_queue_tasks_processed_total = Counter(
    'supoclip_worker_queue_tasks_processed_total',
    'Total number of tasks processed by workers',
    ['queue_name', 'task_type', 'status'],
    registry=registry
)

# Active workers
active_workers = Gauge(
    'supoclip_active_workers',
    'Number of active worker processes',
    registry=registry
)

# Failed workers
failed_workers_total = Counter(
    'supoclip_failed_workers_total',
    'Total number of worker failures',
    ['worker_id', 'reason'],
    registry=registry
)

# =============================================================================
# ERROR METRICS
# =============================================================================

# Error counter
errors_total = Counter(
    'supoclip_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint'],
    registry=registry
)

# Exception counter
exceptions_total = Counter(
    'supoclip_exceptions_total',
    'Total number of unhandled exceptions',
    ['exception_type', 'endpoint'],
    registry=registry
)

# =============================================================================
# RESOURCE METRICS
# =============================================================================

# CPU usage
cpu_usage_percent = Gauge(
    'supoclip_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

# Memory usage
memory_usage_bytes = Gauge(
    'supoclip_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

memory_usage_percent = Gauge(
    'supoclip_memory_usage_percent',
    'Memory usage percentage',
    registry=registry
)

# Disk usage
disk_usage_bytes = Gauge(
    'supoclip_disk_usage_bytes',
    'Disk usage in bytes',
    ['path'],
    registry=registry
)

disk_usage_percent = Gauge(
    'supoclip_disk_usage_percent',
    'Disk usage percentage',
    ['path'],
    registry=registry
)

disk_free_bytes = Gauge(
    'supoclip_disk_free_bytes',
    'Free disk space in bytes',
    ['path'],
    registry=registry
)

# =============================================================================
# DATABASE METRICS
# =============================================================================

# Database query duration
db_query_duration_seconds = Histogram(
    'supoclip_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, float('inf')),
    registry=registry
)

# Database connections
db_connections_active = Gauge(
    'supoclip_db_connections_active',
    'Number of active database connections',
    registry=registry
)

db_connections_idle = Gauge(
    'supoclip_db_connections_idle',
    'Number of idle database connections',
    registry=registry
)

# =============================================================================
# APPLICATION INFO
# =============================================================================

# Application info
app_info = Info(
    'supoclip_app',
    'SupoClip application information',
    registry=registry
)

# Application uptime
app_uptime_seconds = Gauge(
    'supoclip_app_uptime_seconds',
    'Application uptime in seconds',
    registry=registry
)

# =============================================================================
# CUSTOM METRICS HELPER FUNCTIONS
# =============================================================================

def update_resource_metrics():
    """Update system resource metrics (CPU, memory, disk)"""
    try:
        # CPU usage
        cpu_usage_percent.set(psutil.cpu_percent(interval=0.1))

        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage_bytes.set(memory.used)
        memory_usage_percent.set(memory.percent)

        # Disk usage for common paths
        paths_to_monitor = ['/tmp', '/app/uploads', '/app/clips']
        for path in paths_to_monitor:
            if Path(path).exists():
                try:
                    usage = shutil.disk_usage(path)
                    disk_usage_bytes.labels(path=path).set(usage.used)
                    disk_usage_percent.labels(path=path).set((usage.used / usage.total) * 100)
                    disk_free_bytes.labels(path=path).set(usage.free)
                except Exception:
                    pass  # Path might not be accessible

    except Exception as e:
        print(f"Error updating resource metrics: {e}")


def track_video_processing_stage(stage: str):
    """Context manager to track video processing stage duration"""
    class VideoProcessingTimer:
        def __init__(self, stage: str):
            self.stage = stage
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            video_processing_duration_seconds.labels(stage=self.stage).observe(duration)

    return VideoProcessingTimer(stage)


def track_worker_task(queue_name: str, task_type: str):
    """Decorator to track worker task processing"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failed"
                raise
            finally:
                duration = time.time() - start_time
                worker_queue_processing_time_seconds.labels(
                    queue_name=queue_name,
                    task_type=task_type
                ).observe(duration)
                worker_queue_tasks_processed_total.labels(
                    queue_name=queue_name,
                    task_type=task_type,
                    status=status
                ).inc()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failed"
                raise
            finally:
                duration = time.time() - start_time
                worker_queue_processing_time_seconds.labels(
                    queue_name=queue_name,
                    task_type=task_type
                ).observe(duration)
                worker_queue_tasks_processed_total.labels(
                    queue_name=queue_name,
                    task_type=task_type,
                    status=status
                ).inc()

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_db_query(query_type: str):
    """Context manager to track database query duration"""
    class DBQueryTimer:
        def __init__(self, query_type: str):
            self.query_type = query_type
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            db_query_duration_seconds.labels(query_type=self.query_type).observe(duration)

    return DBQueryTimer(query_type)


# =============================================================================
# PROMETHEUS MIDDLEWARE
# =============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics"""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Normalize path (remove IDs)
        normalized_path = self._normalize_path(path)

        # Track request in progress
        http_requests_in_progress.labels(method=method, endpoint=normalized_path).inc()

        # Track request duration
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code

            # Record metrics
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=normalized_path
            ).observe(duration)

            http_requests_total.labels(
                method=method,
                endpoint=normalized_path,
                status=status
            ).inc()

            return response

        except Exception as e:
            # Track exception
            exceptions_total.labels(
                exception_type=type(e).__name__,
                endpoint=normalized_path
            ).inc()
            raise

        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=normalized_path).dec()

    def _normalize_path(self, path: str) -> str:
        """Normalize path by removing UUIDs and IDs"""
        import re
        # Replace UUIDs
        path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path, flags=re.IGNORECASE)
        # Replace numeric IDs
        path = re.sub(r'/\d+/', '/{id}/', path)
        # Replace trailing numeric IDs
        path = re.sub(r'/\d+$', '/{id}', path)
        return path


# =============================================================================
# METRICS EXPORT
# =============================================================================

def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    # Update resource metrics before exporting
    update_resource_metrics()
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST

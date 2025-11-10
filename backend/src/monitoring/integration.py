"""
Integration helper for adding monitoring to FastAPI app
"""

from fastapi import FastAPI, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from .metrics import PrometheusMiddleware, get_metrics, get_metrics_content_type, app_info, app_uptime_seconds
from .health import get_health_status
import time

# Store app start time
_app_start_time = time.time()


def setup_monitoring(app: FastAPI, version: str = "1.0.0"):
    """
    Setup monitoring for FastAPI app.

    This adds:
    - Prometheus middleware for request tracking
    - /metrics endpoint for Prometheus scraping
    - /health endpoint for health checks
    """

    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)

    # Set app info
    app_info.info({
        'version': version,
        'name': 'SupoClip Backend'
    })

    # Add metrics endpoint
    @app.get(
        "/metrics",
        summary="Prometheus Metrics",
        description="Endpoint for Prometheus to scrape metrics",
        tags=["Monitoring"],
        include_in_schema=True,
        responses={
            200: {
                "description": "Prometheus metrics in text format",
                "content": {
                    "text/plain": {
                        "example": """# HELP supoclip_http_requests_total Total HTTP requests
# TYPE supoclip_http_requests_total counter
supoclip_http_requests_total{method="GET",endpoint="/",status="200"} 42.0"""
                    }
                }
            }
        }
    )
    async def metrics():
        """Prometheus metrics endpoint"""
        # Update uptime
        app_uptime_seconds.set(time.time() - _app_start_time)

        metrics_data = get_metrics()
        return Response(
            content=metrics_data,
            media_type=get_metrics_content_type()
        )

    # Add health endpoint
    @app.get(
        "/health",
        summary="Health Check",
        description="""
Comprehensive health check endpoint that verifies:
- Database connectivity
- Redis connectivity (optional)
- Disk space availability
- Memory usage
- CPU usage
- Worker status

Returns status:
- `healthy`: All systems operational
- `degraded`: Some non-critical issues detected
- `unhealthy`: Critical issues detected

This endpoint is used by:
- Docker health checks
- Load balancer health checks
- Monitoring systems (Prometheus, Grafana)
- Alerting systems (PagerDuty, etc.)
        """,
        tags=["Monitoring"],
        responses={
            200: {
                "description": "Health check results",
                "content": {
                    "application/json": {
                        "examples": {
                            "healthy": {
                                "summary": "All systems healthy",
                                "value": {
                                    "status": "healthy",
                                    "timestamp": "2025-11-10T12:00:00Z",
                                    "checks": [
                                        {
                                            "name": "database",
                                            "status": "healthy",
                                            "response_time_ms": 5.2,
                                            "details": {
                                                "pool_size": 10,
                                                "connections_in_use": 2,
                                                "overflow": 0
                                            }
                                        },
                                        {
                                            "name": "redis",
                                            "status": "healthy",
                                            "response_time_ms": 1.5,
                                            "details": {
                                                "version": "7.0",
                                                "used_memory_mb": 12.5,
                                                "connected_clients": 3
                                            }
                                        },
                                        {
                                            "name": "disk_space",
                                            "status": "healthy",
                                            "details": {
                                                "temp_dir": {
                                                    "path": "/tmp",
                                                    "total_gb": 100.0,
                                                    "used_gb": 45.5,
                                                    "free_gb": 54.5,
                                                    "used_percent": 45.5,
                                                    "healthy": True
                                                }
                                            }
                                        },
                                        {
                                            "name": "memory",
                                            "status": "healthy",
                                            "details": {
                                                "total_gb": 16.0,
                                                "used_gb": 8.5,
                                                "available_gb": 7.5,
                                                "used_percent": 53.1
                                            }
                                        },
                                        {
                                            "name": "cpu",
                                            "status": "healthy",
                                            "details": {
                                                "cpu_count": 8,
                                                "cpu_percent": 25.5
                                            }
                                        },
                                        {
                                            "name": "workers",
                                            "status": "healthy",
                                            "details": {
                                                "processing_tasks": 2,
                                                "stuck_tasks": 0
                                            }
                                        }
                                    ]
                                }
                            },
                            "degraded": {
                                "summary": "System degraded",
                                "value": {
                                    "status": "degraded",
                                    "timestamp": "2025-11-10T12:00:00Z",
                                    "checks": [
                                        {
                                            "name": "memory",
                                            "status": "degraded",
                                            "details": {
                                                "used_percent": 92.5
                                            }
                                        }
                                    ]
                                }
                            },
                            "unhealthy": {
                                "summary": "Critical issues",
                                "value": {
                                    "status": "unhealthy",
                                    "timestamp": "2025-11-10T12:00:00Z",
                                    "checks": [
                                        {
                                            "name": "database",
                                            "status": "unhealthy",
                                            "error": "Connection refused"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    async def health(db: AsyncSession = Depends(get_db_dependency)):
        """Comprehensive health check endpoint"""
        health_status = await get_health_status(db)
        return health_status


# This function needs to be provided by the app
def get_db_dependency():
    """Import and return the get_db dependency"""
    from ..database import get_db
    return get_db

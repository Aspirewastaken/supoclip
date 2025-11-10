"""
Performance monitoring and autoscaling API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from ...utils.performance import (
    performance_monitor,
    WorkerAutoscaler,
    get_gpu_info,
    video_cache
)
from ...utils.preprocessing_queue import get_preprocessing_queue

router = APIRouter(prefix="/performance", tags=["performance"])
logger = logging.getLogger(__name__)


@router.get("/gpu-info")
async def get_gpu_information():
    """Get GPU acceleration information."""
    try:
        gpu_info = get_gpu_info()
        return {
            "available": gpu_info.available,
            "name": gpu_info.name,
            "driver_version": gpu_info.driver_version,
            "cuda_available": gpu_info.cuda_available,
            "nvenc_available": gpu_info.nvenc_available,
            "recommended_encoder": gpu_info.recommended_encoder
        }
    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-metrics")
async def get_system_metrics():
    """Get current system resource metrics."""
    try:
        metrics = WorkerAutoscaler.get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue-stats")
async def get_queue_statistics():
    """Get preprocessing queue statistics."""
    try:
        queue = get_preprocessing_queue()
        stats = queue.get_queue_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worker-recommendations")
async def get_worker_recommendations(
    avg_processing_time_seconds: float = 120.0
):
    """
    Get worker autoscaling recommendations.

    Args:
        avg_processing_time_seconds: Average time to process one video (default: 120s)
    """
    try:
        queue = get_preprocessing_queue()
        queue_stats = queue.get_queue_stats()
        queue_size = queue_stats['queue_size']

        recommendations = WorkerAutoscaler.recommend_worker_count(
            queue_size=queue_size,
            avg_processing_time_seconds=avg_processing_time_seconds
        )

        # Add current worker count
        recommendations['current_workers'] = queue_stats['active_tasks']
        recommendations['max_workers'] = queue_stats['max_concurrent_tasks']

        # Check if scaling is needed
        current_workers = queue_stats['max_concurrent_tasks']
        system_metrics = recommendations['current_metrics']

        should_scale_up, scale_up_reason = WorkerAutoscaler.should_scale_up(
            current_workers=current_workers,
            queue_size=queue_size,
            avg_cpu_percent=system_metrics['cpu_percent']
        )

        should_scale_down, scale_down_reason = WorkerAutoscaler.should_scale_down(
            current_workers=current_workers,
            queue_size=queue_size,
            avg_cpu_percent=system_metrics['cpu_percent']
        )

        recommendations['scaling_recommendations'] = {
            'should_scale_up': should_scale_up,
            'scale_up_reason': scale_up_reason,
            'should_scale_down': should_scale_down,
            'scale_down_reason': scale_down_reason
        }

        return recommendations

    except Exception as e:
        logger.error(f"Error getting worker recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-stats")
async def get_cache_statistics():
    """Get video cache statistics."""
    try:
        import os
        cache_dir = video_cache.cache_dir

        if not cache_dir.exists():
            return {
                "cache_dir": str(cache_dir),
                "exists": False,
                "file_count": 0,
                "total_size_mb": 0
            }

        # Count files and calculate size
        cache_files = list(cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_dir": str(cache_dir),
            "exists": True,
            "file_count": len(cache_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(max_age_hours: int = 24):
    """
    Clear old cache entries.

    Args:
        max_age_hours: Maximum age in hours for cache entries
    """
    try:
        video_cache.clear_old_cache(max_age_hours)
        return {
            "message": f"Cache cleared (entries older than {max_age_hours} hours)",
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/recent")
async def get_recent_metrics(limit: int = 100):
    """
    Get recent performance metrics.

    Args:
        limit: Maximum number of metrics to return
    """
    try:
        recent_metrics = performance_monitor.metrics[-limit:]
        return {
            "count": len(recent_metrics),
            "metrics": [m.to_dict() for m in recent_metrics]
        }
    except Exception as e:
        logger.error(f"Error getting recent metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/save")
async def save_metrics():
    """Save current metrics to file."""
    try:
        performance_monitor.save_metrics()
        return {"message": "Metrics saved successfully"}
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def performance_health_check():
    """
    Comprehensive health check including performance metrics.
    """
    try:
        system_metrics = WorkerAutoscaler.get_system_metrics()
        queue_stats = get_preprocessing_queue().get_queue_stats()
        gpu_info = get_gpu_info()

        # Determine health status
        health_status = "healthy"
        warnings = []

        if system_metrics['cpu_percent'] > 90:
            warnings.append("High CPU usage")
            health_status = "degraded"

        if system_metrics['memory_percent'] > 90:
            warnings.append("High memory usage")
            health_status = "degraded"

        if system_metrics['disk_percent'] > 90:
            warnings.append("Low disk space")
            health_status = "degraded"

        if queue_stats['queue_size'] > 20:
            warnings.append("Large queue backlog")

        return {
            "status": health_status,
            "warnings": warnings,
            "system_metrics": system_metrics,
            "queue_stats": queue_stats,
            "gpu_available": gpu_info.available,
            "timestamp": performance_monitor.metrics[-1].to_dict()['operation'] if performance_monitor.metrics else None
        }

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

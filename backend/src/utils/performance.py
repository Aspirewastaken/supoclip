"""
Performance optimization utilities for video processing.

This module provides utilities for:
- GPU acceleration detection and configuration
- Parallel processing for multiple clips
- Caching layer for frequently used operations
- Performance monitoring and benchmarking
- Worker autoscaling recommendations
"""

import os
import time
import logging
import hashlib
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from functools import wraps
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import asyncio
from dataclasses import dataclass, asdict
import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for video processing operations."""
    operation: str
    duration_seconds: float
    cpu_percent: float
    memory_mb: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GPUInfo:
    """GPU information for acceleration."""
    available: bool
    name: Optional[str] = None
    driver_version: Optional[str] = None
    cuda_available: bool = False
    nvenc_available: bool = False
    recommended_encoder: str = "libx264"  # fallback to CPU


class PerformanceMonitor:
    """Monitor and log performance metrics for video processing."""

    def __init__(self, log_file: Optional[Path] = None):
        self.metrics: List[PerformanceMetrics] = []
        self.log_file = log_file or Path("logs/performance_metrics.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def record_metric(self, metric: PerformanceMetrics):
        """Record a performance metric."""
        self.metrics.append(metric)
        logger.info(
            f"Performance: {metric.operation} - "
            f"Duration: {metric.duration_seconds:.2f}s, "
            f"CPU: {metric.cpu_percent:.1f}%, "
            f"Memory: {metric.memory_mb:.1f}MB"
        )

    def save_metrics(self):
        """Save metrics to JSON file."""
        try:
            with open(self.log_file, 'a') as f:
                for metric in self.metrics:
                    json.dump(metric.to_dict(), f)
                    f.write('\n')
            self.metrics.clear()
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")

    def benchmark(self, operation_name: str):
        """Decorator to benchmark function performance."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                process = psutil.Process()
                start_time = time.time()
                start_cpu = process.cpu_percent()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB

                error = None
                success = True
                result = None

                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    error = str(e)
                    success = False
                    raise
                finally:
                    end_time = time.time()
                    end_cpu = process.cpu_percent()
                    end_memory = process.memory_info().rss / 1024 / 1024

                    metric = PerformanceMetrics(
                        operation=operation_name,
                        duration_seconds=end_time - start_time,
                        cpu_percent=(start_cpu + end_cpu) / 2,
                        memory_mb=end_memory - start_memory,
                        success=success,
                        error=error
                    )
                    self.record_metric(metric)

                return result
            return wrapper
        return decorator

    async def async_benchmark(self, operation_name: str):
        """Async decorator to benchmark async function performance."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                process = psutil.Process()
                start_time = time.time()
                start_cpu = process.cpu_percent()
                start_memory = process.memory_info().rss / 1024 / 1024

                error = None
                success = True
                result = None

                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    error = str(e)
                    success = False
                    raise
                finally:
                    end_time = time.time()
                    end_cpu = process.cpu_percent()
                    end_memory = process.memory_info().rss / 1024 / 1024

                    metric = PerformanceMetrics(
                        operation=operation_name,
                        duration_seconds=end_time - start_time,
                        cpu_percent=(start_cpu + end_cpu) / 2,
                        memory_mb=end_memory - start_memory,
                        success=success,
                        error=error
                    )
                    self.record_metric(metric)

                return result
            return wrapper
        return decorator


class GPUAccelerator:
    """Detect and configure GPU acceleration for FFmpeg."""

    @staticmethod
    def detect_gpu() -> GPUInfo:
        """Detect available GPU and encoding capabilities."""
        gpu_info = GPUInfo(available=False)

        try:
            # Check for NVIDIA GPU using nvidia-smi
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(',')
                gpu_info.available = True
                gpu_info.name = gpu_data[0].strip()
                gpu_info.driver_version = gpu_data[1].strip() if len(gpu_data) > 1 else None
                logger.info(f"NVIDIA GPU detected: {gpu_info.name}")

                # Check for NVENC support
                nvenc_result = subprocess.run(
                    ['ffmpeg', '-hide_banner', '-encoders'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if 'h264_nvenc' in nvenc_result.stdout or 'hevc_nvenc' in nvenc_result.stdout:
                    gpu_info.nvenc_available = True
                    gpu_info.recommended_encoder = 'h264_nvenc'
                    logger.info("NVENC hardware encoder available")
                else:
                    logger.warning("NVENC encoder not found in FFmpeg")

        except FileNotFoundError:
            logger.info("nvidia-smi not found - no NVIDIA GPU detected")
        except subprocess.TimeoutExpired:
            logger.warning("GPU detection timed out")
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")

        # Check for Intel Quick Sync (QSV)
        if not gpu_info.nvenc_available:
            try:
                qsv_result = subprocess.run(
                    ['ffmpeg', '-hide_banner', '-encoders'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if 'h264_qsv' in qsv_result.stdout:
                    gpu_info.available = True
                    gpu_info.name = "Intel Quick Sync"
                    gpu_info.recommended_encoder = 'h264_qsv'
                    logger.info("Intel Quick Sync encoder available")

            except Exception as e:
                logger.debug(f"QSV detection failed: {e}")

        # Check for AMD VCE/VCN
        if not gpu_info.nvenc_available and gpu_info.recommended_encoder == 'libx264':
            try:
                amd_result = subprocess.run(
                    ['ffmpeg', '-hide_banner', '-encoders'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if 'h264_amf' in amd_result.stdout:
                    gpu_info.available = True
                    gpu_info.name = "AMD VCE/VCN"
                    gpu_info.recommended_encoder = 'h264_amf'
                    logger.info("AMD VCE/VCN encoder available")

            except Exception as e:
                logger.debug(f"AMD encoder detection failed: {e}")

        return gpu_info

    @staticmethod
    def get_optimized_encoding_params(
        quality: str = "high",
        gpu_info: Optional[GPUInfo] = None
    ) -> Dict[str, Any]:
        """Get optimized encoding parameters based on available hardware."""
        if gpu_info is None:
            gpu_info = GPUAccelerator.detect_gpu()

        # Base parameters
        params = {
            "codec": gpu_info.recommended_encoder,
            "audio_codec": "aac",
            "preset": "medium",
        }

        # GPU-specific optimizations
        if gpu_info.nvenc_available:
            # NVENC parameters
            if quality == "high":
                params.update({
                    "preset": "p7",  # Best quality preset for NVENC
                    "bitrate": "8000k",
                    "audio_bitrate": "256k",
                    "ffmpeg_params": [
                        "-rc", "vbr",  # Variable bitrate
                        "-cq", "19",   # Quality level (lower = better)
                        "-b:v", "8M",
                        "-maxrate:v", "12M",
                        "-bufsize:v", "16M",
                        "-pix_fmt", "yuv420p",
                        "-profile:v", "high",
                        "-level", "4.1",
                        "-gpu", "0"  # Use first GPU
                    ]
                })
            else:  # medium quality
                params.update({
                    "preset": "p4",  # Balanced preset
                    "bitrate": "4000k",
                    "audio_bitrate": "192k",
                    "ffmpeg_params": [
                        "-rc", "vbr",
                        "-cq", "23",
                        "-b:v", "4M",
                        "-pix_fmt", "yuv420p"
                    ]
                })

        elif gpu_info.recommended_encoder == 'h264_qsv':
            # Intel Quick Sync parameters
            if quality == "high":
                params.update({
                    "preset": "veryslow",
                    "bitrate": "8000k",
                    "audio_bitrate": "256k",
                    "ffmpeg_params": [
                        "-global_quality", "20",
                        "-look_ahead", "1",
                        "-pix_fmt", "yuv420p"
                    ]
                })
            else:
                params.update({
                    "preset": "medium",
                    "bitrate": "4000k",
                    "audio_bitrate": "192k",
                    "ffmpeg_params": ["-global_quality", "23", "-pix_fmt", "yuv420p"]
                })

        elif gpu_info.recommended_encoder == 'h264_amf':
            # AMD VCE/VCN parameters
            if quality == "high":
                params.update({
                    "bitrate": "8000k",
                    "audio_bitrate": "256k",
                    "ffmpeg_params": [
                        "-quality", "quality",
                        "-rc", "vbr_peak",
                        "-qp_i", "20",
                        "-qp_p", "22",
                        "-pix_fmt", "yuv420p"
                    ]
                })
            else:
                params.update({
                    "bitrate": "4000k",
                    "audio_bitrate": "192k",
                    "ffmpeg_params": [
                        "-quality", "balanced",
                        "-rc", "vbr_peak",
                        "-pix_fmt", "yuv420p"
                    ]
                })

        else:
            # CPU fallback (libx264)
            if quality == "high":
                params.update({
                    "preset": "medium",
                    "bitrate": "8000k",
                    "audio_bitrate": "256k",
                    "ffmpeg_params": [
                        "-crf", "20",
                        "-pix_fmt", "yuv420p",
                        "-profile:v", "main",
                        "-level", "4.1"
                    ]
                })
            else:
                params.update({
                    "preset": "fast",
                    "bitrate": "4000k",
                    "audio_bitrate": "192k",
                    "ffmpeg_params": ["-crf", "23", "-pix_fmt", "yuv420p"]
                })

        logger.info(f"Using encoder: {params['codec']} (quality: {quality})")
        return params


class VideoCache:
    """Caching layer for video processing operations."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("temp/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key from operation and parameters."""
        key_data = f"{operation}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, operation: str, *args, **kwargs) -> Optional[Any]:
        """Get cached result if available."""
        cache_key = self._get_cache_key(operation, *args, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Check if cache is still valid (24 hour TTL)
                    cache_time = cached_data.get('timestamp', 0)
                    if time.time() - cache_time < 86400:  # 24 hours
                        logger.info(f"Cache hit for {operation}")
                        return cached_data.get('result')
                    else:
                        logger.info(f"Cache expired for {operation}")
                        cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
                cache_file.unlink(missing_ok=True)

        return None

    def set(self, operation: str, result: Any, *args, **kwargs):
        """Cache operation result."""
        cache_key = self._get_cache_key(operation, *args, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            cache_data = {
                'operation': operation,
                'timestamp': time.time(),
                'result': result
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            logger.info(f"Cached result for {operation}")
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def clear_old_cache(self, max_age_hours: int = 24):
        """Clear cache entries older than max_age_hours."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleared_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_seconds:
                    cache_file.unlink()
                    cleared_count += 1
            except Exception as e:
                logger.warning(f"Failed to check/delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {cleared_count} old cache entries")


class ParallelProcessor:
    """Parallel processing utilities for video clips."""

    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize parallel processor.

        Args:
            max_workers: Maximum number of parallel workers.
                        If None, uses CPU count - 1 (leaves one core free)
        """
        self.max_workers = max_workers or max(1, os.cpu_count() - 1)
        logger.info(f"Parallel processor initialized with {self.max_workers} workers")

    def process_clips_parallel(
        self,
        clip_tasks: List[Tuple[Callable, tuple, dict]],
        use_processes: bool = False
    ) -> List[Any]:
        """
        Process multiple clips in parallel.

        Args:
            clip_tasks: List of (function, args, kwargs) tuples
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
                          (better for CPU-intensive tasks, but higher overhead)

        Returns:
            List of results in the same order as input tasks
        """
        executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        results = [None] * len(clip_tasks)

        logger.info(f"Processing {len(clip_tasks)} clips in parallel using {executor_class.__name__}")

        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {}
            for i, (func, args, kwargs) in enumerate(clip_tasks):
                future = executor.submit(func, *args, **kwargs)
                future_to_index[future] = i

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                    completed += 1
                    logger.info(f"Clip {completed}/{len(clip_tasks)} completed")
                except Exception as e:
                    logger.error(f"Clip {index} failed: {e}")
                    results[index] = None

        successful = sum(1 for r in results if r is not None)
        logger.info(f"Parallel processing complete: {successful}/{len(clip_tasks)} successful")

        return results

    async def process_clips_async(
        self,
        clip_tasks: List[Tuple[Callable, tuple, dict]]
    ) -> List[Any]:
        """
        Process multiple clips asynchronously.

        Args:
            clip_tasks: List of (async_function, args, kwargs) tuples

        Returns:
            List of results in the same order as input tasks
        """
        logger.info(f"Processing {len(clip_tasks)} clips asynchronously")

        tasks = []
        for func, args, kwargs in clip_tasks:
            task = func(*args, **kwargs)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Async processing complete: {successful}/{len(clip_tasks)} successful")

        return results


class WorkerAutoscaler:
    """Recommendations for worker autoscaling based on system metrics."""

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_percent': cpu_percent,
            'cpu_count': os.cpu_count(),
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / 1024 / 1024 / 1024,
            'memory_total_gb': memory.total / 1024 / 1024 / 1024,
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / 1024 / 1024 / 1024
        }

    @staticmethod
    def recommend_worker_count(
        queue_size: int,
        avg_processing_time_seconds: float
    ) -> Dict[str, Any]:
        """
        Recommend optimal worker count based on queue and system metrics.

        Args:
            queue_size: Number of tasks in queue
            avg_processing_time_seconds: Average time to process one task

        Returns:
            Dictionary with recommendations
        """
        metrics = WorkerAutoscaler.get_system_metrics()

        # Calculate base recommendation
        cpu_count = metrics['cpu_count']
        current_cpu = metrics['cpu_percent']
        memory_available = metrics['memory_available_gb']

        # Rule of thumb: 1 worker per 2 CPU cores (leave room for system)
        max_cpu_workers = max(1, cpu_count // 2)

        # Memory constraint: assume each worker needs ~2GB
        max_memory_workers = max(1, int(memory_available // 2))

        # Queue-based recommendation
        # If queue is large and CPU is not saturated, recommend more workers
        if queue_size > 10 and current_cpu < 80:
            queue_workers = min(queue_size // 5, cpu_count)
        elif queue_size > 5:
            queue_workers = min(queue_size // 3, cpu_count // 2)
        else:
            queue_workers = 1

        # Take the minimum to ensure we don't overload
        recommended_workers = min(max_cpu_workers, max_memory_workers, queue_workers)

        # Estimated time to clear queue
        estimated_time_minutes = (queue_size * avg_processing_time_seconds) / (recommended_workers * 60)

        recommendation = {
            'recommended_workers': recommended_workers,
            'max_cpu_workers': max_cpu_workers,
            'max_memory_workers': max_memory_workers,
            'queue_based_workers': queue_workers,
            'estimated_queue_clear_minutes': round(estimated_time_minutes, 1),
            'current_metrics': metrics,
            'reasoning': []
        }

        # Add reasoning
        if current_cpu > 80:
            recommendation['reasoning'].append("CPU usage high - limiting workers")
        if memory_available < 4:
            recommendation['reasoning'].append("Low memory - limiting workers")
        if queue_size > 20:
            recommendation['reasoning'].append("Large queue - consider scaling up")

        return recommendation

    @staticmethod
    def should_scale_up(
        current_workers: int,
        queue_size: int,
        avg_cpu_percent: float,
        max_workers: int = 8
    ) -> Tuple[bool, str]:
        """
        Determine if workers should be scaled up.

        Returns:
            (should_scale, reason)
        """
        if current_workers >= max_workers:
            return False, "Already at max workers"

        if queue_size > current_workers * 5 and avg_cpu_percent < 80:
            return True, f"Queue size ({queue_size}) exceeds threshold and CPU not saturated"

        if queue_size > 20 and avg_cpu_percent < 70:
            return True, "Large queue and available CPU capacity"

        return False, "No scaling needed"

    @staticmethod
    def should_scale_down(
        current_workers: int,
        queue_size: int,
        avg_cpu_percent: float,
        min_workers: int = 1
    ) -> Tuple[bool, str]:
        """
        Determine if workers should be scaled down.

        Returns:
            (should_scale, reason)
        """
        if current_workers <= min_workers:
            return False, "Already at min workers"

        if queue_size == 0 and current_workers > 1:
            return True, "Queue empty - scale down to minimum"

        if queue_size < current_workers and avg_cpu_percent < 30:
            return True, "Low queue size and CPU utilization"

        return False, "No scaling needed"


# Global instances for convenience
performance_monitor = PerformanceMonitor()
video_cache = VideoCache()
parallel_processor = ParallelProcessor()


def get_gpu_info() -> GPUInfo:
    """Get GPU information (convenience function)."""
    return GPUAccelerator.detect_gpu()


def get_optimized_ffmpeg_params(quality: str = "high") -> Dict[str, Any]:
    """Get optimized FFmpeg parameters based on available hardware."""
    gpu_info = get_gpu_info()
    return GPUAccelerator.get_optimized_encoding_params(quality, gpu_info)

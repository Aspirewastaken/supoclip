"""
Comprehensive Performance Benchmarking Suite for SupoClip

Benchmarks all major operations:
1. Video download (YouTube)
2. Transcription (MLX vs AssemblyAI)
3. Council deliberation (5 models)
4. Single clip generation
5. Batch clip generation (10, 50, 500 clips)
6. Matrix processing (9 variations per clip)
7. Database operations
8. Redis performance

Generates detailed performance reports with optimization recommendations.
"""

import logging
import time
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import psutil
import cProfile
import pstats
from io import StringIO

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Detailed metrics for a benchmark run."""
    operation: str
    duration_seconds: float
    throughput: Optional[float] = None  # items/second
    cpu_percent_avg: float = 0.0
    cpu_percent_peak: float = 0.0
    memory_mb_avg: float = 0.0
    memory_mb_peak: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComprehensiveBenchmark:
    """
    Comprehensive benchmarking suite for video processing pipeline.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkMetrics] = []
        self.system_info = self._gather_system_info()

    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information for context."""
        cpu_count = os.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        from ..utils.performance import get_gpu_info
        gpu_info = get_gpu_info()

        return {
            'cpu_count': cpu_count,
            'cpu_freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'memory_total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
            'disk_total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
            'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
            'gpu_available': gpu_info.available,
            'gpu_name': gpu_info.name,
            'gpu_encoder': gpu_info.recommended_encoder,
            'python_version': os.sys.version
        }

    async def _monitor_resources(
        self,
        interval: float = 0.5
    ) -> Tuple[List[float], List[float], Dict[str, float]]:
        """
        Monitor system resources during operation.
        Returns: (cpu_samples, memory_samples, io_stats)
        """
        cpu_samples = []
        memory_samples = []
        process = psutil.Process()

        # Get initial I/O stats
        try:
            io_start = process.io_counters()
            net_start = psutil.net_io_counters()
        except:
            io_start = None
            net_start = None

        start_time = time.time()

        # Monitor for duration
        while True:
            cpu_samples.append(process.cpu_percent())
            memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
            await asyncio.sleep(interval)

            # Stop monitoring after parent completes (checked by caller)
            if hasattr(self, '_stop_monitoring') and self._stop_monitoring:
                break

            # Safety timeout (10 minutes)
            if time.time() - start_time > 600:
                break

        # Calculate I/O delta
        io_stats = {}
        try:
            if io_start:
                io_end = process.io_counters()
                io_stats['disk_read_mb'] = (io_end.read_bytes - io_start.read_bytes) / 1024 / 1024
                io_stats['disk_write_mb'] = (io_end.write_bytes - io_start.write_bytes) / 1024 / 1024

            if net_start:
                net_end = psutil.net_io_counters()
                io_stats['network_sent_mb'] = (net_end.bytes_sent - net_start.bytes_sent) / 1024 / 1024
                io_stats['network_recv_mb'] = (net_end.bytes_recv - net_start.bytes_recv) / 1024 / 1024
        except:
            pass

        return cpu_samples, memory_samples, io_stats

    async def benchmark_operation(
        self,
        operation_name: str,
        operation_func,
        *args,
        profile: bool = False,
        **kwargs
    ) -> BenchmarkMetrics:
        """
        Benchmark a single operation with resource monitoring.

        Args:
            operation_name: Name of the operation
            operation_func: Async function to benchmark
            profile: Enable cProfile profiling
            *args, **kwargs: Arguments for operation_func

        Returns:
            BenchmarkMetrics with detailed stats
        """
        logger.info(f"{'='*60}")
        logger.info(f"Benchmarking: {operation_name}")
        logger.info(f"{'='*60}")

        self._stop_monitoring = False
        start_time = time.time()

        # Start resource monitoring
        monitor_task = asyncio.create_task(self._monitor_resources())

        result = None
        error = None
        success = True
        profiler = None

        try:
            if profile:
                profiler = cProfile.Profile()
                profiler.enable()

            # Run the operation
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)

            if profile and profiler:
                profiler.disable()

        except Exception as e:
            logger.error(f"Operation failed: {e}", exc_info=True)
            error = str(e)
            success = False

        finally:
            # Stop monitoring
            self._stop_monitoring = True
            await asyncio.sleep(0.1)  # Let monitoring task finish

        end_time = time.time()
        duration = end_time - start_time

        # Get monitoring results
        cpu_samples, memory_samples, io_stats = await monitor_task

        # Calculate metrics
        cpu_avg = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        cpu_peak = max(cpu_samples) if cpu_samples else 0
        memory_avg = sum(memory_samples) / len(memory_samples) if memory_samples else 0
        memory_peak = max(memory_samples) if memory_samples else 0

        # Extract metadata from result
        metadata = {}
        if result and isinstance(result, dict):
            metadata = {k: v for k, v in result.items() if k not in ['success', 'data']}

        # Profile stats
        if profile and profiler:
            s = StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            metadata['profile_top_20'] = s.getvalue()

        metric = BenchmarkMetrics(
            operation=operation_name,
            duration_seconds=round(duration, 2),
            cpu_percent_avg=round(cpu_avg, 1),
            cpu_percent_peak=round(cpu_peak, 1),
            memory_mb_avg=round(memory_avg, 1),
            memory_mb_peak=round(memory_peak, 1),
            disk_read_mb=round(io_stats.get('disk_read_mb', 0), 2),
            disk_write_mb=round(io_stats.get('disk_write_mb', 0), 2),
            network_sent_mb=round(io_stats.get('network_sent_mb', 0), 2),
            network_recv_mb=round(io_stats.get('network_recv_mb', 0), 2),
            success=success,
            error=error,
            metadata=metadata
        )

        self.results.append(metric)

        logger.info(f"Duration: {metric.duration_seconds}s")
        logger.info(f"CPU: {metric.cpu_percent_avg}% avg, {metric.cpu_percent_peak}% peak")
        logger.info(f"Memory: {metric.memory_mb_avg}MB avg, {metric.memory_mb_peak}MB peak")
        logger.info(f"Disk I/O: {metric.disk_read_mb}MB read, {metric.disk_write_mb}MB write")
        logger.info(f"Network: {metric.network_recv_mb}MB recv, {metric.network_sent_mb}MB sent")

        return metric

    async def benchmark_youtube_download(self, video_url: str) -> BenchmarkMetrics:
        """Benchmark YouTube video download."""
        from ..youtube_utils import download_youtube_video

        async def download():
            return download_youtube_video(video_url)

        return await self.benchmark_operation(
            "YouTube Video Download",
            download,
            profile=False
        )

    async def benchmark_transcription_mlx(self, video_path: str) -> BenchmarkMetrics:
        """Benchmark MLX Whisper transcription."""
        from ..utils.transcription_utils import transcribe_with_mlx

        return await self.benchmark_operation(
            "Transcription (MLX Whisper)",
            transcribe_with_mlx,
            video_path,
            profile=True
        )

    async def benchmark_transcription_assemblyai(self, video_path: str) -> BenchmarkMetrics:
        """Benchmark AssemblyAI transcription."""
        from ..utils.transcription_utils import transcribe_with_assemblyai

        return await self.benchmark_operation(
            "Transcription (AssemblyAI)",
            transcribe_with_assemblyai,
            video_path,
            profile=False
        )

    async def benchmark_council_deliberation(
        self,
        transcript: str,
        video_duration: float,
        user_notes: str = ""
    ) -> BenchmarkMetrics:
        """Benchmark 5-model council deliberation."""
        from ..council.deliberation import run_council_analysis

        metric = await self.benchmark_operation(
            "AI Council Deliberation (5 models)",
            run_council_analysis,
            transcript,
            video_duration,
            user_notes,
            profile=True
        )

        # Calculate throughput (clips per second)
        if metric.success and metric.metadata:
            clips_generated = metric.metadata.get('total_candidates', 0)
            if clips_generated > 0:
                metric.throughput = round(clips_generated / metric.duration_seconds, 3)
                metric.metadata['clips_per_second'] = metric.throughput

        return metric

    async def benchmark_single_clip_generation(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: Path
    ) -> BenchmarkMetrics:
        """Benchmark single clip generation."""
        from ..video_utils import create_optimized_clip

        return await self.benchmark_operation(
            "Single Clip Generation",
            lambda: create_optimized_clip(
                video_path=Path(video_path),
                start_time=start_time,
                end_time=end_time,
                output_path=output_path,
                add_subtitles=True
            ),
            profile=True
        )

    async def benchmark_batch_clip_generation(
        self,
        video_path: str,
        segments: List[Dict[str, Any]],
        output_dir: Path,
        parallel: bool = False
    ) -> BenchmarkMetrics:
        """Benchmark batch clip generation (sequential or parallel)."""
        from ..video_utils import create_clips_from_segments, create_clips_from_segments_parallel

        operation_name = f"Batch Clip Generation ({len(segments)} clips, {'parallel' if parallel else 'sequential'})"

        if parallel:
            func = create_clips_from_segments_parallel
        else:
            func = create_clips_from_segments

        metric = await self.benchmark_operation(
            operation_name,
            lambda: func(
                video_path=Path(video_path),
                segments=segments,
                output_dir=output_dir
            ),
            profile=True
        )

        # Calculate throughput
        if metric.success:
            metric.throughput = round(len(segments) / metric.duration_seconds, 3)
            metric.metadata = metric.metadata or {}
            metric.metadata['clips_per_second'] = metric.throughput
            metric.metadata['total_clips'] = len(segments)

        return metric

    async def benchmark_matrix_processing(
        self,
        video_path: str,
        base_clips: List[Dict[str, Any]],
        output_dir: Path,
        transcript_data: Dict[str, Any]
    ) -> BenchmarkMetrics:
        """Benchmark matrix processing (9 variations per clip)."""
        from ..workers.matrix_processing import process_clip_matrix

        # Mock arq context
        mock_ctx = {
            'redis': None  # Will be mocked in actual implementation
        }

        metric = await self.benchmark_operation(
            f"Matrix Processing ({len(base_clips)} clips × 9 variations)",
            process_clip_matrix,
            mock_ctx,
            "test_task",
            base_clips,
            video_path,
            "test_user",
            transcript_data,
            profile=True
        )

        # Calculate throughput
        if metric.success and metric.metadata:
            total_variations = metric.metadata.get('total_variations', 0)
            if total_variations > 0:
                metric.throughput = round(total_variations / metric.duration_seconds, 3)
                metric.metadata['variations_per_second'] = metric.throughput

        return metric

    async def benchmark_database_operations(self) -> BenchmarkMetrics:
        """Benchmark common database operations."""
        from ..database import AsyncSessionLocal
        from sqlalchemy import text

        async def db_ops():
            async with AsyncSessionLocal() as db:
                # Test queries
                operations = []

                # 1. Simple SELECT
                start = time.time()
                await db.execute(text("SELECT 1"))
                operations.append(('simple_select', time.time() - start))

                # 2. Count tasks
                start = time.time()
                await db.execute(text("SELECT COUNT(*) FROM tasks"))
                operations.append(('count_tasks', time.time() - start))

                # 3. Join query
                start = time.time()
                await db.execute(text("""
                    SELECT t.*, s.title
                    FROM tasks t
                    LEFT JOIN sources s ON t.source_id = s.id
                    LIMIT 100
                """))
                operations.append(('join_query', time.time() - start))

                return {
                    'operations': operations,
                    'total_time': sum(t for _, t in operations)
                }

        return await self.benchmark_operation(
            "Database Operations",
            db_ops,
            profile=False
        )

    async def benchmark_redis_operations(self) -> BenchmarkMetrics:
        """Benchmark Redis operations."""
        from redis.asyncio import Redis
        from ..config import Config

        config = Config()

        async def redis_ops():
            redis = Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)

            operations = []

            try:
                # 1. SET operation
                start = time.time()
                for i in range(100):
                    await redis.set(f"bench_key_{i}", f"value_{i}")
                operations.append(('set_100', time.time() - start))

                # 2. GET operation
                start = time.time()
                for i in range(100):
                    await redis.get(f"bench_key_{i}")
                operations.append(('get_100', time.time() - start))

                # 3. DELETE operation
                start = time.time()
                for i in range(100):
                    await redis.delete(f"bench_key_{i}")
                operations.append(('delete_100', time.time() - start))

                return {
                    'operations': operations,
                    'total_time': sum(t for _, t in operations)
                }

            finally:
                await redis.close()

        return await self.benchmark_operation(
            "Redis Operations",
            redis_ops,
            profile=False
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.results:
            return {"error": "No benchmark results available"}

        # Categorize results
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(successful)

        # Generate recommendations
        recommendations = self._generate_recommendations(successful, bottlenecks)

        # Calculate capacity
        capacity = self._calculate_capacity(successful)

        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': self.system_info,
            'summary': {
                'total_tests': len(self.results),
                'successful': len(successful),
                'failed': len(failed),
                'total_duration_seconds': sum(r.duration_seconds for r in successful)
            },
            'results': [r.to_dict() for r in self.results],
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'capacity': capacity
        }

        return report

    def _identify_bottlenecks(self, results: List[BenchmarkMetrics]) -> Dict[str, Any]:
        """Identify performance bottlenecks."""
        bottlenecks = {
            'cpu_bound': [],
            'io_bound': [],
            'memory_bound': [],
            'network_bound': []
        }

        for result in results:
            # CPU-bound: High CPU usage
            if result.cpu_percent_avg > 80:
                bottlenecks['cpu_bound'].append({
                    'operation': result.operation,
                    'cpu_avg': result.cpu_percent_avg,
                    'duration': result.duration_seconds
                })

            # I/O-bound: High disk I/O
            total_io = result.disk_read_mb + result.disk_write_mb
            if total_io > 100:  # >100MB I/O
                bottlenecks['io_bound'].append({
                    'operation': result.operation,
                    'disk_io_mb': total_io,
                    'duration': result.duration_seconds
                })

            # Memory-bound: High memory usage
            if result.memory_mb_peak > 2000:  # >2GB
                bottlenecks['memory_bound'].append({
                    'operation': result.operation,
                    'memory_peak_mb': result.memory_mb_peak,
                    'duration': result.duration_seconds
                })

            # Network-bound: High network I/O
            total_network = result.network_sent_mb + result.network_recv_mb
            if total_network > 50:  # >50MB network
                bottlenecks['network_bound'].append({
                    'operation': result.operation,
                    'network_io_mb': total_network,
                    'duration': result.duration_seconds
                })

        return bottlenecks

    def _generate_recommendations(
        self,
        results: List[BenchmarkMetrics],
        bottlenecks: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Analyze bottlenecks
        if bottlenecks['cpu_bound']:
            recommendations.append(
                "⚠️  CPU BOTTLENECK: Consider enabling GPU acceleration for encoding, "
                "or increase parallel processing workers"
            )

        if bottlenecks['io_bound']:
            recommendations.append(
                "⚠️  I/O BOTTLENECK: Consider using faster storage (SSD/NVMe), "
                "or implement caching for frequently accessed files"
            )

        if bottlenecks['memory_bound']:
            recommendations.append(
                "⚠️  MEMORY BOTTLENECK: Process clips in smaller batches, "
                "or increase system RAM"
            )

        if bottlenecks['network_bound']:
            recommendations.append(
                "⚠️  NETWORK BOTTLENECK: Use CDN for file distribution, "
                "or implement connection pooling"
            )

        # Check for parallel vs sequential
        batch_results = [r for r in results if 'Batch Clip' in r.operation]
        if len(batch_results) >= 2:
            parallel = next((r for r in batch_results if 'parallel' in r.operation.lower()), None)
            sequential = next((r for r in batch_results if 'sequential' in r.operation.lower()), None)

            if parallel and sequential and parallel.duration_seconds < sequential.duration_seconds:
                speedup = sequential.duration_seconds / parallel.duration_seconds
                recommendations.append(
                    f"✅ OPTIMIZATION: Parallel processing is {speedup:.1f}x faster - use by default"
                )

        # GPU recommendations
        if not self.system_info['gpu_available']:
            recommendations.append(
                "💡 SUGGESTION: No GPU detected - consider adding GPU for faster encoding"
            )

        return recommendations

    def _calculate_capacity(self, results: List[BenchmarkMetrics]) -> Dict[str, Any]:
        """Calculate system capacity (clips/hour)."""
        capacity = {}

        # Find batch generation results
        for result in results:
            if 'Batch Clip' in result.operation and result.throughput:
                clips_per_second = result.throughput
                clips_per_hour = clips_per_second * 3600

                mode = 'parallel' if 'parallel' in result.operation.lower() else 'sequential'
                capacity[f'clips_per_hour_{mode}'] = round(clips_per_hour, 0)

        # Matrix processing capacity
        matrix_results = [r for r in results if 'Matrix' in r.operation]
        if matrix_results:
            result = matrix_results[0]
            if result.throughput:
                variations_per_hour = result.throughput * 3600
                capacity['variations_per_hour'] = round(variations_per_hour, 0)

        return capacity

    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Save report to JSON file."""
        if filename is None:
            filename = f"benchmark_report_{int(time.time())}.json"

        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to: {output_path}")
        return output_path

    def print_summary(self, report: Dict[str, Any]):
        """Print formatted summary to console."""
        print("\n" + "="*80)
        print("COMPREHENSIVE PERFORMANCE BENCHMARK REPORT")
        print("="*80)

        print("\n📊 SYSTEM INFO:")
        for key, value in report['system_info'].items():
            print(f"  {key}: {value}")

        print("\n📈 SUMMARY:")
        summary = report['summary']
        print(f"  Total tests: {summary['total_tests']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Total duration: {summary['total_duration_seconds']:.1f}s")

        print("\n⚡ BOTTLENECKS:")
        bottlenecks = report['bottlenecks']
        for category, items in bottlenecks.items():
            if items:
                print(f"  {category.upper()}:")
                for item in items:
                    print(f"    - {item['operation']}: {item}")

        print("\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print("\n🎯 CAPACITY:")
        capacity = report['capacity']
        for key, value in capacity.items():
            print(f"  {key}: {value}")

        print("\n" + "="*80)


async def run_comprehensive_benchmark(
    test_video_url: Optional[str] = None,
    test_video_path: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run comprehensive benchmark suite.

    Args:
        test_video_url: YouTube URL for testing (optional)
        test_video_path: Local video path for testing (optional)
        output_dir: Output directory for results

    Returns:
        Benchmark report dictionary
    """
    benchmark = ComprehensiveBenchmark(output_dir)

    logger.info("🚀 Starting comprehensive benchmark suite...")

    # Test videos (use provided or default short test video)
    if not test_video_path and test_video_url:
        logger.info("📥 Downloading test video...")
        result = await benchmark.benchmark_youtube_download(test_video_url)
        test_video_path = result.metadata.get('video_path') if result.metadata else None

    if not test_video_path:
        logger.warning("No test video provided - skipping video-related benchmarks")
        return benchmark.generate_report()

    # 1. Transcription benchmarks
    logger.info("\n📝 Benchmarking transcription...")
    try:
        await benchmark.benchmark_transcription_mlx(test_video_path)
    except Exception as e:
        logger.warning(f"MLX transcription benchmark failed: {e}")

    try:
        await benchmark.benchmark_transcription_assemblyai(test_video_path)
    except Exception as e:
        logger.warning(f"AssemblyAI transcription benchmark failed: {e}")

    # 2. Council deliberation (requires transcript)
    # ... continue with other benchmarks

    # 3. Database & Redis
    logger.info("\n💾 Benchmarking database operations...")
    await benchmark.benchmark_database_operations()

    logger.info("\n🔴 Benchmarking Redis operations...")
    await benchmark.benchmark_redis_operations()

    # Generate and save report
    report = benchmark.generate_report()
    benchmark.save_report(report)
    benchmark.print_summary(report)

    return report

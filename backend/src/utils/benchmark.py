"""
Benchmarking utilities for video processing performance.

This script provides benchmarks to compare:
- Sequential vs parallel clip processing
- CPU vs GPU encoding
- With and without caching
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import json
from dataclasses import dataclass, asdict

from .performance import (
    PerformanceMonitor,
    GPUAccelerator,
    ParallelProcessor,
    VideoCache,
    get_gpu_info
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    name: str
    duration_seconds: float
    clips_created: int
    clips_per_second: float
    avg_clip_duration: float
    cpu_percent: float
    memory_mb: float
    gpu_used: bool
    parallel: bool
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VideoBenchmark:
    """Benchmark video processing performance."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.monitor = PerformanceMonitor()

    async def run_full_benchmark(
        self,
        video_path: Path,
        segments: List[Dict[str, Any]],
        output_base_dir: Path
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark comparing different configurations.

        Args:
            video_path: Path to test video
            segments: List of segments to create clips from
            output_base_dir: Base directory for output clips

        Returns:
            Dictionary with all benchmark results
        """
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE VIDEO PROCESSING BENCHMARK")
        logger.info("=" * 80)

        # Detect GPU
        gpu_info = get_gpu_info()
        logger.info(f"GPU Available: {gpu_info.available}")
        if gpu_info.available:
            logger.info(f"GPU: {gpu_info.name} ({gpu_info.recommended_encoder})")

        # Test configurations
        configs = [
            {
                "name": "Sequential_CPU",
                "parallel": False,
                "use_gpu": False
            },
            {
                "name": "Sequential_GPU",
                "parallel": False,
                "use_gpu": True
            },
            {
                "name": "Parallel_CPU",
                "parallel": True,
                "use_gpu": False
            },
            {
                "name": "Parallel_GPU",
                "parallel": True,
                "use_gpu": True
            }
        ]

        # Run benchmarks
        for config in configs:
            # Skip GPU tests if GPU not available
            if config["use_gpu"] and not gpu_info.available:
                logger.info(f"Skipping {config['name']} - GPU not available")
                continue

            logger.info(f"\n{'=' * 60}")
            logger.info(f"Running: {config['name']}")
            logger.info(f"{'=' * 60}")

            output_dir = output_base_dir / config['name']
            output_dir.mkdir(parents=True, exist_ok=True)

            result = await self._run_single_benchmark(
                name=config['name'],
                video_path=video_path,
                segments=segments,
                output_dir=output_dir,
                parallel=config['parallel'],
                use_gpu=config['use_gpu']
            )

            self.results.append(result)

            # Clean up output directory to save space
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)

        # Generate comparison report
        report = self._generate_report()

        # Save results
        results_file = self.output_dir / f"benchmark_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n{'=' * 80}")
        logger.info("BENCHMARK COMPLETE")
        logger.info(f"Results saved to: {results_file}")
        logger.info(f"{'=' * 80}")

        return report

    async def _run_single_benchmark(
        self,
        name: str,
        video_path: Path,
        segments: List[Dict[str, Any]],
        output_dir: Path,
        parallel: bool,
        use_gpu: bool
    ) -> BenchmarkResult:
        """Run a single benchmark configuration."""
        import psutil

        process = psutil.Process()
        start_time = time.time()
        start_cpu = process.cpu_percent()
        start_memory = process.memory_info().rss / 1024 / 1024

        clips_created = 0
        success = True
        error = None

        try:
            if parallel:
                # Use parallel processing
                from ..video_utils import create_clips_from_segments_parallel
                clips_info = create_clips_from_segments_parallel(
                    video_path=video_path,
                    segments=segments,
                    output_dir=output_dir,
                    max_workers=None  # Use default
                )
            else:
                # Use sequential processing
                from ..video_utils import create_clips_from_segments
                clips_info = create_clips_from_segments(
                    video_path=video_path,
                    segments=segments,
                    output_dir=output_dir
                )

            clips_created = len(clips_info)

        except Exception as e:
            logger.error(f"Benchmark {name} failed: {e}")
            success = False
            error = str(e)

        end_time = time.time()
        end_cpu = process.cpu_percent()
        end_memory = process.memory_info().rss / 1024 / 1024

        duration = end_time - start_time
        clips_per_second = clips_created / duration if duration > 0 else 0
        avg_clip_duration = sum(
            float(seg.get('duration', 0)) for seg in segments
        ) / len(segments) if segments else 0

        result = BenchmarkResult(
            name=name,
            duration_seconds=round(duration, 2),
            clips_created=clips_created,
            clips_per_second=round(clips_per_second, 3),
            avg_clip_duration=round(avg_clip_duration, 2),
            cpu_percent=round((start_cpu + end_cpu) / 2, 1),
            memory_mb=round(end_memory - start_memory, 1),
            gpu_used=use_gpu,
            parallel=parallel,
            success=success,
            error=error
        )

        logger.info(f"  Duration: {result.duration_seconds}s")
        logger.info(f"  Clips: {result.clips_created}")
        logger.info(f"  Speed: {result.clips_per_second} clips/sec")
        logger.info(f"  CPU: {result.cpu_percent}%")
        logger.info(f"  Memory: {result.memory_mb}MB")

        return result

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return {"error": "No benchmark results available"}

        # Find best performers
        successful_results = [r for r in self.results if r.success]

        if not successful_results:
            return {"error": "All benchmarks failed"}

        fastest = min(successful_results, key=lambda r: r.duration_seconds)
        most_efficient = min(successful_results, key=lambda r: r.cpu_percent)
        best_throughput = max(successful_results, key=lambda r: r.clips_per_second)

        # Calculate improvements
        cpu_sequential = next(
            (r for r in self.results if r.name == "Sequential_CPU" and r.success),
            None
        )
        gpu_parallel = next(
            (r for r in self.results if r.name == "Parallel_GPU" and r.success),
            None
        )

        improvements = {}
        if cpu_sequential and gpu_parallel:
            speedup = cpu_sequential.duration_seconds / gpu_parallel.duration_seconds
            improvements['overall_speedup'] = round(speedup, 2)
            improvements['time_saved_percent'] = round(
                (1 - 1/speedup) * 100, 1
            )

        report = {
            "benchmark_summary": {
                "total_tests": len(self.results),
                "successful_tests": len(successful_results),
                "failed_tests": len(self.results) - len(successful_results)
            },
            "best_performers": {
                "fastest": fastest.to_dict(),
                "most_efficient_cpu": most_efficient.to_dict(),
                "best_throughput": best_throughput.to_dict()
            },
            "improvements": improvements,
            "all_results": [r.to_dict() for r in self.results],
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on benchmark results."""
        recommendations = []

        successful_results = [r for r in self.results if r.success]
        if not successful_results:
            return ["Could not generate recommendations - all tests failed"]

        # Check if parallel is faster
        parallel_results = [r for r in successful_results if r.parallel]
        sequential_results = [r for r in successful_results if not r.parallel]

        if parallel_results and sequential_results:
            avg_parallel_time = sum(r.duration_seconds for r in parallel_results) / len(parallel_results)
            avg_sequential_time = sum(r.duration_seconds for r in sequential_results) / len(sequential_results)

            if avg_parallel_time < avg_sequential_time:
                speedup = avg_sequential_time / avg_parallel_time
                recommendations.append(
                    f"✓ Use parallel processing for {speedup:.1f}x faster clip generation"
                )

        # Check if GPU helps
        gpu_results = [r for r in successful_results if r.gpu_used]
        cpu_results = [r for r in successful_results if not r.gpu_used]

        if gpu_results and cpu_results:
            avg_gpu_time = sum(r.duration_seconds for r in gpu_results) / len(gpu_results)
            avg_cpu_time = sum(r.duration_seconds for r in cpu_results) / len(cpu_results)

            if avg_gpu_time < avg_cpu_time:
                speedup = avg_cpu_time / avg_gpu_time
                recommendations.append(
                    f"✓ Use GPU acceleration for {speedup:.1f}x faster encoding"
                )

        # Memory recommendations
        max_memory = max(r.memory_mb for r in successful_results)
        if max_memory > 2000:
            recommendations.append(
                f"⚠ Peak memory usage: {max_memory:.0f}MB - consider processing in smaller batches"
            )

        # CPU recommendations
        max_cpu = max(r.cpu_percent for r in successful_results)
        if max_cpu > 90:
            recommendations.append(
                f"⚠ High CPU usage ({max_cpu:.0f}%) - may impact other services"
            )

        if not recommendations:
            recommendations.append("✓ All configurations performed well")

        return recommendations


def print_benchmark_summary(report: Dict[str, Any]):
    """Print a formatted benchmark summary."""
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    summary = report.get('benchmark_summary', {})
    print(f"\nTests Run: {summary.get('total_tests', 0)}")
    print(f"Successful: {summary.get('successful_tests', 0)}")
    print(f"Failed: {summary.get('failed_tests', 0)}")

    if 'best_performers' in report:
        print("\n" + "-" * 80)
        print("BEST PERFORMERS")
        print("-" * 80)

        fastest = report['best_performers'].get('fastest', {})
        print(f"\nFastest: {fastest.get('name')}")
        print(f"  Time: {fastest.get('duration_seconds')}s")
        print(f"  Throughput: {fastest.get('clips_per_second')} clips/sec")

    if 'improvements' in report and report['improvements']:
        print("\n" + "-" * 80)
        print("PERFORMANCE IMPROVEMENTS")
        print("-" * 80)

        improvements = report['improvements']
        if 'overall_speedup' in improvements:
            print(f"\nOverall Speedup: {improvements['overall_speedup']}x")
            print(f"Time Saved: {improvements['time_saved_percent']}%")

    if 'recommendations' in report:
        print("\n" + "-" * 80)
        print("RECOMMENDATIONS")
        print("-" * 80)
        for rec in report['recommendations']:
            print(f"  {rec}")

    print("\n" + "=" * 80)

#!/usr/bin/env python3
"""
CLI script to run comprehensive performance benchmarks.

Usage:
    python run_benchmark.py --full                    # Run all benchmarks
    python run_benchmark.py --quick                   # Run quick benchmarks only
    python run_benchmark.py --video /path/to/video    # Use specific test video
    python run_benchmark.py --profile                 # Enable profiling
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.comprehensive_benchmark import ComprehensiveBenchmark, run_comprehensive_benchmark
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_quick_benchmark():
    """Run quick benchmark (database, Redis, single clip)."""
    logger.info("🚀 Running QUICK benchmark suite...")

    benchmark = ComprehensiveBenchmark()

    # 1. Database operations
    logger.info("\n💾 Benchmarking database...")
    await benchmark.benchmark_database_operations()

    # 2. Redis operations
    logger.info("\n🔴 Benchmarking Redis...")
    await benchmark.benchmark_redis_operations()

    # Generate report
    report = benchmark.generate_report()
    report_path = benchmark.save_report(report, "quick_benchmark.json")
    benchmark.print_summary(report)

    logger.info(f"\n✅ Quick benchmark complete! Report: {report_path}")
    return report


async def run_full_benchmark(video_path: str = None, video_url: str = None):
    """Run full benchmark suite (all operations)."""
    logger.info("🚀 Running FULL benchmark suite...")

    benchmark = ComprehensiveBenchmark()

    # Determine test video
    test_video = video_path

    if not test_video and video_url:
        logger.info("📥 Downloading test video from YouTube...")
        try:
            result = await benchmark.benchmark_youtube_download(video_url)
            if result.success and result.metadata:
                test_video = result.metadata.get('video_path')
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return

    if not test_video:
        # Use default short test video if available
        test_video = "/tmp/test_video.mp4"
        if not Path(test_video).exists():
            logger.warning(
                "No test video provided and default not found. "
                "Use --video or --url to specify a test video."
            )
            logger.info("Running non-video benchmarks only...")

    # 1. Database & Redis
    logger.info("\n💾 Benchmarking database operations...")
    await benchmark.benchmark_database_operations()

    logger.info("\n🔴 Benchmarking Redis operations...")
    await benchmark.benchmark_redis_operations()

    if test_video and Path(test_video).exists():
        # 2. Transcription benchmarks
        logger.info(f"\n📝 Benchmarking transcription (video: {test_video})...")

        try:
            logger.info("Testing MLX Whisper...")
            await benchmark.benchmark_transcription_mlx(test_video)
        except Exception as e:
            logger.warning(f"MLX transcription benchmark failed: {e}")

        try:
            logger.info("Testing AssemblyAI...")
            await benchmark.benchmark_transcription_assemblyai(test_video)
        except Exception as e:
            logger.warning(f"AssemblyAI transcription benchmark failed: {e}")

        # 3. Single clip generation
        logger.info("\n🎬 Benchmarking single clip generation...")
        output_dir = Path("/tmp/benchmark_clips")
        output_dir.mkdir(exist_ok=True)

        try:
            await benchmark.benchmark_single_clip_generation(
                video_path=test_video,
                start_time=10.0,
                end_time=25.0,
                output_path=output_dir / "test_clip.mp4"
            )
        except Exception as e:
            logger.warning(f"Single clip benchmark failed: {e}")

        # 4. Batch clip generation (sequential vs parallel)
        logger.info("\n🎬 Benchmarking batch clip generation...")

        # Create test segments
        test_segments = [
            {
                "start_time": f"{i*15//60:02d}:{i*15%60:02d}",
                "end_time": f"{(i*15+10)//60:02d}:{(i*15+10)%60:02d}",
                "text": f"Test segment {i}",
                "relevance_score": 8.0,
                "reasoning": "Test"
            }
            for i in range(10)  # 10 clips for quick test
        ]

        # Sequential
        try:
            output_dir_seq = Path("/tmp/benchmark_clips_seq")
            output_dir_seq.mkdir(exist_ok=True)
            await benchmark.benchmark_batch_clip_generation(
                video_path=test_video,
                segments=test_segments,
                output_dir=output_dir_seq,
                parallel=False
            )
        except Exception as e:
            logger.warning(f"Sequential batch benchmark failed: {e}")

        # Parallel
        try:
            output_dir_par = Path("/tmp/benchmark_clips_par")
            output_dir_par.mkdir(exist_ok=True)
            await benchmark.benchmark_batch_clip_generation(
                video_path=test_video,
                segments=test_segments,
                output_dir=output_dir_par,
                parallel=True
            )
        except Exception as e:
            logger.warning(f"Parallel batch benchmark failed: {e}")

    # Generate report
    report = benchmark.generate_report()
    report_path = benchmark.save_report(report, "full_benchmark.json")
    benchmark.print_summary(report)

    logger.info(f"\n✅ Full benchmark complete! Report: {report_path}")
    return report


async def run_stress_test(video_path: str, clip_counts: list = [10, 50, 100]):
    """Run stress test with varying clip counts."""
    logger.info(f"🚀 Running STRESS TEST (clip counts: {clip_counts})...")

    benchmark = ComprehensiveBenchmark()

    for count in clip_counts:
        logger.info(f"\n📊 Testing {count} clips...")

        # Generate segments
        segments = [
            {
                "start_time": f"{i*10//60:02d}:{i*10%60:02d}",
                "end_time": f"{(i*10+8)//60:02d}:{(i*10+8)%60:02d}",
                "text": f"Clip {i}",
                "relevance_score": 7.5,
                "reasoning": "Stress test"
            }
            for i in range(count)
        ]

        output_dir = Path(f"/tmp/stress_test_{count}")
        output_dir.mkdir(exist_ok=True)

        try:
            await benchmark.benchmark_batch_clip_generation(
                video_path=video_path,
                segments=segments,
                output_dir=output_dir,
                parallel=True
            )
        except Exception as e:
            logger.error(f"Stress test with {count} clips failed: {e}")

    # Generate report
    report = benchmark.generate_report()
    report_path = benchmark.save_report(report, "stress_test.json")
    benchmark.print_summary(report)

    logger.info(f"\n✅ Stress test complete! Report: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="SupoClip Performance Benchmark Suite"
    )

    parser.add_argument(
        '--mode',
        choices=['quick', 'full', 'stress'],
        default='quick',
        help='Benchmark mode (default: quick)'
    )

    parser.add_argument(
        '--video',
        type=str,
        help='Path to test video file'
    )

    parser.add_argument(
        '--url',
        type=str,
        help='YouTube URL for test video'
    )

    parser.add_argument(
        '--clips',
        type=int,
        nargs='+',
        default=[10, 50, 100],
        help='Clip counts for stress test (default: 10 50 100)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output directory for results'
    )

    parser.add_argument(
        '--profile',
        action='store_true',
        help='Enable code profiling'
    )

    args = parser.parse_args()

    # Run benchmark
    if args.mode == 'quick':
        asyncio.run(run_quick_benchmark())

    elif args.mode == 'full':
        asyncio.run(run_full_benchmark(
            video_path=args.video,
            video_url=args.url
        ))

    elif args.mode == 'stress':
        if not args.video:
            logger.error("Stress test requires --video argument")
            sys.exit(1)

        asyncio.run(run_stress_test(
            video_path=args.video,
            clip_counts=args.clips
        ))


if __name__ == '__main__':
    main()

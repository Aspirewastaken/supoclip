"""
Capacity test for 500-clip generation pipeline.
Simulates video processing without actual video encoding.

Usage:
    python -m tests.test_500_clip_capacity

This test simulates the matrix processing pipeline to estimate:
- Processing time for different clip counts (50, 250, 500)
- Memory usage patterns
- Disk space requirements
- System resource utilization
"""
import asyncio
import time
import psutil
import logging
import os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CapacityTestResult:
    """Results from capacity test."""
    test_name: str
    num_clips: int
    variations_per_clip: int
    total_variations: int
    batch_size: int
    max_workers: int

    # Timings
    duration_seconds: float
    duration_minutes: float
    avg_time_per_variation: float
    variations_per_second: float

    # Resources
    memory_start_mb: float
    memory_end_mb: float
    memory_used_mb: float
    cpu_count: int

    # Estimates
    estimated_real_time_sequential_hours: float
    estimated_real_time_parallel_hours: float
    estimated_disk_space_gb: float

    # System check
    current_free_disk_gb: float
    disk_space_sufficient: bool


async def simulate_clip_processing(
    clip_idx: int,
    variation_idx: int,
    processing_time_seconds: float = 0.1  # Simulated time
) -> Dict[str, Any]:
    """Simulate processing a single variation."""
    await asyncio.sleep(processing_time_seconds)

    return {
        'clip_index': clip_idx,
        'variation_index': variation_idx,
        'success': True,
        'processing_time': processing_time_seconds
    }


async def run_capacity_test(
    num_clips: int,
    variations_per_clip: int = 9,
    batch_size: int = 10,
    max_workers: int = 8,
    simulation_time_per_variation: float = 0.1
) -> CapacityTestResult:
    """
    Run capacity test for given number of clips.

    Args:
        num_clips: Number of base clips
        variations_per_clip: Number of variations per clip (default 9)
        batch_size: Batch size for processing
        max_workers: Max parallel workers
        simulation_time_per_variation: Simulated processing time
    """
    total_variations = num_clips * variations_per_clip

    logger.info("=" * 70)
    logger.info(f"CAPACITY TEST: {num_clips} clips")
    logger.info("=" * 70)
    logger.info(f"Total variations: {total_variations} ({num_clips} × {variations_per_clip})")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max workers: {max_workers}")
    logger.info("=" * 70)

    # System metrics before
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    cpu_count = os.cpu_count() or 1

    # Simulate parallel processing
    all_results = []

    for batch_start in range(0, num_clips, batch_size):
        batch_end = min(batch_start + batch_size, num_clips)
        batch_clips = list(range(batch_start, batch_end))
        batch_num = (batch_start // batch_size) + 1
        total_batches = (num_clips + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} (clips {batch_start+1}-{batch_end})")

        # Simulate parallel variation processing
        tasks = []
        for clip_idx in batch_clips:
            for var_idx in range(variations_per_clip):
                task = simulate_clip_processing(
                    clip_idx,
                    var_idx,
                    simulation_time_per_variation
                )
                tasks.append(task)

        # Process with concurrency limit
        for i in range(0, len(tasks), max_workers):
            batch_tasks = tasks[i:i+max_workers]
            results = await asyncio.gather(*batch_tasks)
            all_results.extend(results)

        # Simulate memory cleanup between batches
        if batch_end % 100 == 0:
            logger.info(f"  [Simulated memory cleanup at clip {batch_end}]")

    # System metrics after
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024

    duration_seconds = end_time - start_time
    duration_minutes = duration_seconds / 60
    memory_used = end_memory - start_memory

    # Calculate estimates for real processing
    real_processing_time_per_var = 70  # seconds (realistic estimate)
    estimated_sequential_hours = (total_variations * real_processing_time_per_var) / 3600
    estimated_parallel_hours = (total_variations * real_processing_time_per_var / max_workers) / 3600

    # Disk space estimate
    avg_clip_size_mb = 20  # MB per clip
    safety_margin = 1.3  # 30% safety buffer
    estimated_disk_gb = (total_variations * avg_clip_size_mb * safety_margin) / 1024

    # Check current disk space
    import shutil
    disk_usage = shutil.disk_usage('/home/user/supoclip/backend')
    free_disk_gb = disk_usage.free / (1024 ** 3)
    disk_sufficient = free_disk_gb >= estimated_disk_gb

    result = CapacityTestResult(
        test_name=f"{num_clips}_clips",
        num_clips=num_clips,
        variations_per_clip=variations_per_clip,
        total_variations=len(all_results),
        batch_size=batch_size,
        max_workers=max_workers,
        duration_seconds=duration_seconds,
        duration_minutes=duration_minutes,
        avg_time_per_variation=duration_seconds / len(all_results) if all_results else 0,
        variations_per_second=len(all_results) / duration_seconds if duration_seconds > 0 else 0,
        memory_start_mb=start_memory,
        memory_end_mb=end_memory,
        memory_used_mb=memory_used,
        cpu_count=cpu_count,
        estimated_real_time_sequential_hours=estimated_sequential_hours,
        estimated_real_time_parallel_hours=estimated_parallel_hours,
        estimated_disk_space_gb=estimated_disk_gb,
        current_free_disk_gb=free_disk_gb,
        disk_space_sufficient=disk_sufficient
    )

    return result


def print_results(result: CapacityTestResult):
    """Print formatted test results."""
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"TEST RESULTS: {result.test_name}")
    logger.info("=" * 70)

    logger.info("")
    logger.info("SIMULATION METRICS:")
    logger.info(f"  Total variations processed: {result.total_variations:,}")
    logger.info(f"  Simulation time: {result.duration_minutes:.2f} minutes")
    logger.info(f"  Memory used: {result.memory_used_mb:.1f} MB")
    logger.info(f"  Avg time per variation: {result.avg_time_per_variation:.3f}s")
    logger.info(f"  Variations per second: {result.variations_per_second:.2f}")

    logger.info("")
    logger.info("REAL PROCESSING ESTIMATES:")
    logger.info(f"  Sequential processing: {result.estimated_real_time_sequential_hours:.1f} hours")
    logger.info(f"  Parallel ({result.max_workers} workers): {result.estimated_real_time_parallel_hours:.1f} hours")
    logger.info(f"  Speedup: {result.estimated_real_time_sequential_hours / result.estimated_real_time_parallel_hours:.1f}x")

    logger.info("")
    logger.info("DISK SPACE:")
    logger.info(f"  Estimated space needed: {result.estimated_disk_space_gb:.1f} GB")
    logger.info(f"  Currently available: {result.current_free_disk_gb:.1f} GB")

    if result.disk_space_sufficient:
        logger.info(f"  Status: ✅ SUFFICIENT (surplus: {result.current_free_disk_gb - result.estimated_disk_space_gb:.1f} GB)")
    else:
        logger.info(f"  Status: ❌ INSUFFICIENT (shortage: {result.estimated_disk_space_gb - result.current_free_disk_gb:.1f} GB)")
        logger.info(f"  ⚠️  WARNING: Free up {result.estimated_disk_space_gb - result.current_free_disk_gb:.1f} GB before running!")

    logger.info("")
    logger.info("SYSTEM INFO:")
    logger.info(f"  CPU cores: {result.cpu_count}")
    logger.info(f"  Batch size: {result.batch_size}")
    logger.info(f"  Max workers: {result.max_workers}")

    logger.info("=" * 70)
    logger.info("")


async def run_all_tests():
    """Run capacity tests for 50, 250, and 500 clips."""

    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 15 + "500-CLIP CAPACITY TEST SUITE" + " " * 25 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")

    results = []

    # Test 1: 50 clips (small scale)
    logger.info("TEST 1: Small scale (50 clips)")
    result_50 = await run_capacity_test(
        num_clips=50,
        batch_size=10,
        max_workers=8
    )
    print_results(result_50)
    results.append(result_50)

    # Test 2: 250 clips (medium scale)
    logger.info("TEST 2: Medium scale (250 clips)")
    result_250 = await run_capacity_test(
        num_clips=250,
        batch_size=10,
        max_workers=8
    )
    print_results(result_250)
    results.append(result_250)

    # Test 3: 500 clips (full scale)
    logger.info("TEST 3: Full scale (500 clips)")
    result_500 = await run_capacity_test(
        num_clips=500,
        batch_size=10,
        max_workers=8
    )
    print_results(result_500)
    results.append(result_500)

    # Summary comparison
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY COMPARISON")
    logger.info("=" * 70)
    logger.info("")
    logger.info(f"{'Scale':<15} {'Clips':>8} {'Vars':>8} {'Est. Time':>12} {'Disk':>10} {'Status':>10}")
    logger.info("-" * 70)

    for r in results:
        status = "✅ OK" if r.disk_space_sufficient else "❌ NO SPACE"
        logger.info(
            f"{r.test_name:<15} {r.num_clips:>8} {r.total_variations:>8} "
            f"{r.estimated_real_time_parallel_hours:>11.1f}h {r.estimated_disk_space_gb:>9.1f}GB {status:>10}"
        )

    logger.info("=" * 70)
    logger.info("")

    # Recommendations
    logger.info("RECOMMENDATIONS:")
    logger.info("")

    if not result_500.disk_space_sufficient:
        logger.info("🔴 CRITICAL: Insufficient disk space for 500-clip jobs!")
        logger.info(f"   Action: Free up {result_500.estimated_disk_space_gb - result_500.current_free_disk_gb:.1f} GB")
        logger.info("")

    if result_500.estimated_real_time_parallel_hours > 10:
        logger.info("🟠 RECOMMENDATION: Enable GPU acceleration for faster processing")
        logger.info(f"   Current estimate: {result_500.estimated_real_time_parallel_hours:.1f} hours")
        logger.info(f"   With GPU: ~4-5 hours")
        logger.info("")

    logger.info("✅ NEXT STEPS:")
    logger.info("   1. Review AGENT3_500_CLIP_OPTIMIZATION_REPORT.md")
    logger.info("   2. Implement disk space validation")
    logger.info("   3. Implement parallel batch processing")
    logger.info("   4. Test with real 50-clip job")
    logger.info("")

    # Save results to JSON
    import json
    output_file = "/home/user/supoclip/capacity_test_results.json"
    with open(output_file, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    logger.info(f"Results saved to: {output_file}")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

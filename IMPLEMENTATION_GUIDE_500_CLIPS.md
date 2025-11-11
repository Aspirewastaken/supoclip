# Quick Implementation Guide: 500-Clip Optimization

**Time to implement**: 2-3 days
**Priority**: CRITICAL before running 500-clip jobs

---

## Critical Issues Summary

| Issue | Impact | Status | Priority |
|-------|--------|--------|----------|
| Disk space (13GB vs 90GB) | Job will fail | 🔴 | CRITICAL |
| Sequential processing (40+ hours) | Unusable | 🔴 | CRITICAL |
| Job timeout (2h vs 40h needed) | Job will timeout | 🔴 | CRITICAL |
| Premiere XML (single bin, 4,500 clips) | Unusable in Premiere | 🟠 | HIGH |

---

## Implementation Checklist

### Step 1: Add Disk Space Validation (30 minutes)

**File**: `/backend/src/workers/matrix_processing.py`

Add this function at the top of the file (after imports):

```python
import psutil
import shutil

async def validate_disk_space(
    base_clips: List[Dict[str, Any]],
    output_base: str,
    avg_clip_size_mb: float = 20.0,
    safety_margin: float = 1.3
) -> Tuple[bool, str]:
    """Validate sufficient disk space before starting."""
    total_variations = len(base_clips) * 9
    estimated_size_gb = (total_variations * avg_clip_size_mb * safety_margin) / 1024

    disk_usage = shutil.disk_usage(output_base)
    free_gb = disk_usage.free / (1024 ** 3)

    logger.info(f"Disk space: {estimated_size_gb:.1f}GB needed, {free_gb:.1f}GB available")

    if free_gb < estimated_size_gb:
        return False, f"Insufficient disk space: {estimated_size_gb:.1f}GB needed, {free_gb:.1f}GB available"

    if free_gb < 10:
        return False, f"Critically low disk space: {free_gb:.1f}GB"

    return True, f"Sufficient space: {free_gb:.1f}GB available"
```

Add to `process_clip_matrix()` after line 110 (after creating output_base):

```python
    # PRE-FLIGHT VALIDATION
    await progress.update(1, "Validating disk space...", "processing")

    disk_valid, disk_msg = await validate_disk_space(base_clips, output_base)
    if not disk_valid:
        logger.error(f"❌ {disk_msg}")
        raise RuntimeError(f"Disk space validation failed: {disk_msg}")

    logger.info(f"✅ {disk_msg}")
```

**Test**: Run with 50-clip job, verify it checks disk space

---

### Step 2: Increase Job Timeout (2 minutes)

**File**: `/backend/src/workers/tasks.py`

Change line 108:

```python
# BEFORE:
job_timeout = 7200  # 2 hour timeout

# AFTER:
job_timeout = 172800  # 48 hour timeout for large jobs
```

**Test**: Verify worker starts without errors

---

### Step 3: Fix Premiere XML Bins (1 hour)

**File**: `/backend/src/export/premiere_xml.py`

Replace the entire `generate_premiere_xml()` function with the optimized version from the full report (Section 3.4).

Key changes:
- Add `clips_per_bin=50` parameter
- Organize clips into multiple bins
- Limit sequence to first 100 clips
- Add metadata to clip names

**Test**: Generate XML with 100+ clips, import into Premiere Pro

---

### Step 4: Implement Parallel Processing (4-6 hours)

**File**: `/backend/src/workers/matrix_processing.py`

This is the most complex change. See full implementation in AGENT3_500_CLIP_OPTIMIZATION_REPORT.md Section 3.2.

**Key changes:**
1. Add `process_batch_parallel()` function
2. Add `process_single_variation()` function
3. Replace the main loop in `process_clip_matrix()` with batched processing
4. Add `ThreadPoolExecutor` for parallelization

**Test**: Run with 50-clip job, verify speedup

---

## Testing Protocol

### Test 1: 50-clip job (Baseline)
```bash
# Expected: 30-45 minutes with optimization (vs 5-6 hours without)
# Expected size: ~9GB
```

### Test 2: 250-clip job (Medium scale)
```bash
# Expected: 3-4 hours with optimization
# Expected size: ~45GB
# Prerequisites: 60GB+ free disk space
```

### Test 3: 500-clip job (Full capacity)
```bash
# Expected: 6-8 hours with optimization
# Expected size: ~90GB
# Prerequisites: 120GB+ free disk space, GPU recommended
```

---

## Quick Commands

### Check disk space:
```bash
df -h /home/user/supoclip/backend
```

### Check CPU cores:
```bash
nproc
```

### Check memory:
```bash
free -h
```

### Monitor job in real-time:
```bash
# Watch logs
docker-compose logs -f backend

# Watch disk usage
watch -n 5 'df -h | grep /home'

# Watch memory
watch -n 5 'free -h'
```

---

## Performance Expectations

### Without Optimization (Current)
- 50 clips: 5-6 hours
- 250 clips: 25-30 hours
- 500 clips: 50+ hours (will timeout!)

### With Optimization
- 50 clips: 30-45 minutes (10x faster)
- 250 clips: 3-4 hours (8x faster)
- 500 clips: 6-8 hours (8x faster)

### With GPU Acceleration
- 50 clips: 20-30 minutes
- 250 clips: 2-3 hours
- 500 clips: 4-5 hours

---

## Troubleshooting

### Job times out after 2 hours
- ✅ Step 2: Increase job_timeout to 172800

### "Disk space full" error
- ✅ Step 1: Add disk space validation
- Free up disk space or mount larger volume

### Premiere XML import shows 4,500 clips in one bin
- ✅ Step 3: Update Premiere XML export

### Processing is still slow
- ✅ Step 4: Implement parallel processing
- Check: `htop` - should see 80%+ CPU usage across cores

### Out of memory errors
- Reduce `batch_size` from 10 to 5
- Reduce `max_workers` from 8 to 4
- Add more RAM to system

---

## Configuration Options

Add to `/backend/.env`:

```bash
# Matrix processing optimization
MAX_PARALLEL_WORKERS=8          # CPU cores - 2 (leave some free)
BATCH_SIZE=10                   # Process 10 clips at a time
DISK_SPACE_SAFETY_MARGIN=1.3   # 30% safety buffer
```

---

## Estimated Timeline

| Task | Time | Priority |
|------|------|----------|
| Step 1: Disk validation | 30 min | CRITICAL |
| Step 2: Job timeout | 2 min | CRITICAL |
| Step 3: Premiere XML | 1 hour | HIGH |
| Step 4: Parallel processing | 4-6 hours | CRITICAL |
| Testing | 2-3 hours | CRITICAL |
| **Total** | **8-11 hours** | |

---

## Next Steps After Implementation

1. Run Test 1 (50 clips) to validate
2. Profile memory usage with `memory_profiler`
3. Run Test 2 (250 clips) to verify scaling
4. Provision 120GB+ disk for production
5. Document operational procedures
6. Set up monitoring/alerts
7. Run Test 3 (500 clips) in production

---

## Support

See full technical details in: `AGENT3_500_CLIP_OPTIMIZATION_REPORT.md`

Questions or issues? Check:
- Performance utils: `/backend/src/utils/performance.py`
- Worker settings: `/backend/src/workers/tasks.py`
- Matrix processing: `/backend/src/workers/matrix_processing.py`

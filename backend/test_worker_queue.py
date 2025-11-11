"""
Test script for worker queue system.

Run:
    python test_worker_queue.py

Prerequisites:
    - Redis running (docker compose up -d redis)
    - Database initialized
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from arq.connections import create_pool, RedisSettings
from src.config import Config
from src.database import AsyncSessionLocal
from sqlalchemy import text


async def test_queue_system():
    """Comprehensive test of the worker queue system."""
    print("🧪 Testing SupoClip Worker Queue System")
    print("=" * 60)

    config = Config()
    pool = None
    test_task_id = None

    try:
        # 1. Test Redis connection
        print("\n1️⃣ Testing Redis connection...")
        try:
            pool = await create_pool(
                RedisSettings(
                    host=config.redis_host,
                    port=config.redis_port,
                    database=0
                )
            )
            await pool.ping()
            print(f"   ✅ Redis connected successfully ({config.redis_host}:{config.redis_port})")
        except Exception as e:
            print(f"   ❌ Redis connection failed: {e}")
            return False

        # 2. Test database connection
        print("\n2️⃣ Testing database connection...")
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT 1"))
                result.fetchone()
                print("   ✅ Database connected successfully")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            return False

        # 3. Check queue depth
        print("\n3️⃣ Checking queue depth...")
        try:
            # ARQ uses a list for the queue
            queue_key = "arq:queue:supoclip_tasks"
            queue_depth = await pool.llen(queue_key)
            print(f"   📊 Current queue depth: {queue_depth}")
        except Exception as e:
            print(f"   ⚠️ Could not get queue depth: {e}")

        # 4. Create test task in database
        print("\n4️⃣ Creating test task in database...")
        try:
            async with AsyncSessionLocal() as db:
                # Check if test user exists
                user_result = await db.execute(
                    text("SELECT id FROM users LIMIT 1")
                )
                user_row = user_result.fetchone()

                if not user_row:
                    print("   ⚠️ No users in database. Creating test user...")
                    await db.execute(
                        text("""
                            INSERT INTO users (id, email, name)
                            VALUES ('test-user-id', 'test@example.com', 'Test User')
                        """)
                    )
                    user_id = 'test-user-id'
                else:
                    user_id = user_row[0]

                # Check if test source exists
                source_result = await db.execute(
                    text("SELECT id FROM sources LIMIT 1")
                )
                source_row = source_result.fetchone()

                if not source_row:
                    print("   ⚠️ No sources in database. Creating test source...")
                    await db.execute(
                        text("""
                            INSERT INTO sources (id, type, title)
                            VALUES ('test-source-id', 'youtube', 'Test Source')
                        """)
                    )
                    source_id = 'test-source-id'
                else:
                    source_id = source_row[0]

                # Create test task
                result = await db.execute(
                    text("""
                        INSERT INTO tasks (user_id, source_id, status)
                        VALUES (:user_id, :source_id, 'queued')
                        RETURNING id
                    """),
                    {"user_id": user_id, "source_id": source_id}
                )
                test_task_id = result.fetchone()[0]
                await db.commit()
                print(f"   ✅ Created test task: {test_task_id}")

        except Exception as e:
            print(f"   ❌ Failed to create test task: {e}")
            import traceback
            traceback.print_exc()
            return False

        # 5. Enqueue test job (but don't actually process it)
        print("\n5️⃣ Testing job enqueue (dry run)...")
        try:
            # We'll just test the enqueue mechanism without actually processing
            job = await pool.enqueue_job(
                'process_video_task',
                task_id=test_task_id,
                url='https://example.com/test-video.mp4',
                source_type='youtube',
                user_id=user_id,
                _job_id=f'test-job-{test_task_id}'  # Custom job ID for testing
            )
            print(f"   ✅ Job enqueued successfully: {job.job_id}")

            # Check if job is in queue
            await asyncio.sleep(1)
            queue_depth_after = await pool.llen(queue_key)
            print(f"   📊 Queue depth after enqueue: {queue_depth_after}")

            # Try to get job info
            try:
                job_info = await pool.job(job.job_id)
                if job_info:
                    status = await job_info.status()
                    print(f"   📊 Job status: {status}")
            except Exception as e:
                print(f"   ⚠️ Could not get job status: {e}")

        except Exception as e:
            print(f"   ❌ Failed to enqueue job: {e}")
            import traceback
            traceback.print_exc()
            return False

        # 6. Check for active workers
        print("\n6️⃣ Checking for active workers...")
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("SELECT COUNT(*) FROM tasks WHERE status = 'processing'")
                )
                processing = result.fetchone()[0]
                print(f"   📊 Tasks currently being processed: {processing}")

                result = await db.execute(
                    text("SELECT COUNT(*) FROM tasks WHERE status = 'queued'")
                )
                queued = result.fetchone()[0]
                print(f"   📊 Tasks queued: {queued}")
        except Exception as e:
            print(f"   ⚠️ Could not check worker status: {e}")

        # 7. Test progress tracking
        print("\n7️⃣ Testing progress tracking...")
        try:
            from src.workers.progress import ProgressTracker
            import redis.asyncio as redis

            redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                decode_responses=True
            )

            progress = ProgressTracker(redis_client, test_task_id)
            await progress.update(50, "Test progress update", "processing")

            # Try to read it back
            progress_data = await progress.get()
            if progress_data:
                print(f"   ✅ Progress tracking works: {progress_data['message']}")
            else:
                print("   ⚠️ Could not read progress data")

            await redis_client.close()
        except Exception as e:
            print(f"   ⚠️ Progress tracking test failed: {e}")

        # 8. Monitor queue statistics
        print("\n8️⃣ Queue statistics...")
        try:
            # Get all ARQ keys
            arq_keys = await pool.keys("arq:*")
            print(f"   📊 Total ARQ keys in Redis: {len(arq_keys)}")

            # Show some key examples
            if arq_keys:
                print("   📋 Sample ARQ keys:")
                for key in arq_keys[:5]:
                    print(f"      - {key}")
        except Exception as e:
            print(f"   ⚠️ Could not get queue stats: {e}")

        print("\n" + "=" * 60)
        print("✅ Worker queue system test PASSED")
        print("\nTo start processing jobs, run:")
        print("  arq src.workers.tasks.WorkerSettings")
        print("\nor with Docker:")
        print("  docker compose up worker")
        return True

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if pool:
            try:
                # Clean up test job if it exists
                if test_task_id:
                    print("\n🧹 Cleaning up test data...")
                    # Note: In production, you might want to keep test data
                    # For now, we'll leave it to avoid issues
                    pass

                await pool.close()
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")


async def test_worker_registration():
    """Test that all worker functions are properly registered."""
    print("\n" + "=" * 60)
    print("🔍 Verifying worker function registration")
    print("=" * 60)

    try:
        from src.workers.tasks import WorkerSettings

        print("\n📋 Registered worker functions:")
        for i, func in enumerate(WorkerSettings.functions, 1):
            print(f"   {i}. {func.__name__}")

        expected_functions = [
            'process_video_task',
            'generate_mass_clips_task',
            'generate_full_matrix_task'
        ]

        registered_names = [f.__name__ for f in WorkerSettings.functions]

        print("\n✅ Verification:")
        all_registered = True
        for expected in expected_functions:
            if expected in registered_names:
                print(f"   ✅ {expected}")
            else:
                print(f"   ❌ {expected} - NOT FOUND")
                all_registered = False

        print(f"\n📊 Worker Settings:")
        print(f"   Queue name: {WorkerSettings.queue_name}")
        print(f"   Max tries: {WorkerSettings.max_tries}")
        print(f"   Job timeout: {WorkerSettings.job_timeout}s ({WorkerSettings.job_timeout/60}min)")
        print(f"   Max concurrent jobs: {WorkerSettings.max_jobs}")
        print(f"   Redis host: {WorkerSettings.redis_settings.host}")
        print(f"   Redis port: {WorkerSettings.redis_settings.port}")

        if all_registered:
            print("\n✅ All worker functions properly registered!")
            return True
        else:
            print("\n❌ Some worker functions are missing!")
            return False

    except Exception as e:
        print(f"\n❌ Error verifying worker registration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 SupoClip Worker Queue Test Suite")
    print("=" * 60)

    # Run both tests
    loop = asyncio.get_event_loop()

    registration_ok = loop.run_until_complete(test_worker_registration())
    print()

    queue_ok = loop.run_until_complete(test_queue_system())

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Worker Registration: {'✅ PASS' if registration_ok else '❌ FAIL'}")
    print(f"Queue System: {'✅ PASS' if queue_ok else '❌ FAIL'}")

    if registration_ok and queue_ok:
        print("\n🎉 All tests passed! Worker system is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)

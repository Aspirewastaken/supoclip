"""
Social Media Post Scheduler

This module handles scheduled posting and retry logic for social media integrations.
Uses Redis for job queuing and scheduling.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import asyncpg
import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .social_media import SocialMediaManager, PostStatus, AttemptStatus

logger = logging.getLogger(__name__)


class SocialMediaScheduler:
    """Scheduler for social media posts with retry logic"""

    def __init__(
        self,
        social_media_manager: SocialMediaManager,
        redis_url: str = "redis://localhost:6379"
    ):
        self.manager = social_media_manager
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False

    async def start(self):
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting social media scheduler...")

        # Connect to Redis
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)

        # Initialize APScheduler
        self.scheduler = AsyncIOScheduler()

        # Add jobs
        self._add_jobs()

        # Start scheduler
        self.scheduler.start()
        self._running = True

        logger.info("✅ Social media scheduler started successfully")

    async def stop(self):
        """Stop the scheduler"""
        if not self._running:
            return

        logger.info("Stopping social media scheduler...")

        if self.scheduler:
            self.scheduler.shutdown(wait=True)

        if self.redis:
            await self.redis.close()

        self._running = False
        logger.info("✅ Social media scheduler stopped")

    def _add_jobs(self):
        """Add scheduled jobs"""
        # Check for posts to publish every minute
        self.scheduler.add_job(
            self.process_due_posts,
            trigger=IntervalTrigger(minutes=1),
            id="process_due_posts",
            name="Process due social media posts",
            replace_existing=True
        )

        # Retry failed posts every 5 minutes
        self.scheduler.add_job(
            self.retry_failed_posts,
            trigger=IntervalTrigger(minutes=5),
            id="retry_failed_posts",
            name="Retry failed social media posts",
            replace_existing=True
        )

        # Clean up old completed posts daily
        self.scheduler.add_job(
            self.cleanup_old_posts,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
            id="cleanup_old_posts",
            name="Clean up old social media posts",
            replace_existing=True
        )

    async def process_due_posts(self):
        """Process posts that are due to be published"""
        try:
            logger.info("🔍 Checking for due social media posts...")

            # Get posts that are scheduled for now or earlier
            async with self.manager.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id
                    FROM scheduled_posts
                    WHERE status = $1
                      AND scheduled_for <= CURRENT_TIMESTAMP
                    ORDER BY scheduled_for
                    LIMIT 50
                    """,
                    PostStatus.SCHEDULED.value
                )

                if not rows:
                    logger.debug("No due posts found")
                    return

                logger.info(f"📤 Found {len(rows)} posts to process")

                for row in rows:
                    post_id = row["id"]

                    # Add to Redis queue for processing
                    await self.queue_post(post_id)

                # Process queued posts
                await self.process_queue()

        except Exception as e:
            logger.error(f"❌ Error processing due posts: {str(e)}")

    async def queue_post(self, post_id: str):
        """Add post to processing queue"""
        try:
            # Add to Redis list
            await self.redis.lpush("social_media_queue", post_id)
            logger.info(f"➕ Queued post {post_id} for processing")
        except Exception as e:
            logger.error(f"❌ Error queuing post {post_id}: {str(e)}")

    async def process_queue(self):
        """Process posts in the queue"""
        while True:
            try:
                # Get next post from queue (blocking with timeout)
                result = await self.redis.brpop("social_media_queue", timeout=1)

                if not result:
                    # No more posts in queue
                    break

                _, post_id = result
                logger.info(f"📤 Processing post {post_id}")

                # Process the post
                await self.process_post(post_id)

            except Exception as e:
                logger.error(f"❌ Error processing queue: {str(e)}")
                break

    async def process_post(self, post_id: str):
        """Process a single post"""
        try:
            # Check if post is already being processed (using Redis lock)
            lock_key = f"post_lock:{post_id}"
            lock = await self.redis.set(lock_key, "1", nx=True, ex=300)  # 5 minute lock

            if not lock:
                logger.warning(f"⚠️ Post {post_id} is already being processed")
                return

            try:
                # Process the post
                results = await self.manager.process_scheduled_post(post_id)

                # Log results
                success_count = sum(1 for r in results.values() if r.success)
                total_count = len(results)

                if success_count == total_count:
                    logger.info(f"✅ Successfully posted {post_id} to all {total_count} platforms")
                elif success_count > 0:
                    logger.warning(f"⚠️ Partially posted {post_id} to {success_count}/{total_count} platforms")
                else:
                    logger.error(f"❌ Failed to post {post_id} to any platform")

                    # Schedule retry if needed
                    await self.schedule_retry(post_id)

            finally:
                # Release lock
                await self.redis.delete(lock_key)

        except Exception as e:
            logger.error(f"❌ Error processing post {post_id}: {str(e)}")

            # Schedule retry
            await self.schedule_retry(post_id)

    async def schedule_retry(self, post_id: str):
        """Schedule a retry for a failed post"""
        try:
            async with self.manager.db_pool.acquire() as conn:
                # Get post details
                row = await conn.fetchrow(
                    """
                    SELECT id, max_retries, retry_delay_seconds
                    FROM scheduled_posts
                    WHERE id = $1
                    """,
                    post_id
                )

                if not row:
                    return

                # Get failed attempts
                failed_attempts = await conn.fetch(
                    """
                    SELECT id, platform, attempt_number
                    FROM post_attempts
                    WHERE scheduled_post_id = $1 AND status = $2
                    """,
                    post_id,
                    AttemptStatus.FAILED.value
                )

                # Schedule retry for each failed platform
                for attempt in failed_attempts:
                    if attempt["attempt_number"] < row["max_retries"]:
                        # Calculate exponential backoff
                        delay = self._calculate_retry_delay(
                            attempt["attempt_number"],
                            row["retry_delay_seconds"]
                        )

                        next_retry_at = datetime.utcnow() + timedelta(seconds=delay)

                        # Update attempt with retry time
                        await conn.execute(
                            """
                            UPDATE post_attempts
                            SET next_retry_at = $1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                            """,
                            next_retry_at,
                            attempt["id"]
                        )

                        logger.info(
                            f"⏰ Scheduled retry for post {post_id} "
                            f"platform {attempt['platform']} in {delay} seconds"
                        )
                    else:
                        logger.error(
                            f"❌ Post {post_id} platform {attempt['platform']} "
                            f"exceeded max retries ({row['max_retries']})"
                        )

        except Exception as e:
            logger.error(f"❌ Error scheduling retry for post {post_id}: {str(e)}")

    def _calculate_retry_delay(self, attempt_number: int, base_delay: int) -> int:
        """
        Calculate retry delay with exponential backoff

        Formula: base_delay * (2 ^ (attempt_number - 1))
        Example: 300s * 2^0 = 300s (5 min)
                 300s * 2^1 = 600s (10 min)
                 300s * 2^2 = 1200s (20 min)
        """
        return min(base_delay * (2 ** (attempt_number - 1)), 3600)  # Max 1 hour

    async def retry_failed_posts(self):
        """Retry failed posts that are eligible for retry"""
        try:
            logger.info("🔄 Checking for posts to retry...")

            async with self.manager.db_pool.acquire() as conn:
                # Get attempts that need retry
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT pa.scheduled_post_id
                    FROM post_attempts pa
                    JOIN scheduled_posts sp ON pa.scheduled_post_id = sp.id
                    WHERE pa.status = $1
                      AND pa.next_retry_at IS NOT NULL
                      AND pa.next_retry_at <= CURRENT_TIMESTAMP
                      AND pa.attempt_number < sp.max_retries
                    ORDER BY pa.next_retry_at
                    LIMIT 20
                    """,
                    AttemptStatus.FAILED.value
                )

                if not rows:
                    logger.debug("No posts to retry")
                    return

                logger.info(f"🔄 Found {len(rows)} posts to retry")

                for row in rows:
                    post_id = row["scheduled_post_id"]

                    # Reset post status to scheduled so it can be processed again
                    await conn.execute(
                        """
                        UPDATE scheduled_posts
                        SET status = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                        """,
                        PostStatus.SCHEDULED.value,
                        post_id
                    )

                    # Queue for processing
                    await self.queue_post(post_id)

                # Process queued posts
                await self.process_queue()

        except Exception as e:
            logger.error(f"❌ Error retrying failed posts: {str(e)}")

    async def cleanup_old_posts(self):
        """Clean up old completed/cancelled posts"""
        try:
            logger.info("🧹 Cleaning up old social media posts...")

            # Delete posts older than 30 days that are completed or cancelled
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            async with self.manager.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM scheduled_posts
                    WHERE status IN ($1, $2)
                      AND processed_at < $3
                    """,
                    PostStatus.COMPLETED.value,
                    PostStatus.CANCELLED.value,
                    cutoff_date
                )

                # Extract count from result
                deleted_count = int(result.split()[-1]) if result else 0

                if deleted_count > 0:
                    logger.info(f"🗑️ Deleted {deleted_count} old posts")
                else:
                    logger.debug("No old posts to clean up")

        except Exception as e:
            logger.error(f"❌ Error cleaning up old posts: {str(e)}")

    async def get_queue_status(self) -> dict:
        """Get current queue status"""
        try:
            queue_length = await self.redis.llen("social_media_queue")

            async with self.manager.db_pool.acquire() as conn:
                # Count scheduled posts
                scheduled_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM scheduled_posts WHERE status = $1",
                    PostStatus.SCHEDULED.value
                )

                # Count processing posts
                processing_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM scheduled_posts WHERE status = $1",
                    PostStatus.PROCESSING.value
                )

                # Count failed attempts waiting for retry
                retry_count = await conn.fetchval(
                    """
                    SELECT COUNT(DISTINCT scheduled_post_id)
                    FROM post_attempts
                    WHERE status = $1 AND next_retry_at IS NOT NULL
                    """,
                    AttemptStatus.FAILED.value
                )

            return {
                "queue_length": queue_length,
                "scheduled_posts": scheduled_count,
                "processing_posts": processing_count,
                "posts_awaiting_retry": retry_count,
                "scheduler_running": self._running
            }

        except Exception as e:
            logger.error(f"❌ Error getting queue status: {str(e)}")
            return {
                "error": str(e),
                "scheduler_running": self._running
            }


# ============================================================================
# Standalone Background Worker
# ============================================================================

async def run_scheduler(db_pool: asyncpg.Pool, redis_url: str = "redis://localhost:6379"):
    """
    Run the scheduler as a standalone background worker

    This can be run in a separate process/container for production deployments.
    """
    from .social_media import init_integrations

    logger.info("🚀 Starting social media scheduler worker...")

    # Initialize integrations
    manager = await init_integrations(db_pool)

    # Create scheduler
    scheduler = SocialMediaScheduler(manager, redis_url)

    try:
        # Start scheduler
        await scheduler.start()

        logger.info("✅ Scheduler worker started. Press Ctrl+C to stop.")

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("⚠️ Received shutdown signal")
    finally:
        await scheduler.stop()
        logger.info("✅ Scheduler worker stopped")


if __name__ == "__main__":
    import asyncio
    import os
    from ..database import get_db_pool

    async def main():
        # Get database connection
        db_pool = await get_db_pool()

        # Run scheduler
        await run_scheduler(
            db_pool=db_pool,
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )

    asyncio.run(main())

"""
Backup Scheduler Module

Handles automated backup scheduling:
- Daily backups
- Weekly full backups
- Incremental backups
- Cleanup of old backups
- Verification tasks
"""

import asyncio
from datetime import datetime, time
from typing import Optional
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import BackupConfig
from .database_backup import DatabaseBackup
from .file_backup import FileBackup
from .verify import BackupVerifier

logger = logging.getLogger(__name__)


class BackupScheduler:
    """Manages automated backup scheduling"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.db_backup = DatabaseBackup(config)
        self.file_backup = FileBackup(config)
        self.verifier = BackupVerifier(config)

        self._setup_jobs()

    def _setup_jobs(self):
        """Setup scheduled backup jobs"""

        # Parse daily backup time (format: "HH:MM")
        try:
            hour, minute = map(int, self.config.daily_backup_time.split(":"))
        except:
            logger.warning(f"Invalid daily backup time: {self.config.daily_backup_time}. Using 02:00")
            hour, minute = 2, 0

        # Daily incremental database backup
        if self.config.enable_incremental:
            self.scheduler.add_job(
                self._daily_incremental_backup,
                CronTrigger(hour=hour, minute=minute),
                id="daily_incremental_backup",
                name="Daily Incremental Database Backup",
                replace_existing=True
            )
            logger.info(f"Scheduled daily incremental backup at {hour:02d}:{minute:02d}")

        # Weekly full database backup
        self.scheduler.add_job(
            self._weekly_full_backup,
            CronTrigger(
                day_of_week=self.config.weekly_backup_day,
                hour=hour,
                minute=minute
            ),
            id="weekly_full_backup",
            name="Weekly Full Database Backup",
            replace_existing=True
        )
        logger.info(f"Scheduled weekly full backup on day {self.config.weekly_backup_day} at {hour:02d}:{minute:02d}")

        # Daily file backup
        self.scheduler.add_job(
            self._daily_file_backup,
            CronTrigger(hour=hour + 1, minute=minute),  # 1 hour after DB backup
            id="daily_file_backup",
            name="Daily File Backup",
            replace_existing=True
        )
        logger.info(f"Scheduled daily file backup at {hour+1:02d}:{minute:02d}")

        # Weekly cleanup
        self.scheduler.add_job(
            self._weekly_cleanup,
            CronTrigger(
                day_of_week=(self.config.weekly_backup_day + 1) % 7,
                hour=hour,
                minute=minute
            ),
            id="weekly_cleanup",
            name="Weekly Backup Cleanup",
            replace_existing=True
        )
        logger.info("Scheduled weekly cleanup")

        # Daily verification (if enabled)
        if self.config.verify_after_backup:
            self.scheduler.add_job(
                self._daily_verification,
                CronTrigger(hour=hour + 2, minute=minute),  # 2 hours after DB backup
                id="daily_verification",
                name="Daily Backup Verification",
                replace_existing=True
            )
            logger.info(f"Scheduled daily verification at {hour+2:02d}:{minute:02d}")

        # Weekly completeness check
        self.scheduler.add_job(
            self._weekly_completeness_check,
            CronTrigger(
                day_of_week=0,  # Monday
                hour=9,
                minute=0
            ),
            id="weekly_completeness_check",
            name="Weekly Backup Completeness Check",
            replace_existing=True
        )
        logger.info("Scheduled weekly completeness check")

    async def _daily_incremental_backup(self):
        """Run daily incremental database backup"""
        try:
            logger.info("🔄 Starting scheduled incremental backup")

            # Check if it's time for a full backup instead
            from datetime import timedelta
            backups = await self.db_backup.list_backups("full")

            should_do_full = False
            if not backups:
                should_do_full = True
            else:
                latest = datetime.fromisoformat(backups[0]["timestamp"])
                days_since_full = (datetime.now() - latest).days

                if days_since_full >= self.config.full_backup_interval_days:
                    should_do_full = True

            if should_do_full:
                logger.info("Time for full backup instead of incremental")
                await self._weekly_full_backup()
            else:
                backup_file = await self.db_backup.create_incremental_backup()

                if backup_file:
                    logger.info(f"✅ Scheduled incremental backup completed: {backup_file}")
                    await self._send_notification(
                        "Backup Success",
                        f"Incremental database backup completed: {backup_file.name}"
                    )
                else:
                    logger.error("❌ Scheduled incremental backup failed")
                    await self._send_notification(
                        "Backup Failed",
                        "Incremental database backup failed. Check logs for details."
                    )

        except Exception as e:
            logger.error(f"Failed to run scheduled incremental backup: {e}")
            await self._send_notification(
                "Backup Error",
                f"Incremental backup failed with error: {str(e)}"
            )

    async def _weekly_full_backup(self):
        """Run weekly full database backup"""
        try:
            logger.info("🔄 Starting scheduled full database backup")

            backup_file = await self.db_backup.create_full_backup(
                compress=self.config.compression
            )

            if backup_file:
                logger.info(f"✅ Scheduled full backup completed: {backup_file}")

                # Also create schema backup for version control
                schema_file = await self.db_backup.create_schema_backup()

                await self._send_notification(
                    "Backup Success",
                    f"Full database backup completed: {backup_file.name}"
                )
            else:
                logger.error("❌ Scheduled full backup failed")
                await self._send_notification(
                    "Backup Failed",
                    "Full database backup failed. Check logs for details."
                )

        except Exception as e:
            logger.error(f"Failed to run scheduled full backup: {e}")
            await self._send_notification(
                "Backup Error",
                f"Full backup failed with error: {str(e)}"
            )

    async def _daily_file_backup(self):
        """Run daily file backup"""
        try:
            logger.info("🔄 Starting scheduled file backup")

            stats = await self.file_backup.backup_all_files()

            total_files = stats["uploads"]["count"] + stats["clips"]["count"]
            total_size_mb = (stats["uploads"]["size_bytes"] + stats["clips"]["size_bytes"]) / 1024 / 1024

            logger.info(f"✅ Scheduled file backup completed: {total_files} files ({total_size_mb:.2f} MB)")

            await self._send_notification(
                "File Backup Success",
                f"Backed up {total_files} files ({total_size_mb:.2f} MB)\n"
                f"Uploads: {stats['uploads']['count']} files\n"
                f"Clips: {stats['clips']['count']} files"
            )

        except Exception as e:
            logger.error(f"Failed to run scheduled file backup: {e}")
            await self._send_notification(
                "File Backup Error",
                f"File backup failed with error: {str(e)}"
            )

    async def _daily_verification(self):
        """Run daily backup verification"""
        try:
            logger.info("🔍 Starting scheduled backup verification")

            report = await self.verifier.verify_all_backups()

            status = report.get("overall_status", "UNKNOWN")

            logger.info(f"Verification completed: {status}")

            if status == "PASSED":
                await self._send_notification(
                    "Verification Success",
                    f"All backups verified successfully\n"
                    f"Database: {report['database']['passed']}/{report['database']['total']}\n"
                    f"Files: {report['files']['passed']}/{report['files']['total']}"
                )
            else:
                await self._send_notification(
                    "Verification Failed",
                    f"Backup verification found issues\n"
                    f"Database: {report['database']['passed']}/{report['database']['total']}\n"
                    f"Files: {report['files']['passed']}/{report['files']['total']}\n"
                    f"Check verification report for details."
                )

        except Exception as e:
            logger.error(f"Failed to run scheduled verification: {e}")
            await self._send_notification(
                "Verification Error",
                f"Backup verification failed with error: {str(e)}"
            )

    async def _weekly_cleanup(self):
        """Run weekly cleanup of old backups"""
        try:
            logger.info("🧹 Starting scheduled backup cleanup")

            # Cleanup database backups
            await self.db_backup.cleanup_old_backups()

            # Cleanup file backups
            await self.file_backup.cleanup_old_files()

            logger.info("✅ Scheduled cleanup completed")

            await self._send_notification(
                "Cleanup Success",
                f"Old backups cleaned up (retention: {self.config.retention_days} days)"
            )

        except Exception as e:
            logger.error(f"Failed to run scheduled cleanup: {e}")
            await self._send_notification(
                "Cleanup Error",
                f"Backup cleanup failed with error: {str(e)}"
            )

    async def _weekly_completeness_check(self):
        """Run weekly backup completeness check"""
        try:
            logger.info("📊 Starting scheduled completeness check")

            report = await self.verifier.check_backup_completeness()

            warnings = report.get("warnings", [])

            if warnings:
                logger.warning(f"Completeness check found {len(warnings)} warnings")

                await self._send_notification(
                    "Backup Completeness Warning",
                    f"Backup completeness check found issues:\n\n" +
                    "\n".join(f"- {w}" for w in warnings)
                )
            else:
                logger.info("✅ Completeness check passed")

                await self._send_notification(
                    "Backup Completeness OK",
                    "All backups are complete and up-to-date"
                )

        except Exception as e:
            logger.error(f"Failed to run completeness check: {e}")

    async def _send_notification(self, subject: str, message: str):
        """Send notification email or webhook"""
        try:
            # Send email notification
            if self.config.notification_email:
                await self._send_email_notification(subject, message)

            # Send webhook notification
            if self.config.notification_webhook:
                await self._send_webhook_notification(subject, message)

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def _send_email_notification(self, subject: str, message: str):
        """Send email notification (placeholder - implement with your email service)"""
        # TODO: Implement email sending using SMTP or email service (SendGrid, SES, etc.)
        logger.info(f"[EMAIL] {subject}: {message}")

    async def _send_webhook_notification(self, subject: str, message: str):
        """Send webhook notification"""
        try:
            import aiohttp
            import json

            async with aiohttp.ClientSession() as session:
                payload = {
                    "subject": subject,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "source": "SupoClip Backup System"
                }

                async with session.post(
                    self.config.notification_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent: {subject}")
                    else:
                        logger.error(f"Webhook notification failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    def start(self):
        """Start the backup scheduler"""
        try:
            self.scheduler.start()
            logger.info("✅ Backup scheduler started")
            logger.info(f"Active jobs: {len(self.scheduler.get_jobs())}")

            for job in self.scheduler.get_jobs():
                logger.info(f"  - {job.name} (ID: {job.id})")

        except Exception as e:
            logger.error(f"Failed to start backup scheduler: {e}")
            raise

    def stop(self):
        """Stop the backup scheduler"""
        try:
            self.scheduler.shutdown(wait=False)
            logger.info("Backup scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop backup scheduler: {e}")

    def get_job_status(self) -> list:
        """Get status of all scheduled jobs"""
        try:
            jobs = []

            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                })

            return jobs

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return []

    async def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a scheduled job"""
        try:
            job = self.scheduler.get_job(job_id)

            if job is None:
                logger.error(f"Job not found: {job_id}")
                return False

            logger.info(f"Manually triggering job: {job.name}")

            # Run the job's function
            await job.func()

            return True

        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False

"""
Example: Integrating Backup System into FastAPI Application

This file shows how to integrate the backup system into your main FastAPI application.
Copy the relevant parts to your src/main.py or src/main_refactored.py
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from src.backup import (
    BackupConfig,
    BackupScheduler,
    DatabaseBackup,
    FileBackup,
    RestoreManager,
    BackupVerifier
)

logger = logging.getLogger(__name__)

# Global backup instances
backup_config = None
backup_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown
    """
    global backup_config, backup_scheduler

    # Startup
    logger.info("Starting backup system...")

    try:
        # Initialize backup configuration
        backup_config = BackupConfig()

        # Initialize and start backup scheduler
        backup_scheduler = BackupScheduler(backup_config)
        backup_scheduler.start()

        logger.info("✅ Backup system started successfully")

        # Print scheduled jobs
        for job in backup_scheduler.get_job_status():
            logger.info(f"  Scheduled: {job['name']} - Next run: {job['next_run']}")

    except Exception as e:
        logger.error(f"Failed to start backup system: {e}")

    yield

    # Shutdown
    logger.info("Stopping backup system...")

    if backup_scheduler:
        backup_scheduler.stop()

    logger.info("Backup system stopped")


# Create FastAPI app with lifespan
app = FastAPI(
    title="SupoClip API",
    description="AI-powered video clipping with automated backups",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# BACKUP API ENDPOINTS
# ============================================================================

@app.get("/backup/status")
async def backup_status():
    """Get backup system status"""
    try:
        if not backup_scheduler:
            return JSONResponse(
                status_code=503,
                content={"error": "Backup system not initialized"}
            )

        jobs = backup_scheduler.get_job_status()

        # Get completeness report
        verifier = BackupVerifier(backup_config)
        completeness = await verifier.check_backup_completeness()

        return {
            "status": "running",
            "scheduled_jobs": jobs,
            "completeness": completeness,
            "config": {
                "storage_backend": backup_config.storage_backend,
                "retention_days": backup_config.retention_days,
                "incremental_enabled": backup_config.enable_incremental,
            }
        }

    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backup/database")
async def create_database_backup(
    background_tasks: BackgroundTasks,
    backup_type: str = "full"
):
    """
    Manually trigger a database backup

    Args:
        backup_type: 'full', 'incremental', or 'schema'
    """
    try:
        db_backup = DatabaseBackup(backup_config)

        async def run_backup():
            if backup_type == "full":
                await db_backup.create_full_backup()
            elif backup_type == "incremental":
                await db_backup.create_incremental_backup()
            elif backup_type == "schema":
                await db_backup.create_schema_backup()
            else:
                raise ValueError(f"Invalid backup type: {backup_type}")

        background_tasks.add_task(run_backup)

        return {
            "message": f"Database backup ({backup_type}) started",
            "backup_type": backup_type
        }

    except Exception as e:
        logger.error(f"Failed to start database backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backup/files")
async def create_file_backup(background_tasks: BackgroundTasks):
    """Manually trigger a file backup"""
    try:
        file_backup = FileBackup(backup_config)

        async def run_backup():
            await file_backup.backup_all_files()

        background_tasks.add_task(run_backup)

        return {
            "message": "File backup started"
        }

    except Exception as e:
        logger.error(f"Failed to start file backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backup/verify")
async def verify_backups(background_tasks: BackgroundTasks):
    """Manually trigger backup verification"""
    try:
        verifier = BackupVerifier(backup_config)

        async def run_verification():
            await verifier.verify_all_backups()

        background_tasks.add_task(run_verification)

        return {
            "message": "Backup verification started"
        }

    except Exception as e:
        logger.error(f"Failed to start verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backup/list")
async def list_backups(backup_type: str = None):
    """
    List available backups

    Args:
        backup_type: Filter by type ('full', 'incremental', 'schema')
    """
    try:
        db_backup = DatabaseBackup(backup_config)
        file_backup = FileBackup(backup_config)

        db_backups = await db_backup.list_backups(backup_type)
        file_backups = await file_backup.list_backed_up_files()

        return {
            "database_backups": db_backups,
            "file_backups": file_backups,
            "total_database": len(db_backups),
            "total_files": len(file_backups)
        }

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backup/job/{job_id}/run")
async def run_backup_job(job_id: str):
    """
    Manually trigger a scheduled backup job

    Args:
        job_id: Job ID (e.g., 'daily_incremental_backup', 'weekly_full_backup')
    """
    try:
        if not backup_scheduler:
            raise HTTPException(status_code=503, detail="Backup scheduler not running")

        success = await backup_scheduler.run_job_now(job_id)

        if success:
            return {
                "message": f"Job {job_id} triggered successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    except Exception as e:
        logger.error(f"Failed to run backup job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OPTIONAL: RESTORE ENDPOINTS (Use with caution!)
# ============================================================================

@app.post("/backup/restore/database")
async def restore_database(
    background_tasks: BackgroundTasks,
    admin_key: str,  # Require admin authentication
):
    """
    ⚠️ DANGEROUS: Restore database from latest backup

    This will OVERWRITE the current database!
    Requires admin authentication.
    """
    try:
        # Verify admin key (implement proper authentication)
        if admin_key != backup_config.config.get("ADMIN_KEY"):
            raise HTTPException(status_code=403, detail="Invalid admin key")

        restore_manager = RestoreManager(backup_config)

        async def run_restore():
            await restore_manager.restore_database_full()

        background_tasks.add_task(run_restore)

        return {
            "message": "⚠️ Database restoration started - system may be unavailable",
            "warning": "Current database will be overwritten"
        }

    except Exception as e:
        logger.error(f"Failed to start database restore: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK WITH BACKUP STATUS
# ============================================================================

@app.get("/health")
async def health_check():
    """Enhanced health check including backup status"""
    try:
        db_backup = DatabaseBackup(backup_config)
        backups = await db_backup.list_backups("full")

        last_backup = None
        if backups:
            last_backup = backups[0]["timestamp"]

        return {
            "status": "healthy",
            "backup_system": {
                "running": backup_scheduler is not None,
                "last_full_backup": last_backup,
                "storage_backend": backup_config.storage_backend
            }
        }

    except Exception as e:
        return {
            "status": "healthy",
            "backup_system": {
                "running": False,
                "error": str(e)
            }
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
1. Start the application:
   uvicorn src.main:app --reload

2. Check backup status:
   curl http://localhost:8000/backup/status

3. Trigger manual backup:
   curl -X POST http://localhost:8000/backup/database?backup_type=full

4. List backups:
   curl http://localhost:8000/backup/list

5. Verify backups:
   curl -X POST http://localhost:8000/backup/verify

6. Run scheduled job manually:
   curl -X POST http://localhost:8000/backup/job/weekly_full_backup/run
"""

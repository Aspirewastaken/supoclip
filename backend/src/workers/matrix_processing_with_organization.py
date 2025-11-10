"""
Enhanced matrix processing with automatic folder organization.

This module extends the matrix processing pipeline to automatically
organize clips into dated folder structure by channel.
"""
import logging
from typing import Dict, Any, List, Optional

from ..utils.folder_organizer import organize_matrix_clips, FolderOrganizer

logger = logging.getLogger(__name__)


async def process_clip_matrix_with_organization(
    ctx: Dict[str, Any],
    task_id: str,
    base_clips: List[Dict[str, Any]],
    video_path: str,
    user_id: str,
    transcript_data: Dict[str, Any],
    video_metadata: Optional[Dict[str, Any]] = None,
    channel_name: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process clips through matrix pipeline with automatic folder organization.

    This function wraps the standard matrix processing and adds automatic
    folder organization by channel and date.

    Args:
        ctx: arq context (provides Redis connection)
        task_id: Task ID for tracking
        base_clips: List of base clip dicts from council deliberation
        video_path: Source video file path
        user_id: User ID
        transcript_data: Full transcript with word-level timing
        video_metadata: Video metadata (for channel extraction)
        channel_name: Optional explicit channel name
        options: Processing options (includes organization settings)

    Returns:
        Dict with processing results including organization info
    """
    from ..workers.matrix_processing import process_clip_matrix
    from ..workers.progress import ProgressTracker

    logger.info(f"🎬 Starting matrix processing with organization for task {task_id}")

    # Create progress tracker
    progress = ProgressTracker(ctx['redis'], task_id)

    # STEP 1: Run standard matrix processing (0-90%)
    await progress.update(0, "Starting matrix processing...", "processing")

    matrix_result = await process_clip_matrix(
        ctx=ctx,
        task_id=task_id,
        base_clips=base_clips,
        video_path=video_path,
        user_id=user_id,
        transcript_data=transcript_data,
        options=options
    )

    if not matrix_result.get('success'):
        logger.error("Matrix processing failed")
        return matrix_result

    # STEP 2: Organize clips into dated folder structure (90-100%)
    await progress.update(90, "Organizing clips into dated folders...", "processing")

    try:
        # Parse organization options
        options = options or {}
        retention_days = options.get('folder_retention_days', 30)
        enable_organization = options.get('enable_folder_organization', True)

        if not enable_organization:
            logger.info("Folder organization disabled, skipping")
            await progress.update(100, "Complete!", "completed")
            return matrix_result

        # Organize clips
        organization_result = organize_matrix_clips(
            matrix_result=matrix_result,
            channel_name=channel_name or "unknown_channel",
            video_metadata=video_metadata,
            task_metadata={
                'task_id': task_id,
                'user_id': user_id,
                'video_path': video_path,
                'base_clips_count': len(base_clips)
            },
            retention_days=retention_days
        )

        logger.info(f"✅ Organization complete: {organization_result['organized_count']} clips organized")

        # Merge results
        matrix_result['organization'] = organization_result
        matrix_result['organized_folder'] = organization_result['folder']
        matrix_result['organized_clips'] = organization_result['organized_clips']

        await progress.update(100, f"Complete! {organization_result['organized_count']} clips organized", "completed")

        return matrix_result

    except Exception as e:
        logger.error(f"Error during folder organization: {e}", exc_info=True)
        await progress.update(
            95,
            f"Warning: Folder organization failed, but clips were generated successfully",
            "processing"
        )

        # Return matrix result even if organization fails
        matrix_result['organization_error'] = str(e)
        await progress.update(100, "Complete (organization failed)", "completed")

        return matrix_result


async def cleanup_old_clip_folders(retention_days: int = 30, dry_run: bool = False) -> Dict[str, Any]:
    """
    Background task to cleanup old clip folders.

    This should be run periodically (e.g., daily) to maintain storage space.

    Args:
        retention_days: Number of days to retain folders
        dry_run: If True, only simulate cleanup

    Returns:
        Dict with cleanup results
    """
    logger.info(f"🧹 Starting clip folder cleanup (retention: {retention_days} days, dry_run: {dry_run})")

    try:
        organizer = FolderOrganizer(retention_days=retention_days)
        result = organizer.cleanup_old_folders(dry_run=dry_run)

        logger.info(f"✅ Cleanup complete: {result['deleted_count']} folders deleted, {result['kept_count']} kept")

        return result

    except Exception as e:
        logger.error(f"Error during folder cleanup: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def get_folder_statistics() -> Dict[str, Any]:
    """
    Get statistics about organized clip folders.

    Returns:
        Dict with folder statistics
    """
    try:
        organizer = FolderOrganizer()
        stats = organizer.get_folder_statistics()

        logger.info(f"📊 Folder statistics: {stats['total_channels']} channels, {stats['total_clips']} clips")

        return {
            'success': True,
            'statistics': stats
        }

    except Exception as e:
        logger.error(f"Error getting folder statistics: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def list_organized_folders(
    channel_name: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    List organized clip folders with optional filtering.

    Args:
        channel_name: Optional channel name filter
        limit: Maximum number of folders to return

    Returns:
        Dict with folder list
    """
    try:
        organizer = FolderOrganizer()
        folders = organizer.list_folders(channel_name=channel_name)

        # Limit results
        folders = folders[:limit]

        logger.info(f"📁 Found {len(folders)} organized folders")

        return {
            'success': True,
            'folders': folders,
            'count': len(folders)
        }

    except Exception as e:
        logger.error(f"Error listing folders: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


# Integration with arq worker

async def register_organization_tasks(worker_settings):
    """
    Register organization-related background tasks with arq worker.

    Add to your arq WorkerSettings:

    ```python
    from .workers.matrix_processing_with_organization import (
        cleanup_old_clip_folders,
        get_folder_statistics
    )

    class WorkerSettings:
        functions = [
            # ... other tasks
            cleanup_old_clip_folders,
            get_folder_statistics,
        ]

        # Optional: Schedule daily cleanup at 2 AM
        cron_jobs = [
            cron(cleanup_old_clip_folders, hour=2, minute=0)
        ]
    ```

    Args:
        worker_settings: arq WorkerSettings instance
    """
    pass  # Documentation only

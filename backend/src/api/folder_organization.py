"""
API endpoints for folder organization management.

Endpoints:
- GET /api/folders/statistics - Get folder statistics
- GET /api/folders/list - List organized folders
- POST /api/folders/cleanup - Trigger folder cleanup
- POST /api/folders/organize - Manually organize existing clips
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..utils.folder_organizer import FolderOrganizer, organize_task_clips
from ..database import AsyncSessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/folders", tags=["folder-organization"])


# Pydantic models

class FolderStatistics(BaseModel):
    """Folder statistics response."""
    success: bool
    total_channels: int
    total_folders: int
    total_clips: int
    channels: dict


class FolderListResponse(BaseModel):
    """Folder list response."""
    success: bool
    folders: List[dict]
    count: int


class CleanupRequest(BaseModel):
    """Cleanup request."""
    retention_days: int = Field(default=30, ge=1, le=365, description="Days to retain folders")
    dry_run: bool = Field(default=False, description="Simulate cleanup without deleting")


class CleanupResponse(BaseModel):
    """Cleanup response."""
    success: bool
    dry_run: bool
    cutoff_date: str
    retention_days: int
    deleted_count: int
    kept_count: int
    error_count: int
    deleted_folders: List[dict] = []
    kept_folders: List[dict] = []
    errors: List[dict] = []


class OrganizeClipsRequest(BaseModel):
    """Manual clip organization request."""
    task_id: str = Field(..., description="Task ID to organize clips for")
    channel_name: Optional[str] = Field(None, description="Override channel name")


class OrganizeClipsResponse(BaseModel):
    """Clip organization response."""
    success: bool
    channel_name: str
    folder: str
    date: str
    organized_count: int
    failed_count: int
    manifest_path: str


# Endpoints

@router.get("/statistics", response_model=FolderStatistics)
async def get_folder_statistics():
    """
    Get statistics about organized clip folders.

    Returns:
        Folder statistics including channel count, folder count, and clip count
    """
    try:
        organizer = FolderOrganizer()
        stats = organizer.get_folder_statistics()

        return FolderStatistics(
            success=True,
            total_channels=stats['total_channels'],
            total_folders=stats['total_folders'],
            total_clips=stats['total_clips'],
            channels=stats['channels']
        )

    except Exception as e:
        logger.error(f"Error getting folder statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/list", response_model=FolderListResponse)
async def list_folders(
    channel_name: Optional[str] = Query(None, description="Filter by channel name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum folders to return")
):
    """
    List organized clip folders with optional filtering.

    Args:
        channel_name: Optional channel name filter
        limit: Maximum number of folders to return (1-200)

    Returns:
        List of organized folders with metadata
    """
    try:
        organizer = FolderOrganizer()
        folders = organizer.list_folders(channel_name=channel_name)

        # Limit results
        folders = folders[:limit]

        return FolderListResponse(
            success=True,
            folders=folders,
            count=len(folders)
        )

    except Exception as e:
        logger.error(f"Error listing folders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list folders: {str(e)}")


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_old_folders(request: CleanupRequest):
    """
    Cleanup folders older than retention period.

    Args:
        request: Cleanup configuration

    Returns:
        Cleanup results including deleted and kept folders
    """
    try:
        organizer = FolderOrganizer(retention_days=request.retention_days)
        result = organizer.cleanup_old_folders(dry_run=request.dry_run)

        return CleanupResponse(
            success=result['success'],
            dry_run=result['dry_run'],
            cutoff_date=result['cutoff_date'],
            retention_days=result['retention_days'],
            deleted_count=result['deleted_count'],
            kept_count=result['kept_count'],
            error_count=result['error_count'],
            deleted_folders=result['deleted_folders'],
            kept_folders=result['kept_folders'],
            errors=result['errors']
        )

    except Exception as e:
        logger.error(f"Error during folder cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/organize", response_model=OrganizeClipsResponse)
async def organize_existing_clips(request: OrganizeClipsRequest):
    """
    Manually organize clips from an existing task.

    This endpoint allows re-organizing clips that were generated without
    folder organization, or moving clips to a different channel folder.

    Args:
        request: Organization request with task_id and optional channel override

    Returns:
        Organization results
    """
    try:
        # Fetch task and clips from database
        async with AsyncSessionLocal() as db:
            # Get task with source
            task_query = text("""
                SELECT t.id, t.user_id, s.title, s.channel_name, s.url
                FROM tasks t
                LEFT JOIN sources s ON t.source_id = s.id
                WHERE t.id = :task_id
            """)
            task_result = await db.execute(task_query, {"task_id": request.task_id})
            task_row = task_result.fetchone()

            if not task_row:
                raise HTTPException(status_code=404, detail=f"Task not found: {request.task_id}")

            # Get clips for task
            clips_query = text("""
                SELECT id, filename, file_path, start_time, end_time, duration,
                       text, relevance_score, reasoning, clip_order
                FROM generated_clips
                WHERE task_id = :task_id
                ORDER BY clip_order
            """)
            clips_result = await db.execute(clips_query, {"task_id": request.task_id})
            clips_rows = clips_result.fetchall()

            if not clips_rows:
                raise HTTPException(status_code=404, detail=f"No clips found for task: {request.task_id}")

        # Prepare clip file paths
        clip_files = [row.file_path for row in clips_rows]

        # Determine channel name
        channel_name = request.channel_name or task_row.channel_name or "unknown_channel"

        # Prepare video metadata
        video_metadata = None
        if task_row.url:
            video_metadata = {
                'uploader': task_row.channel_name,
                'title': task_row.title,
                'url': task_row.url
            }

        # Prepare task metadata
        task_metadata = {
            'task_id': request.task_id,
            'user_id': task_row.user_id,
            'title': task_row.title,
            'clip_count': len(clip_files)
        }

        # Organize clips
        result = organize_task_clips(
            task_id=request.task_id,
            clip_files=clip_files,
            channel_name=channel_name,
            video_metadata=video_metadata,
            task_metadata=task_metadata
        )

        return OrganizeClipsResponse(
            success=result['success'],
            channel_name=result['channel_name'],
            folder=result['folder'],
            date=result['date'],
            organized_count=result['organized_count'],
            failed_count=result['failed_count'],
            manifest_path=result['manifest_path']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error organizing clips: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Organization failed: {str(e)}")


@router.get("/channels")
async def list_channels():
    """
    List all channels with clip folders.

    Returns:
        List of channel names with clip counts
    """
    try:
        organizer = FolderOrganizer()
        stats = organizer.get_folder_statistics()

        channels = [
            {
                'name': channel_name,
                'folders': channel_data['folders'],
                'clips': channel_data['clips'],
                'dates': channel_data['dates']
            }
            for channel_name, channel_data in stats['channels'].items()
        ]

        # Sort by clip count descending
        channels.sort(key=lambda x: x['clips'], reverse=True)

        return {
            'success': True,
            'channels': channels,
            'count': len(channels)
        }

    except Exception as e:
        logger.error(f"Error listing channels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list channels: {str(e)}")


@router.get("/manifest/{channel_name}/{date}")
async def get_folder_manifest(channel_name: str, date: str):
    """
    Get manifest.json for a specific folder.

    Args:
        channel_name: Channel name
        date: Folder date (YYYY-MM-DD format)

    Returns:
        Manifest contents
    """
    try:
        organizer = FolderOrganizer()

        # Parse date
        folder_date = datetime.strptime(date, "%Y-%m-%d")

        # Get folder path
        folder_path = organizer.get_dated_folder_path(channel_name, folder_date)
        manifest_path = folder_path / "manifest.json"

        if not manifest_path.exists():
            raise HTTPException(status_code=404, detail=f"Manifest not found: {manifest_path}")

        # Read manifest
        import json
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        return {
            'success': True,
            'manifest': manifest,
            'path': str(manifest_path)
        }

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date}. Expected YYYY-MM-DD")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading manifest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read manifest: {str(e)}")

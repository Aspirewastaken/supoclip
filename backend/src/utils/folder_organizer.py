"""
Automatic folder organization system for SupoClip clips.

Organizes clips into structure:
  /clips/{channel_name}/{YYYY-MM-DD}/{clip_files}

Features:
- Extract channel name from video metadata or user input
- Create dated folders automatically
- Generate manifest.json with metadata
- Cleanup old folders (configurable retention period)
- Integration with matrix processing worker
"""
import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re

from ..config import Config

logger = logging.getLogger(__name__)
config = Config()


class FolderOrganizer:
    """Manages automatic folder organization for clip files."""

    def __init__(self, base_clips_dir: Optional[str] = None, retention_days: int = 30):
        """
        Initialize folder organizer.

        Args:
            base_clips_dir: Base directory for clips (defaults to config.temp_dir/clips)
            retention_days: Number of days to retain old folders (default: 30)
        """
        self.base_clips_dir = Path(base_clips_dir or os.path.join(config.temp_dir, "clips"))
        self.retention_days = retention_days
        self.base_clips_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FolderOrganizer initialized: {self.base_clips_dir}")

    def sanitize_channel_name(self, channel_name: str) -> str:
        """
        Sanitize channel name for use in filesystem.

        Args:
            channel_name: Raw channel name

        Returns:
            Sanitized channel name safe for filesystem
        """
        if not channel_name:
            return "unknown_channel"

        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', channel_name)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Remove consecutive underscores
        sanitized = re.sub(r'_{2,}', '_', sanitized)
        # Trim and lowercase
        sanitized = sanitized.strip('_').lower()
        # Limit length
        sanitized = sanitized[:100]

        return sanitized or "unknown_channel"

    def get_channel_name_from_metadata(
        self,
        video_metadata: Optional[Dict[str, Any]] = None,
        user_input: Optional[str] = None
    ) -> str:
        """
        Extract channel name from video metadata or user input.

        Priority:
        1. User input (if provided)
        2. Video metadata (uploader field)
        3. Default "unknown_channel"

        Args:
            video_metadata: Video metadata dict (from YouTube or other source)
            user_input: User-provided channel name

        Returns:
            Sanitized channel name
        """
        # Priority 1: User input
        if user_input:
            return self.sanitize_channel_name(user_input)

        # Priority 2: Video metadata
        if video_metadata:
            # Try multiple fields
            for field in ['uploader', 'channel', 'channel_name', 'creator']:
                if field in video_metadata and video_metadata[field]:
                    return self.sanitize_channel_name(video_metadata[field])

        # Default fallback
        return "unknown_channel"

    def get_dated_folder_path(
        self,
        channel_name: str,
        date: Optional[datetime] = None
    ) -> Path:
        """
        Get dated folder path for channel.

        Args:
            channel_name: Sanitized channel name
            date: Date for folder (defaults to today)

        Returns:
            Path to dated folder
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        folder_path = self.base_clips_dir / channel_name / date_str

        return folder_path

    def create_dated_folder(
        self,
        channel_name: str,
        date: Optional[datetime] = None
    ) -> Path:
        """
        Create dated folder structure.

        Args:
            channel_name: Sanitized channel name
            date: Date for folder (defaults to today)

        Returns:
            Path to created folder
        """
        folder_path = self.get_dated_folder_path(channel_name, date)
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created folder: {folder_path}")
        return folder_path

    def organize_clip(
        self,
        clip_path: str,
        channel_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Organize a single clip into dated folder structure.

        Args:
            clip_path: Path to clip file
            channel_name: Channel name (will be sanitized)
            metadata: Optional metadata for the clip
            date: Date for folder (defaults to today)

        Returns:
            Dict with organized file information
        """
        clip_path = Path(clip_path)

        if not clip_path.exists():
            logger.error(f"Clip file not found: {clip_path}")
            raise FileNotFoundError(f"Clip file not found: {clip_path}")

        # Sanitize channel name
        sanitized_channel = self.sanitize_channel_name(channel_name)

        # Create dated folder
        target_folder = self.create_dated_folder(sanitized_channel, date)

        # Determine target filename
        filename = clip_path.name
        target_path = target_folder / filename

        # Handle filename conflicts
        counter = 1
        while target_path.exists():
            stem = clip_path.stem
            suffix = clip_path.suffix
            filename = f"{stem}_{counter}{suffix}"
            target_path = target_folder / filename
            counter += 1

        # Move or copy file
        try:
            shutil.move(str(clip_path), str(target_path))
            logger.info(f"Moved clip: {clip_path.name} -> {target_path}")
        except Exception as e:
            logger.warning(f"Failed to move, trying copy: {e}")
            shutil.copy2(str(clip_path), str(target_path))
            logger.info(f"Copied clip: {clip_path.name} -> {target_path}")

        # Return organized file info
        result = {
            'original_path': str(clip_path),
            'new_path': str(target_path),
            'filename': filename,
            'channel_name': sanitized_channel,
            'folder': str(target_folder),
            'date': (date or datetime.now()).strftime("%Y-%m-%d"),
            'metadata': metadata or {}
        }

        return result

    def organize_clips_batch(
        self,
        clips: List[Dict[str, Any]],
        channel_name: str,
        task_metadata: Optional[Dict[str, Any]] = None,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Organize multiple clips into dated folder structure.

        Args:
            clips: List of clip dicts with 'file_path' and optional metadata
            channel_name: Channel name (will be sanitized)
            task_metadata: Optional task-level metadata
            date: Date for folder (defaults to today)

        Returns:
            Dict with batch organization results
        """
        sanitized_channel = self.sanitize_channel_name(channel_name)
        target_folder = self.create_dated_folder(sanitized_channel, date)

        organized_clips = []
        failed_clips = []

        for clip in clips:
            try:
                clip_path = clip.get('file_path')
                if not clip_path:
                    logger.warning(f"Clip missing file_path: {clip}")
                    failed_clips.append({'clip': clip, 'error': 'Missing file_path'})
                    continue

                result = self.organize_clip(
                    clip_path=clip_path,
                    channel_name=sanitized_channel,
                    metadata=clip,
                    date=date
                )
                organized_clips.append(result)

            except Exception as e:
                logger.error(f"Failed to organize clip {clip.get('file_path')}: {e}")
                failed_clips.append({'clip': clip, 'error': str(e)})

        # Generate manifest
        manifest_path = self.generate_manifest(
            folder_path=target_folder,
            clips=organized_clips,
            channel_name=sanitized_channel,
            task_metadata=task_metadata
        )

        result = {
            'success': True,
            'channel_name': sanitized_channel,
            'folder': str(target_folder),
            'date': (date or datetime.now()).strftime("%Y-%m-%d"),
            'organized_count': len(organized_clips),
            'failed_count': len(failed_clips),
            'organized_clips': organized_clips,
            'failed_clips': failed_clips,
            'manifest_path': str(manifest_path)
        }

        logger.info(f"Batch organization complete: {len(organized_clips)} clips organized, {len(failed_clips)} failed")
        return result

    def generate_manifest(
        self,
        folder_path: Path,
        clips: List[Dict[str, Any]],
        channel_name: str,
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate manifest.json in folder with metadata.

        Args:
            folder_path: Path to folder
            clips: List of organized clip dicts
            channel_name: Channel name
            task_metadata: Optional task-level metadata

        Returns:
            Path to manifest file
        """
        manifest = {
            'version': '1.0',
            'channel_name': channel_name,
            'folder': str(folder_path),
            'created_at': datetime.now().isoformat(),
            'total_clips': len(clips),
            'clips': clips,
            'task_metadata': task_metadata or {}
        }

        manifest_path = folder_path / "manifest.json"

        # Merge with existing manifest if present
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    existing = json.load(f)

                # Merge clips
                existing_clips = existing.get('clips', [])
                existing_files = {c['filename'] for c in existing_clips}

                for clip in clips:
                    if clip['filename'] not in existing_files:
                        existing_clips.append(clip)

                manifest['clips'] = existing_clips
                manifest['total_clips'] = len(existing_clips)
                manifest['updated_at'] = datetime.now().isoformat()
                manifest['created_at'] = existing.get('created_at', manifest['created_at'])

                logger.info(f"Merged with existing manifest: {manifest_path}")

            except Exception as e:
                logger.warning(f"Failed to merge with existing manifest: {e}")

        # Write manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Generated manifest: {manifest_path}")
        return manifest_path

    def cleanup_old_folders(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Cleanup folders older than retention period.

        Args:
            dry_run: If True, only simulate cleanup without deleting

        Returns:
            Dict with cleanup results
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        logger.info(f"Cleaning up folders older than {cutoff_date.strftime('%Y-%m-%d')} (retention: {self.retention_days} days)")

        deleted_folders = []
        kept_folders = []
        errors = []

        # Iterate through channel folders
        for channel_folder in self.base_clips_dir.iterdir():
            if not channel_folder.is_dir():
                continue

            # Iterate through dated folders
            for dated_folder in channel_folder.iterdir():
                if not dated_folder.is_dir():
                    continue

                # Parse folder date
                try:
                    folder_date = datetime.strptime(dated_folder.name, "%Y-%m-%d")

                    if folder_date < cutoff_date:
                        # Delete old folder
                        if not dry_run:
                            shutil.rmtree(dated_folder)
                            logger.info(f"Deleted old folder: {dated_folder}")

                        deleted_folders.append({
                            'path': str(dated_folder),
                            'channel': channel_folder.name,
                            'date': folder_date.strftime("%Y-%m-%d"),
                            'age_days': (datetime.now() - folder_date).days
                        })
                    else:
                        kept_folders.append({
                            'path': str(dated_folder),
                            'channel': channel_folder.name,
                            'date': folder_date.strftime("%Y-%m-%d")
                        })

                except ValueError:
                    logger.warning(f"Skipping folder with invalid date format: {dated_folder}")
                    errors.append({
                        'path': str(dated_folder),
                        'error': 'Invalid date format'
                    })
                except Exception as e:
                    logger.error(f"Error processing folder {dated_folder}: {e}")
                    errors.append({
                        'path': str(dated_folder),
                        'error': str(e)
                    })

        result = {
            'success': True,
            'dry_run': dry_run,
            'cutoff_date': cutoff_date.strftime("%Y-%m-%d"),
            'retention_days': self.retention_days,
            'deleted_count': len(deleted_folders),
            'kept_count': len(kept_folders),
            'error_count': len(errors),
            'deleted_folders': deleted_folders,
            'kept_folders': kept_folders,
            'errors': errors
        }

        if dry_run:
            logger.info(f"Cleanup dry run: {len(deleted_folders)} folders would be deleted")
        else:
            logger.info(f"Cleanup complete: {len(deleted_folders)} folders deleted, {len(kept_folders)} kept")

        return result

    def get_folder_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about organized folders.

        Returns:
            Dict with folder statistics
        """
        stats = {
            'total_channels': 0,
            'total_folders': 0,
            'total_clips': 0,
            'channels': {}
        }

        for channel_folder in self.base_clips_dir.iterdir():
            if not channel_folder.is_dir():
                continue

            channel_name = channel_folder.name
            stats['total_channels'] += 1
            stats['channels'][channel_name] = {
                'folders': 0,
                'clips': 0,
                'dates': []
            }

            for dated_folder in channel_folder.iterdir():
                if not dated_folder.is_dir():
                    continue

                stats['total_folders'] += 1
                stats['channels'][channel_name]['folders'] += 1
                stats['channels'][channel_name]['dates'].append(dated_folder.name)

                # Count clips in folder
                clip_count = len(list(dated_folder.glob("*.mp4")))
                stats['total_clips'] += clip_count
                stats['channels'][channel_name]['clips'] += clip_count

        return stats

    def list_folders(
        self,
        channel_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List organized folders with optional filtering.

        Args:
            channel_name: Filter by channel name
            date_from: Filter folders from this date
            date_to: Filter folders up to this date

        Returns:
            List of folder dicts
        """
        folders = []

        # Determine which channels to scan
        if channel_name:
            channel_name = self.sanitize_channel_name(channel_name)
            channel_folders = [self.base_clips_dir / channel_name]
        else:
            channel_folders = [f for f in self.base_clips_dir.iterdir() if f.is_dir()]

        for channel_folder in channel_folders:
            if not channel_folder.exists():
                continue

            for dated_folder in channel_folder.iterdir():
                if not dated_folder.is_dir():
                    continue

                try:
                    folder_date = datetime.strptime(dated_folder.name, "%Y-%m-%d")

                    # Apply date filters
                    if date_from and folder_date < date_from:
                        continue
                    if date_to and folder_date > date_to:
                        continue

                    # Count clips
                    clip_count = len(list(dated_folder.glob("*.mp4")))

                    # Check for manifest
                    manifest_path = dated_folder / "manifest.json"
                    has_manifest = manifest_path.exists()

                    folders.append({
                        'path': str(dated_folder),
                        'channel': channel_folder.name,
                        'date': folder_date.strftime("%Y-%m-%d"),
                        'clip_count': clip_count,
                        'has_manifest': has_manifest,
                        'manifest_path': str(manifest_path) if has_manifest else None
                    })

                except ValueError:
                    logger.warning(f"Skipping folder with invalid date: {dated_folder}")

        # Sort by date descending
        folders.sort(key=lambda x: x['date'], reverse=True)

        return folders


# Helper functions for integration


def organize_matrix_clips(
    matrix_result: Dict[str, Any],
    channel_name: str,
    video_metadata: Optional[Dict[str, Any]] = None,
    task_metadata: Optional[Dict[str, Any]] = None,
    retention_days: int = 30
) -> Dict[str, Any]:
    """
    Organize matrix processing results into dated folder structure.

    Integration point for matrix processing worker.

    Args:
        matrix_result: Result dict from process_clip_matrix
        channel_name: Channel name (or will be extracted from video_metadata)
        video_metadata: Optional video metadata for channel extraction
        task_metadata: Optional task metadata
        retention_days: Folder retention period in days

    Returns:
        Dict with organization results
    """
    organizer = FolderOrganizer(retention_days=retention_days)

    # Extract channel name
    final_channel_name = organizer.get_channel_name_from_metadata(
        video_metadata=video_metadata,
        user_input=channel_name
    )

    # Get clips from matrix result
    clips = matrix_result.get('variations', [])

    # Organize clips
    result = organizer.organize_clips_batch(
        clips=clips,
        channel_name=final_channel_name,
        task_metadata=task_metadata,
        date=datetime.now()
    )

    return result


def organize_task_clips(
    task_id: str,
    clip_files: List[str],
    channel_name: str,
    video_metadata: Optional[Dict[str, Any]] = None,
    task_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Organize clips from a task into dated folder structure.

    Args:
        task_id: Task ID
        clip_files: List of clip file paths
        channel_name: Channel name
        video_metadata: Optional video metadata
        task_metadata: Optional task metadata

    Returns:
        Dict with organization results
    """
    organizer = FolderOrganizer()

    # Extract channel name
    final_channel_name = organizer.get_channel_name_from_metadata(
        video_metadata=video_metadata,
        user_input=channel_name
    )

    # Convert file paths to clip dicts
    clips = [{'file_path': path} for path in clip_files]

    # Add task_id to metadata
    if task_metadata is None:
        task_metadata = {}
    task_metadata['task_id'] = task_id

    # Organize clips
    result = organizer.organize_clips_batch(
        clips=clips,
        channel_name=final_channel_name,
        task_metadata=task_metadata,
        date=datetime.now()
    )

    return result

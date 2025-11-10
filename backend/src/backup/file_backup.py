"""
File Backup Module

Handles backup of video files and generated clips:
- Original uploaded videos
- Downloaded YouTube videos
- Generated clips
- Metadata preservation (transcripts, thumbnails, etc.)
"""

import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .config import BackupConfig
from .storage_backends import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)


class FileBackup:
    """Manages file backups for videos and clips"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.storage = get_storage_backend(config)
        self.backup_dir = config.backup_dir / "files"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def backup_all_files(self) -> Dict[str, Any]:
        """
        Backup all video files and clips

        Returns:
            Dictionary with backup statistics
        """
        logger.info("Starting full file backup")

        stats = {
            "uploads": {"count": 0, "size_bytes": 0, "failed": []},
            "clips": {"count": 0, "size_bytes": 0, "failed": []},
            "metadata": {"count": 0, "size_bytes": 0, "failed": []},
            "start_time": datetime.now().isoformat(),
        }

        # Backup uploaded videos
        if self.config.uploads_dir.exists():
            await self._backup_directory(
                self.config.uploads_dir,
                "uploads",
                stats["uploads"]
            )

        # Backup generated clips
        if self.config.clips_dir.exists():
            await self._backup_directory(
                self.config.clips_dir,
                "clips",
                stats["clips"]
            )

        # Backup associated metadata (transcripts, cache files, etc.)
        await self._backup_metadata(stats["metadata"])

        stats["end_time"] = datetime.now().isoformat()

        # Save backup report
        await self._save_backup_report(stats)

        logger.info(
            f"File backup completed. "
            f"Uploads: {stats['uploads']['count']} files ({stats['uploads']['size_bytes'] / 1024 / 1024:.2f} MB), "
            f"Clips: {stats['clips']['count']} files ({stats['clips']['size_bytes'] / 1024 / 1024:.2f} MB)"
        )

        return stats

    async def backup_file(self, file_path: Path, category: str = "uploads") -> bool:
        """
        Backup a single file

        Args:
            file_path: Path to the file to backup
            category: Category (uploads, clips, metadata)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return False

            # Calculate file hash for integrity verification
            file_hash = await self._calculate_file_hash(file_path)

            # Determine remote path
            timestamp = datetime.now().strftime("%Y%m%d")
            remote_path = f"files/{category}/{timestamp}/{file_path.name}"

            # Upload file
            success = await self.storage.upload_file(file_path, remote_path)

            if success:
                # Save file metadata
                metadata = {
                    "filename": file_path.name,
                    "category": category,
                    "size_bytes": file_path.stat().st_size,
                    "hash_sha256": file_hash,
                    "backup_time": datetime.now().isoformat(),
                    "remote_path": remote_path,
                }

                await self._save_file_metadata(file_path.name, metadata)

            return success

        except Exception as e:
            logger.error(f"Failed to backup file {file_path}: {e}")
            return False

    async def backup_directory(self, directory: Path, category: str = "uploads") -> Dict[str, Any]:
        """
        Backup an entire directory

        Args:
            directory: Directory to backup
            category: Category for organization

        Returns:
            Statistics dictionary
        """
        stats = {"count": 0, "size_bytes": 0, "failed": []}

        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return stats

        await self._backup_directory(directory, category, stats)

        return stats

    async def _backup_directory(self, directory: Path, category: str, stats: Dict):
        """Internal method to backup a directory recursively"""
        try:
            # Get all files (including in subdirectories)
            files = [f for f in directory.rglob("*") if f.is_file()]

            logger.info(f"Backing up {len(files)} files from {directory}")

            # Process files with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent uploads

            async def backup_with_limit(file_path):
                async with semaphore:
                    return await self._backup_single_file(file_path, category, stats)

            # Backup all files concurrently (with limit)
            await asyncio.gather(*[backup_with_limit(f) for f in files])

        except Exception as e:
            logger.error(f"Failed to backup directory {directory}: {e}")

    async def _backup_single_file(self, file_path: Path, category: str, stats: Dict) -> bool:
        """Backup a single file and update stats"""
        try:
            success = await self.backup_file(file_path, category)

            if success:
                stats["count"] += 1
                stats["size_bytes"] += file_path.stat().st_size
            else:
                stats["failed"].append(str(file_path))

            return success

        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            stats["failed"].append(str(file_path))
            return False

    async def _backup_metadata(self, stats: Dict):
        """Backup metadata files (transcripts, cache files, etc.)"""
        try:
            # Backup transcript cache files
            for cache_file in self.config.temp_dir.rglob(".transcript_cache.json"):
                await self._backup_single_file(cache_file, "metadata", stats)

            # Backup any other metadata files
            for meta_file in self.config.temp_dir.rglob("*.meta.json"):
                await self._backup_single_file(meta_file, "metadata", stats)

        except Exception as e:
            logger.error(f"Failed to backup metadata: {e}")

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            sha256_hash = hashlib.sha256()

            def read_chunks():
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        sha256_hash.update(chunk)
                return sha256_hash.hexdigest()

            # Run in thread pool to avoid blocking
            return await asyncio.to_thread(read_chunks)

        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    async def _save_file_metadata(self, filename: str, metadata: Dict):
        """Save metadata for a backed up file"""
        metadata_dir = self.config.backup_dir / "metadata" / "files"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        # Use timestamp + filename for metadata file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        meta_filename = f"{timestamp}_{filename}.meta.json"
        meta_path = metadata_dir / meta_filename

        meta_path.write_text(json.dumps(metadata, indent=2))

    async def _save_backup_report(self, stats: Dict):
        """Save backup report with statistics"""
        report_dir = self.config.backup_dir / "metadata" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"file_backup_report_{timestamp}.json"

        report_path.write_text(json.dumps(stats, indent=2))

        logger.info(f"Backup report saved to {report_path}")

        # Upload report to remote storage
        await self.storage.upload_file(report_path, f"metadata/reports/{report_path.name}")

    async def verify_backup(self, filename: str, category: str = "uploads") -> bool:
        """
        Verify a backed up file by comparing hashes

        Args:
            filename: Name of the file to verify
            category: Category where the file was backed up

        Returns:
            True if verification successful, False otherwise
        """
        try:
            # Find the metadata file
            metadata_dir = self.config.backup_dir / "metadata" / "files"
            meta_files = list(metadata_dir.glob(f"*_{filename}.meta.json"))

            if not meta_files:
                logger.warning(f"No metadata found for {filename}")
                return False

            # Use the most recent metadata
            latest_meta = max(meta_files, key=lambda p: p.stat().st_mtime)
            metadata = json.loads(latest_meta.read_text())

            # Download file from remote storage
            temp_path = self.backup_dir / f"temp_{filename}"
            remote_path = metadata["remote_path"]

            success = await self.storage.download_file(remote_path, temp_path)

            if not success:
                logger.error(f"Failed to download {remote_path} for verification")
                return False

            # Calculate hash of downloaded file
            downloaded_hash = await self._calculate_file_hash(temp_path)

            # Compare hashes
            verified = downloaded_hash == metadata["hash_sha256"]

            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

            if verified:
                logger.info(f"Backup verification successful for {filename}")
            else:
                logger.error(f"Backup verification failed for {filename}. Hash mismatch!")

            return verified

        except Exception as e:
            logger.error(f"Failed to verify backup for {filename}: {e}")
            return False

    async def list_backed_up_files(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all backed up files

        Args:
            category: Filter by category (uploads, clips, metadata)

        Returns:
            List of file metadata dictionaries
        """
        try:
            metadata_dir = self.config.backup_dir / "metadata" / "files"

            if not metadata_dir.exists():
                return []

            files = []

            for meta_file in metadata_dir.glob("*.meta.json"):
                try:
                    metadata = json.loads(meta_file.read_text())

                    if category is None or metadata.get("category") == category:
                        files.append(metadata)

                except Exception as e:
                    logger.warning(f"Failed to read {meta_file}: {e}")

            # Sort by backup time (newest first)
            files.sort(key=lambda x: x.get("backup_time", ""), reverse=True)

            return files

        except Exception as e:
            logger.error(f"Failed to list backed up files: {e}")
            return []

    async def cleanup_old_files(self):
        """Remove backed up files older than retention period"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)

            logger.info(f"Cleaning up file backups older than {cutoff_date}")

            files = await self.list_backed_up_files()
            deleted_count = 0

            for file_meta in files:
                backup_time = datetime.fromisoformat(file_meta["backup_time"])

                if backup_time < cutoff_date:
                    # Delete from remote storage
                    remote_path = file_meta["remote_path"]
                    success = await self.storage.delete_file(remote_path)

                    if success:
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {remote_path}")

            logger.info(f"Cleaned up {deleted_count} old file backups")

        except Exception as e:
            logger.error(f"Failed to cleanup old file backups: {e}")

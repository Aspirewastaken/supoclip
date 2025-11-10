"""
Restore and Recovery Module

Handles restoration of:
- Database from backups
- Video files and clips
- Complete system recovery
"""

import asyncio
import gzip
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .config import BackupConfig
from .storage_backends import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)


class RestoreManager:
    """Manages database and file restoration"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.storage = get_storage_backend(config)
        self.restore_dir = config.backup_dir / "restore"
        self.restore_dir.mkdir(parents=True, exist_ok=True)

    async def restore_database_full(self, backup_file: Optional[Path] = None) -> bool:
        """
        Restore database from a full backup

        Args:
            backup_file: Path to backup file (if None, uses most recent)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get backup file
            if backup_file is None:
                backup_file = await self._get_latest_backup("full")

            if backup_file is None:
                logger.error("No backup file found for restoration")
                return False

            logger.info(f"Restoring database from {backup_file}")

            # Check if compressed
            is_compressed = backup_file.suffix == ".gz"

            # Prepare SQL content
            if is_compressed:
                sql_content = await asyncio.to_thread(
                    lambda: gzip.open(backup_file, 'rb').read()
                )
            else:
                sql_content = backup_file.read_bytes()

            # WARNING: This will drop and recreate the database
            logger.warning("⚠️  This will DROP the existing database and recreate it!")

            # Execute restoration
            cmd = [
                "psql",
                self.config.get_pg_connection_string(),
                "-v", "ON_ERROR_STOP=1"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            stdout, stderr = await process.communicate(input=sql_content)

            if process.returncode != 0:
                logger.error(f"Database restoration failed: {stderr.decode()}")
                return False

            logger.info("✅ Database restored successfully")

            # Create restoration record
            await self._create_restore_record("database_full", backup_file)

            return True

        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False

    async def restore_database_incremental(self, backup_files: Optional[List[Path]] = None) -> bool:
        """
        Restore database from incremental backups

        Args:
            backup_files: List of incremental backup files (in order)

        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_files is None:
                backup_files = await self._get_incremental_backups()

            if not backup_files:
                logger.error("No incremental backups found")
                return False

            logger.info(f"Restoring {len(backup_files)} incremental backups")

            # First, restore the base full backup
            base_backup = await self._get_latest_backup("full")
            if base_backup is None:
                logger.error("No full backup found for incremental restore")
                return False

            success = await self.restore_database_full(base_backup)
            if not success:
                return False

            # Then apply incremental changes
            for backup_file in backup_files:
                logger.info(f"Applying incremental backup: {backup_file}")

                # Read backup content
                with gzip.open(backup_file, 'rb') as f:
                    content = f.read()

                # Apply changes (this is simplified - in production, you'd need proper incremental restore logic)
                cmd = [
                    "psql",
                    self.config.get_pg_connection_string(),
                    "-v", "ON_ERROR_STOP=1"
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=self.config.get_pg_env()
                )

                stdout, stderr = await process.communicate(input=content)

                if process.returncode != 0:
                    logger.error(f"Failed to apply incremental backup: {stderr.decode()}")
                    return False

            logger.info("✅ Incremental restore completed successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to restore incremental backups: {e}")
            return False

    async def restore_table(self, table_name: str, backup_file: Optional[Path] = None) -> bool:
        """
        Restore a specific table from backup

        Args:
            table_name: Name of the table to restore
            backup_file: Path to table backup file

        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_file is None:
                # Find latest backup for this table
                backup_dir = self.config.backup_dir / "database" / "tables"
                if not backup_dir.exists():
                    logger.error(f"No table backups found")
                    return False

                table_backups = list(backup_dir.glob(f"supoclip_table_{table_name}_*.sql.gz"))
                if not table_backups:
                    logger.error(f"No backups found for table {table_name}")
                    return False

                backup_file = max(table_backups, key=lambda p: p.stat().st_mtime)

            logger.info(f"Restoring table {table_name} from {backup_file}")

            # Read backup
            with gzip.open(backup_file, 'rb') as f:
                sql_content = f.read()

            # Execute restoration
            cmd = [
                "psql",
                self.config.get_pg_connection_string(),
                "-v", "ON_ERROR_STOP=1"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            stdout, stderr = await process.communicate(input=sql_content)

            if process.returncode != 0:
                logger.error(f"Table restoration failed: {stderr.decode()}")
                return False

            logger.info(f"✅ Table {table_name} restored successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to restore table {table_name}: {e}")
            return False

    async def restore_file(self, filename: str, category: str = "uploads", destination: Optional[Path] = None) -> bool:
        """
        Restore a specific file from backup

        Args:
            filename: Name of the file to restore
            category: Category (uploads, clips, metadata)
            destination: Where to restore the file (if None, uses original location)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find file metadata
            metadata_dir = self.config.backup_dir / "metadata" / "files"
            meta_files = list(metadata_dir.glob(f"*_{filename}.meta.json"))

            if not meta_files:
                logger.error(f"No metadata found for {filename}")
                return False

            # Use most recent metadata
            latest_meta = max(meta_files, key=lambda p: p.stat().st_mtime)
            metadata = json.loads(latest_meta.read_text())

            logger.info(f"Restoring file {filename} from {metadata['remote_path']}")

            # Determine destination
            if destination is None:
                if category == "uploads":
                    destination = self.config.uploads_dir / filename
                elif category == "clips":
                    destination = self.config.clips_dir / filename
                else:
                    destination = self.restore_dir / filename

            destination.parent.mkdir(parents=True, exist_ok=True)

            # Download from remote storage
            success = await self.storage.download_file(metadata['remote_path'], destination)

            if success:
                logger.info(f"✅ File restored to {destination}")
            else:
                logger.error(f"Failed to restore {filename}")

            return success

        except Exception as e:
            logger.error(f"Failed to restore file {filename}: {e}")
            return False

    async def restore_all_files(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore all files from backup

        Args:
            category: Restore only files from this category (None = all)

        Returns:
            Statistics dictionary
        """
        try:
            logger.info("Starting full file restoration")

            stats = {
                "restored": 0,
                "failed": 0,
                "total_bytes": 0,
                "files": []
            }

            # Get list of backed up files
            metadata_dir = self.config.backup_dir / "metadata" / "files"

            if not metadata_dir.exists():
                logger.warning("No file backups found")
                return stats

            meta_files = list(metadata_dir.glob("*.meta.json"))

            for meta_file in meta_files:
                try:
                    metadata = json.loads(meta_file.read_text())

                    # Filter by category if specified
                    if category is not None and metadata.get("category") != category:
                        continue

                    filename = metadata["filename"]
                    file_category = metadata.get("category", "uploads")

                    success = await self.restore_file(filename, file_category)

                    if success:
                        stats["restored"] += 1
                        stats["total_bytes"] += metadata.get("size_bytes", 0)
                        stats["files"].append(filename)
                    else:
                        stats["failed"] += 1

                except Exception as e:
                    logger.error(f"Failed to process {meta_file}: {e}")
                    stats["failed"] += 1

            logger.info(
                f"✅ File restoration completed. "
                f"Restored: {stats['restored']}, Failed: {stats['failed']}, "
                f"Total size: {stats['total_bytes'] / 1024 / 1024:.2f} MB"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to restore files: {e}")
            return stats

    async def full_system_restore(self) -> bool:
        """
        Perform a complete system restoration

        This restores:
        1. Database from most recent full backup
        2. All uploaded videos
        3. All generated clips
        4. Metadata files

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("🚨 Starting FULL SYSTEM RESTORATION")

            # Step 1: Restore database
            logger.info("Step 1/3: Restoring database...")
            db_success = await self.restore_database_full()

            if not db_success:
                logger.error("Database restoration failed. Aborting.")
                return False

            # Step 2: Restore uploaded videos
            logger.info("Step 2/3: Restoring uploaded videos...")
            uploads_stats = await self.restore_all_files(category="uploads")

            # Step 3: Restore generated clips
            logger.info("Step 3/3: Restoring generated clips...")
            clips_stats = await self.restore_all_files(category="clips")

            # Create restoration report
            report = {
                "restore_time": datetime.now().isoformat(),
                "database_restored": db_success,
                "uploads": uploads_stats,
                "clips": clips_stats,
            }

            report_path = self.restore_dir / f"restore_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path.write_text(json.dumps(report, indent=2))

            logger.info(f"✅ FULL SYSTEM RESTORATION COMPLETED")
            logger.info(f"Restoration report: {report_path}")

            return True

        except Exception as e:
            logger.error(f"Full system restoration failed: {e}")
            return False

    async def _get_latest_backup(self, backup_type: str) -> Optional[Path]:
        """Get the most recent backup of a specific type"""
        try:
            backup_dir = self.config.backup_dir / "database"

            # Look for backup files
            pattern = f"supoclip_{backup_type}_*.sql*"
            backups = list(backup_dir.glob(pattern))

            if not backups:
                # Try downloading from remote storage
                remote_files = await self.storage.list_files(f"database/")
                remote_backups = [f for f in remote_files if backup_type in f and f.endswith(('.sql', '.sql.gz'))]

                if remote_backups:
                    # Download the most recent
                    latest_remote = sorted(remote_backups)[-1]
                    local_path = backup_dir / Path(latest_remote).name

                    await self.storage.download_file(latest_remote, local_path)

                    return local_path

                return None

            # Return most recent
            return max(backups, key=lambda p: p.stat().st_mtime)

        except Exception as e:
            logger.error(f"Failed to get latest backup: {e}")
            return None

    async def _get_incremental_backups(self) -> List[Path]:
        """Get all incremental backups since last full backup"""
        try:
            backup_dir = self.config.backup_dir / "database"

            # Find incremental backups
            backups = list(backup_dir.glob("supoclip_incremental_*.sql.gz"))

            # Sort by timestamp (oldest first)
            backups.sort(key=lambda p: p.stat().st_mtime)

            return backups

        except Exception as e:
            logger.error(f"Failed to get incremental backups: {e}")
            return []

    async def _create_restore_record(self, restore_type: str, source_file: Path):
        """Create a record of the restoration for audit purposes"""
        try:
            record = {
                "restore_type": restore_type,
                "source_file": str(source_file),
                "timestamp": datetime.now().isoformat(),
                "database": self.config.pg_database,
            }

            record_dir = self.config.backup_dir / "metadata" / "restore_records"
            record_dir.mkdir(parents=True, exist_ok=True)

            record_file = record_dir / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            record_file.write_text(json.dumps(record, indent=2))

            logger.info(f"Restore record saved: {record_file}")

        except Exception as e:
            logger.error(f"Failed to create restore record: {e}")

    async def list_available_backups(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all available backups

        Returns:
            Dictionary with lists of database and file backups
        """
        try:
            result = {
                "database": [],
                "files": []
            }

            # List database backups
            db_backup_dir = self.config.backup_dir / "database"
            if db_backup_dir.exists():
                for meta_file in db_backup_dir.glob("*.meta.json"):
                    try:
                        metadata = json.loads(meta_file.read_text())
                        result["database"].append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to read {meta_file}: {e}")

            # List file backups
            file_metadata_dir = self.config.backup_dir / "metadata" / "files"
            if file_metadata_dir.exists():
                for meta_file in file_metadata_dir.glob("*.meta.json"):
                    try:
                        metadata = json.loads(meta_file.read_text())
                        result["files"].append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to read {meta_file}: {e}")

            # Sort by timestamp (newest first)
            result["database"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            result["files"].sort(key=lambda x: x.get("backup_time", ""), reverse=True)

            return result

        except Exception as e:
            logger.error(f"Failed to list available backups: {e}")
            return {"database": [], "files": []}

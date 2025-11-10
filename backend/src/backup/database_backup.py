"""
Database Backup Module

Handles PostgreSQL database backups:
- Full database dumps
- Incremental backups (WAL archiving)
- Schema-only backups
- Data-only backups
- Compressed backups
"""

import asyncio
import gzip
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .config import BackupConfig
from .storage_backends import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Manages PostgreSQL database backups"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.storage = get_storage_backend(config)
        self.backup_dir = config.backup_dir / "database"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_full_backup(self, compress: bool = True) -> Optional[Path]:
        """
        Create a full database backup using pg_dump

        Args:
            compress: Whether to compress the backup with gzip

        Returns:
            Path to the backup file, or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supoclip_full_{timestamp}.sql"
        if compress:
            filename += ".gz"

        backup_path = self.backup_dir / filename

        try:
            logger.info(f"Starting full database backup to {backup_path}")

            # Build pg_dump command
            cmd = [
                "pg_dump",
                "--verbose",
                "--no-owner",
                "--no-acl",
                "--format=plain",
                self.config.get_pg_connection_string()
            ]

            # Run pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"pg_dump failed: {stderr.decode()}")
                return None

            # Write output (optionally compressed)
            if compress:
                with gzip.open(backup_path, 'wb') as f:
                    f.write(stdout)
            else:
                backup_path.write_bytes(stdout)

            # Create metadata file
            await self._create_metadata(backup_path, "full", compress)

            logger.info(f"Full backup completed: {backup_path} ({backup_path.stat().st_size / 1024 / 1024:.2f} MB)")

            # Upload to remote storage
            remote_path = f"database/{filename}"
            await self.storage.upload_file(backup_path, remote_path)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create full backup: {e}")
            return None

    async def create_schema_backup(self) -> Optional[Path]:
        """
        Create a schema-only backup (no data)

        Useful for quick disaster recovery planning and version control
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supoclip_schema_{timestamp}.sql"
        backup_path = self.backup_dir / filename

        try:
            logger.info(f"Starting schema-only backup to {backup_path}")

            cmd = [
                "pg_dump",
                "--schema-only",
                "--no-owner",
                "--no-acl",
                self.config.get_pg_connection_string()
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Schema backup failed: {stderr.decode()}")
                return None

            backup_path.write_bytes(stdout)

            await self._create_metadata(backup_path, "schema", False)

            logger.info(f"Schema backup completed: {backup_path}")

            # Upload to remote storage
            remote_path = f"database/{filename}"
            await self.storage.upload_file(backup_path, remote_path)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create schema backup: {e}")
            return None

    async def create_incremental_backup(self) -> Optional[Path]:
        """
        Create an incremental backup using PostgreSQL WAL archiving

        This requires WAL archiving to be configured in PostgreSQL.
        For now, this creates a logical backup of recently modified data.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supoclip_incremental_{timestamp}.sql.gz"
        backup_path = self.backup_dir / filename

        try:
            logger.info(f"Starting incremental backup to {backup_path}")

            # Get the last full backup timestamp
            last_full = await self._get_last_full_backup_time()

            if not last_full:
                logger.warning("No previous full backup found. Creating full backup instead.")
                return await self.create_full_backup()

            # For SupoClip, we'll backup tables with updated_at timestamps
            # This is a simplified incremental backup approach
            tables_with_timestamps = ["tasks", "generated_clips", "sources"]

            sql_parts = []

            for table in tables_with_timestamps:
                # Build query to export recent changes
                query = f"""
                COPY (
                    SELECT * FROM {table}
                    WHERE updated_at >= '{last_full.isoformat()}'
                ) TO STDOUT WITH CSV HEADER;
                """
                sql_parts.append(f"-- Table: {table}\n{query}\n")

            combined_sql = "\n".join(sql_parts)

            # Execute backup
            cmd = [
                "psql",
                self.config.get_pg_connection_string(),
                "-c", combined_sql
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Incremental backup failed: {stderr.decode()}")
                return None

            # Compress and save
            with gzip.open(backup_path, 'wb') as f:
                f.write(stdout)

            await self._create_metadata(backup_path, "incremental", True)

            logger.info(f"Incremental backup completed: {backup_path}")

            # Upload to remote storage
            remote_path = f"database/{filename}"
            await self.storage.upload_file(backup_path, remote_path)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create incremental backup: {e}")
            return None

    async def backup_table(self, table_name: str) -> Optional[Path]:
        """
        Backup a specific table

        Args:
            table_name: Name of the table to backup

        Returns:
            Path to the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supoclip_table_{table_name}_{timestamp}.sql.gz"
        backup_path = self.backup_dir / filename

        try:
            logger.info(f"Starting backup of table {table_name}")

            cmd = [
                "pg_dump",
                "--table", table_name,
                "--no-owner",
                "--no-acl",
                self.config.get_pg_connection_string()
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Table backup failed: {stderr.decode()}")
                return None

            # Compress and save
            with gzip.open(backup_path, 'wb') as f:
                f.write(stdout)

            await self._create_metadata(backup_path, f"table_{table_name}", True)

            logger.info(f"Table backup completed: {backup_path}")

            # Upload to remote storage
            remote_path = f"database/tables/{filename}"
            await self.storage.upload_file(backup_path, remote_path)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to backup table {table_name}: {e}")
            return None

    async def _create_metadata(self, backup_path: Path, backup_type: str, compressed: bool):
        """Create metadata file for the backup"""
        metadata = {
            "backup_file": backup_path.name,
            "backup_type": backup_type,
            "compressed": compressed,
            "timestamp": datetime.now().isoformat(),
            "database": self.config.pg_database,
            "host": self.config.pg_host,
            "size_bytes": backup_path.stat().st_size,
        }

        metadata_path = backup_path.with_suffix(backup_path.suffix + ".meta.json")
        metadata_path.write_text(json.dumps(metadata, indent=2))

        # Upload metadata too
        remote_meta_path = f"database/{metadata_path.name}"
        await self.storage.upload_file(metadata_path, remote_meta_path)

    async def _get_last_full_backup_time(self) -> Optional[datetime]:
        """Get the timestamp of the last full backup"""
        try:
            # List all metadata files
            metadata_files = list(self.backup_dir.glob("supoclip_full_*.meta.json"))

            if not metadata_files:
                return None

            # Find the most recent
            latest = max(metadata_files, key=lambda p: p.stat().st_mtime)

            metadata = json.loads(latest.read_text())
            return datetime.fromisoformat(metadata["timestamp"])

        except Exception as e:
            logger.error(f"Failed to get last backup time: {e}")
            return None

    async def list_backups(self, backup_type: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        List all available backups

        Args:
            backup_type: Filter by backup type (full, incremental, schema, etc.)

        Returns:
            List of backup metadata dictionaries
        """
        try:
            backups = []

            # Check local backups
            for meta_file in self.backup_dir.glob("*.meta.json"):
                try:
                    metadata = json.loads(meta_file.read_text())
                    if backup_type is None or metadata["backup_type"] == backup_type:
                        backups.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to read metadata from {meta_file}: {e}")

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    async def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)

            logger.info(f"Cleaning up backups older than {cutoff_date}")

            backups = await self.list_backups()
            deleted_count = 0

            for backup in backups:
                backup_date = datetime.fromisoformat(backup["timestamp"])

                if backup_date < cutoff_date:
                    # Delete local file
                    backup_file = self.backup_dir / backup["backup_file"]
                    if backup_file.exists():
                        backup_file.unlink()
                        logger.info(f"Deleted old backup: {backup_file}")

                    # Delete metadata file
                    meta_file = backup_file.with_suffix(backup_file.suffix + ".meta.json")
                    if meta_file.exists():
                        meta_file.unlink()

                    # Delete from remote storage
                    await self.storage.delete_file(f"database/{backup['backup_file']}")
                    await self.storage.delete_file(f"database/{meta_file.name}")

                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old backups")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

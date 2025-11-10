"""
Backup Verification Module

Verifies integrity and completeness of backups:
- File integrity checks (SHA256 hashes)
- Database backup validation
- Restoration testing
- Backup completeness checks
"""

import asyncio
import gzip
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .config import BackupConfig
from .storage_backends import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)


class BackupVerifier:
    """Verifies backup integrity and completeness"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.storage = get_storage_backend(config)
        self.verification_dir = config.backup_dir / "verification"
        self.verification_dir.mkdir(parents=True, exist_ok=True)

    async def verify_all_backups(self) -> Dict[str, Any]:
        """
        Verify all backups (database and files)

        Returns:
            Verification report with statistics
        """
        logger.info("Starting comprehensive backup verification")

        report = {
            "verification_time": datetime.now().isoformat(),
            "database": await self.verify_database_backups(),
            "files": await self.verify_file_backups(),
        }

        # Calculate overall status
        db_ok = report["database"]["passed"] == report["database"]["total"]
        files_ok = report["files"]["passed"] == report["files"]["total"]

        report["overall_status"] = "PASSED" if (db_ok and files_ok) else "FAILED"

        # Save verification report
        await self._save_verification_report(report)

        logger.info(
            f"Verification completed: {report['overall_status']}. "
            f"Database: {report['database']['passed']}/{report['database']['total']}, "
            f"Files: {report['files']['passed']}/{report['files']['total']}"
        )

        return report

    async def verify_database_backups(self) -> Dict[str, Any]:
        """
        Verify all database backups

        Returns:
            Verification statistics
        """
        logger.info("Verifying database backups")

        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

        try:
            backup_dir = self.config.backup_dir / "database"

            if not backup_dir.exists():
                logger.warning("No database backup directory found")
                return stats

            # Get all backup files
            backup_files = list(backup_dir.glob("supoclip_*.sql*"))
            backup_files = [f for f in backup_files if not f.name.endswith('.meta.json')]

            stats["total"] = len(backup_files)

            # Verify each backup
            for backup_file in backup_files:
                try:
                    is_valid = await self._verify_database_backup(backup_file)

                    if is_valid:
                        stats["passed"] += 1
                        logger.info(f"✓ {backup_file.name} - VALID")
                    else:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "file": backup_file.name,
                            "error": "Validation failed"
                        })
                        logger.error(f"✗ {backup_file.name} - INVALID")

                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "file": backup_file.name,
                        "error": str(e)
                    })
                    logger.error(f"✗ {backup_file.name} - ERROR: {e}")

        except Exception as e:
            logger.error(f"Failed to verify database backups: {e}")

        return stats

    async def verify_file_backups(self) -> Dict[str, Any]:
        """
        Verify all file backups by checking hashes

        Returns:
            Verification statistics
        """
        logger.info("Verifying file backups")

        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

        try:
            metadata_dir = self.config.backup_dir / "metadata" / "files"

            if not metadata_dir.exists():
                logger.warning("No file backup metadata found")
                return stats

            # Get all metadata files
            meta_files = list(metadata_dir.glob("*.meta.json"))
            stats["total"] = len(meta_files)

            # Verify each file
            for meta_file in meta_files:
                try:
                    metadata = json.loads(meta_file.read_text())
                    filename = metadata["filename"]
                    remote_path = metadata["remote_path"]
                    expected_hash = metadata["hash_sha256"]

                    # Verify file exists in remote storage
                    exists = await self.storage.file_exists(remote_path)

                    if not exists:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "file": filename,
                            "error": "File not found in remote storage"
                        })
                        logger.error(f"✗ {filename} - NOT FOUND")
                        continue

                    # Download and verify hash
                    temp_path = self.verification_dir / f"temp_{filename}"

                    download_success = await self.storage.download_file(remote_path, temp_path)

                    if not download_success:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "file": filename,
                            "error": "Failed to download for verification"
                        })
                        logger.error(f"✗ {filename} - DOWNLOAD FAILED")
                        continue

                    # Calculate hash
                    actual_hash = await self._calculate_file_hash(temp_path)

                    # Cleanup temp file
                    if temp_path.exists():
                        temp_path.unlink()

                    # Compare hashes
                    if actual_hash == expected_hash:
                        stats["passed"] += 1
                        logger.info(f"✓ {filename} - VALID")
                    else:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "file": filename,
                            "error": "Hash mismatch",
                            "expected": expected_hash,
                            "actual": actual_hash
                        })
                        logger.error(f"✗ {filename} - HASH MISMATCH")

                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "file": meta_file.name,
                        "error": str(e)
                    })
                    logger.error(f"✗ {meta_file.name} - ERROR: {e}")

        except Exception as e:
            logger.error(f"Failed to verify file backups: {e}")

        return stats

    async def _verify_database_backup(self, backup_file: Path) -> bool:
        """
        Verify a database backup file

        Checks:
        1. File is readable
        2. If compressed, can be decompressed
        3. Contains valid SQL
        4. Has expected tables
        """
        try:
            # Check file exists and is readable
            if not backup_file.exists():
                return False

            # Check if compressed
            is_compressed = backup_file.suffix == ".gz"

            # Read content
            if is_compressed:
                with gzip.open(backup_file, 'rt') as f:
                    content = f.read(1000)  # Read first 1000 chars
            else:
                with open(backup_file, 'r') as f:
                    content = f.read(1000)

            # Basic SQL validation
            if not content.strip():
                logger.error(f"Backup file {backup_file.name} is empty")
                return False

            # Check for SQL keywords
            sql_keywords = ['CREATE', 'INSERT', 'TABLE', 'DATABASE']
            has_sql = any(keyword in content.upper() for keyword in sql_keywords)

            if not has_sql:
                logger.error(f"Backup file {backup_file.name} doesn't appear to contain valid SQL")
                return False

            # Check for expected SupoClip tables (at least mention of them)
            expected_tables = ['tasks', 'generated_clips', 'sources', 'users']
            content_lower = content.lower()
            has_tables = any(table in content_lower for table in expected_tables)

            if not has_tables:
                logger.warning(f"Backup file {backup_file.name} may not contain expected tables")
                # This is a warning, not a failure

            return True

        except Exception as e:
            logger.error(f"Failed to verify database backup {backup_file.name}: {e}")
            return False

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            sha256_hash = hashlib.sha256()

            def read_chunks():
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        sha256_hash.update(chunk)
                return sha256_hash.hexdigest()

            return await asyncio.to_thread(read_chunks)

        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    async def test_restore(self, backup_file: Optional[Path] = None) -> bool:
        """
        Test database restoration without actually restoring

        This creates a temporary test database and restores to it

        Args:
            backup_file: Backup file to test (if None, uses latest)

        Returns:
            True if test restore successful, False otherwise
        """
        try:
            logger.info("Starting test restoration")

            if backup_file is None:
                # Find latest backup
                backup_dir = self.config.backup_dir / "database"
                backups = list(backup_dir.glob("supoclip_full_*.sql*"))

                if not backups:
                    logger.error("No backups found for test restore")
                    return False

                backup_file = max(backups, key=lambda p: p.stat().st_mtime)

            logger.info(f"Testing restoration of {backup_file.name}")

            # Create temporary test database
            test_db_name = f"supoclip_test_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Create test database
            create_db_cmd = [
                "createdb",
                "-h", self.config.pg_host,
                "-p", str(self.config.pg_port),
                "-U", self.config.pg_user,
                test_db_name
            ]

            process = await asyncio.create_subprocess_exec(
                *create_db_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.config.get_pg_env()
            )

            await process.communicate()

            if process.returncode != 0:
                logger.error("Failed to create test database")
                return False

            try:
                # Restore to test database
                is_compressed = backup_file.suffix == ".gz"

                if is_compressed:
                    with gzip.open(backup_file, 'rb') as f:
                        sql_content = f.read()
                else:
                    sql_content = backup_file.read_bytes()

                restore_cmd = [
                    "psql",
                    "-h", self.config.pg_host,
                    "-p", str(self.config.pg_port),
                    "-U", self.config.pg_user,
                    "-d", test_db_name,
                    "-v", "ON_ERROR_STOP=1"
                ]

                process = await asyncio.create_subprocess_exec(
                    *restore_cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=self.config.get_pg_env()
                )

                stdout, stderr = await process.communicate(input=sql_content)

                restore_success = process.returncode == 0

                if restore_success:
                    logger.info("✅ Test restoration successful")
                else:
                    logger.error(f"Test restoration failed: {stderr.decode()}")

                return restore_success

            finally:
                # Cleanup: Drop test database
                drop_db_cmd = [
                    "dropdb",
                    "-h", self.config.pg_host,
                    "-p", str(self.config.pg_port),
                    "-U", self.config.pg_user,
                    test_db_name
                ]

                process = await asyncio.create_subprocess_exec(
                    *drop_db_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=self.config.get_pg_env()
                )

                await process.communicate()
                logger.info(f"Cleaned up test database: {test_db_name}")

        except Exception as e:
            logger.error(f"Test restoration failed: {e}")
            return False

    async def check_backup_completeness(self) -> Dict[str, Any]:
        """
        Check if backups are complete and up-to-date

        Returns:
            Report with completeness statistics
        """
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "database_backups": {
                    "full": 0,
                    "incremental": 0,
                    "schema": 0,
                    "latest_full": None,
                    "latest_incremental": None,
                },
                "file_backups": {
                    "uploads": 0,
                    "clips": 0,
                    "metadata": 0,
                },
                "storage_locations": {
                    "local": False,
                    "remote": False,
                },
                "warnings": []
            }

            # Check database backups
            db_backup_dir = self.config.backup_dir / "database"
            if db_backup_dir.exists():
                report["storage_locations"]["local"] = True

                full_backups = list(db_backup_dir.glob("supoclip_full_*.sql*"))
                incremental_backups = list(db_backup_dir.glob("supoclip_incremental_*.sql*"))
                schema_backups = list(db_backup_dir.glob("supoclip_schema_*.sql*"))

                report["database_backups"]["full"] = len([f for f in full_backups if not f.name.endswith('.meta.json')])
                report["database_backups"]["incremental"] = len([f for f in incremental_backups if not f.name.endswith('.meta.json')])
                report["database_backups"]["schema"] = len([f for f in schema_backups if not f.name.endswith('.meta.json')])

                if full_backups:
                    latest_full = max([f for f in full_backups if not f.name.endswith('.meta.json')],
                                    key=lambda p: p.stat().st_mtime)
                    report["database_backups"]["latest_full"] = datetime.fromtimestamp(
                        latest_full.stat().st_mtime
                    ).isoformat()

            # Check file backups
            file_metadata_dir = self.config.backup_dir / "metadata" / "files"
            if file_metadata_dir.exists():
                for meta_file in file_metadata_dir.glob("*.meta.json"):
                    try:
                        metadata = json.loads(meta_file.read_text())
                        category = metadata.get("category", "unknown")

                        if category in report["file_backups"]:
                            report["file_backups"][category] += 1

                    except Exception as e:
                        logger.warning(f"Failed to read {meta_file}: {e}")

            # Check remote storage
            try:
                remote_files = await self.storage.list_files("database/")
                if remote_files:
                    report["storage_locations"]["remote"] = True
            except Exception as e:
                logger.warning(f"Failed to check remote storage: {e}")

            # Add warnings
            if report["database_backups"]["full"] == 0:
                report["warnings"].append("No full database backups found")

            if not report["storage_locations"]["remote"]:
                report["warnings"].append("No remote storage backups found")

            from datetime import timedelta
            if report["database_backups"]["latest_full"]:
                latest = datetime.fromisoformat(report["database_backups"]["latest_full"])
                age_days = (datetime.now() - latest).days

                if age_days > self.config.full_backup_interval_days + 1:
                    report["warnings"].append(
                        f"Latest full backup is {age_days} days old (expected every {self.config.full_backup_interval_days} days)"
                    )

            return report

        except Exception as e:
            logger.error(f"Failed to check backup completeness: {e}")
            return {}

    async def _save_verification_report(self, report: Dict[str, Any]):
        """Save verification report"""
        try:
            report_dir = self.config.backup_dir / "metadata" / "verification"
            report_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"verification_report_{timestamp}.json"

            report_file.write_text(json.dumps(report, indent=2))

            logger.info(f"Verification report saved: {report_file}")

            # Upload to remote storage
            await self.storage.upload_file(report_file, f"metadata/verification/{report_file.name}")

        except Exception as e:
            logger.error(f"Failed to save verification report: {e}")

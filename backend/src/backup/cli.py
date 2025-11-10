"""
Backup CLI Tool

Command-line interface for managing backups manually.

Usage:
    python -m src.backup.cli backup db --full
    python -m src.backup.cli backup files
    python -m src.backup.cli restore db --latest
    python -m src.backup.cli verify
    python -m src.backup.cli list
"""

import asyncio
import sys
from pathlib import Path
import argparse
import logging

from .config import BackupConfig
from .database_backup import DatabaseBackup
from .file_backup import FileBackup
from .restore import RestoreManager
from .verify import BackupVerifier
from .scheduler import BackupScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupCLI:
    """Command-line interface for backup operations"""

    def __init__(self):
        self.config = BackupConfig()
        self.db_backup = DatabaseBackup(self.config)
        self.file_backup = FileBackup(self.config)
        self.restore = RestoreManager(self.config)
        self.verifier = BackupVerifier(self.config)
        self.scheduler = BackupScheduler(self.config)

    async def backup_database(self, backup_type: str = "full"):
        """Backup database"""
        print(f"Starting {backup_type} database backup...")

        if backup_type == "full":
            backup_file = await self.db_backup.create_full_backup(compress=True)
        elif backup_type == "incremental":
            backup_file = await self.db_backup.create_incremental_backup()
        elif backup_type == "schema":
            backup_file = await self.db_backup.create_schema_backup()
        else:
            print(f"Unknown backup type: {backup_type}")
            return

        if backup_file:
            print(f"✅ Backup completed: {backup_file}")
            print(f"   Size: {backup_file.stat().st_size / 1024 / 1024:.2f} MB")
        else:
            print("❌ Backup failed")

    async def backup_files(self):
        """Backup all files"""
        print("Starting file backup...")

        stats = await self.file_backup.backup_all_files()

        print(f"\n✅ File backup completed:")
        print(f"   Uploads: {stats['uploads']['count']} files ({stats['uploads']['size_bytes'] / 1024 / 1024:.2f} MB)")
        print(f"   Clips: {stats['clips']['count']} files ({stats['clips']['size_bytes'] / 1024 / 1024:.2f} MB)")
        print(f"   Metadata: {stats['metadata']['count']} files ({stats['metadata']['size_bytes'] / 1024 / 1024:.2f} MB)")

        if stats['uploads']['failed'] or stats['clips']['failed']:
            print(f"\n⚠️  Failed files:")
            for failed in stats['uploads']['failed'] + stats['clips']['failed']:
                print(f"   - {failed}")

    async def restore_database(self, latest: bool = False, backup_file: str = None):
        """Restore database from backup"""
        print("⚠️  WARNING: This will overwrite the current database!")
        response = input("Are you sure you want to continue? (yes/no): ")

        if response.lower() != "yes":
            print("Restore cancelled")
            return

        if latest or backup_file is None:
            print("Restoring from latest backup...")
            success = await self.restore.restore_database_full()
        else:
            print(f"Restoring from {backup_file}...")
            success = await self.restore.restore_database_full(Path(backup_file))

        if success:
            print("✅ Database restored successfully")
        else:
            print("❌ Database restore failed")

    async def restore_files(self, category: str = None):
        """Restore files from backup"""
        print(f"Starting file restoration (category: {category or 'all'})...")

        stats = await self.restore.restore_all_files(category)

        print(f"\n✅ File restoration completed:")
        print(f"   Restored: {stats['restored']} files")
        print(f"   Failed: {stats['failed']} files")
        print(f"   Total size: {stats['total_bytes'] / 1024 / 1024:.2f} MB")

    async def verify_backups(self):
        """Verify all backups"""
        print("Starting backup verification...\n")

        report = await self.verifier.verify_all_backups()

        print(f"Overall Status: {report['overall_status']}\n")
        print(f"Database Backups:")
        print(f"   Total: {report['database']['total']}")
        print(f"   Passed: {report['database']['passed']}")
        print(f"   Failed: {report['database']['failed']}")

        print(f"\nFile Backups:")
        print(f"   Total: {report['files']['total']}")
        print(f"   Passed: {report['files']['passed']}")
        print(f"   Failed: {report['files']['failed']}")

        if report['database']['errors']:
            print(f"\nDatabase Errors:")
            for error in report['database']['errors']:
                print(f"   - {error['file']}: {error['error']}")

        if report['files']['errors']:
            print(f"\nFile Errors:")
            for error in report['files']['errors'][:10]:  # Show first 10
                print(f"   - {error['file']}: {error['error']}")

            if len(report['files']['errors']) > 10:
                print(f"   ... and {len(report['files']['errors']) - 10} more")

    async def list_backups(self, backup_type: str = None):
        """List all available backups"""
        print("Available Backups:\n")

        # Database backups
        db_backups = await self.db_backup.list_backups(backup_type)

        if db_backups:
            print("Database Backups:")
            for backup in db_backups[:10]:  # Show latest 10
                print(f"   [{backup['backup_type']}] {backup['backup_file']}")
                print(f"      Date: {backup['timestamp']}")
                print(f"      Size: {backup['size_bytes'] / 1024 / 1024:.2f} MB")
                print()

            if len(db_backups) > 10:
                print(f"   ... and {len(db_backups) - 10} more")
        else:
            print("   No database backups found")

        print("\nFile Backups:")

        # File backups
        file_backups = await self.file_backup.list_backed_up_files()

        if file_backups:
            # Group by category
            by_category = {}
            for backup in file_backups:
                category = backup.get("category", "unknown")
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(backup)

            for category, backups in by_category.items():
                print(f"   {category.upper()}: {len(backups)} files")

            print(f"\n   Total: {len(file_backups)} files")
        else:
            print("   No file backups found")

    async def check_completeness(self):
        """Check backup completeness"""
        print("Checking backup completeness...\n")

        report = await self.verifier.check_backup_completeness()

        print("Database Backups:")
        print(f"   Full: {report['database_backups']['full']}")
        print(f"   Incremental: {report['database_backups']['incremental']}")
        print(f"   Schema: {report['database_backups']['schema']}")

        if report['database_backups']['latest_full']:
            print(f"   Latest Full: {report['database_backups']['latest_full']}")

        print("\nFile Backups:")
        print(f"   Uploads: {report['file_backups']['uploads']}")
        print(f"   Clips: {report['file_backups']['clips']}")
        print(f"   Metadata: {report['file_backups']['metadata']}")

        print("\nStorage Locations:")
        print(f"   Local: {'✓' if report['storage_locations']['local'] else '✗'}")
        print(f"   Remote: {'✓' if report['storage_locations']['remote'] else '✗'}")

        if report['warnings']:
            print("\n⚠️  Warnings:")
            for warning in report['warnings']:
                print(f"   - {warning}")

    async def cleanup(self):
        """Cleanup old backups"""
        print(f"Cleaning up backups older than {self.config.retention_days} days...")

        # Cleanup database backups
        await self.db_backup.cleanup_old_backups()

        # Cleanup file backups
        await self.file_backup.cleanup_old_files()

        print("✅ Cleanup completed")

    def show_config(self):
        """Show current configuration"""
        print("Backup Configuration:\n")
        print(f"Database: {self.config.pg_database}@{self.config.pg_host}:{self.config.pg_port}")
        print(f"Backup Directory: {self.config.backup_dir}")
        print(f"Storage Backend: {self.config.storage_backend}")

        if self.config.storage_backend != "local":
            print(f"S3 Bucket: {self.config.s3_bucket}")
            print(f"S3 Region: {self.config.s3_region}")

        print(f"\nRetention: {self.config.retention_days} days")
        print(f"Compression: {'Enabled' if self.config.compression else 'Disabled'}")
        print(f"Incremental Backups: {'Enabled' if self.config.enable_incremental else 'Disabled'}")
        print(f"Full Backup Interval: {self.config.full_backup_interval_days} days")
        print(f"\nDaily Backup Time: {self.config.daily_backup_time}")
        print(f"Weekly Backup Day: {self.config.weekly_backup_day}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="SupoClip Backup Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create backups")
    backup_parser.add_argument("type", choices=["db", "files", "all"], help="What to backup")
    backup_parser.add_argument("--full", action="store_true", help="Full database backup")
    backup_parser.add_argument("--incremental", action="store_true", help="Incremental database backup")
    backup_parser.add_argument("--schema", action="store_true", help="Schema-only backup")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backups")
    restore_parser.add_argument("type", choices=["db", "files", "all"], help="What to restore")
    restore_parser.add_argument("--latest", action="store_true", help="Use latest backup")
    restore_parser.add_argument("--file", type=str, help="Specific backup file to restore")
    restore_parser.add_argument("--category", choices=["uploads", "clips", "metadata"], help="File category to restore")

    # Verify command
    subparsers.add_parser("verify", help="Verify backup integrity")

    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--type", choices=["full", "incremental", "schema"], help="Filter by type")

    # Completeness command
    subparsers.add_parser("completeness", help="Check backup completeness")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Remove old backups")

    # Config command
    subparsers.add_parser("config", help="Show configuration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = BackupCLI()

    try:
        if args.command == "backup":
            if args.type == "db":
                if args.schema:
                    await cli.backup_database("schema")
                elif args.incremental:
                    await cli.backup_database("incremental")
                else:
                    await cli.backup_database("full")
            elif args.type == "files":
                await cli.backup_files()
            elif args.type == "all":
                await cli.backup_database("full")
                await cli.backup_files()

        elif args.command == "restore":
            if args.type == "db":
                await cli.restore_database(latest=args.latest, backup_file=args.file)
            elif args.type == "files":
                await cli.restore_files(category=args.category)
            elif args.type == "all":
                await cli.restore_database(latest=True)
                await cli.restore_files()

        elif args.command == "verify":
            await cli.verify_backups()

        elif args.command == "list":
            await cli.list_backups(backup_type=args.type if hasattr(args, 'type') else None)

        elif args.command == "completeness":
            await cli.check_completeness()

        elif args.command == "cleanup":
            await cli.cleanup()

        elif args.command == "config":
            cli.show_config()

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

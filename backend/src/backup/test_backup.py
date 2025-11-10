"""
Simple test script for the backup system

Run this to verify your backup configuration is working:
    python -m src.backup.test_backup
"""

import asyncio
import sys
from pathlib import Path

try:
    from .config import BackupConfig
    from .database_backup import DatabaseBackup
    from .file_backup import FileBackup
    from .verify import BackupVerifier
    from .storage_backends import get_storage_backend
except ImportError:
    print("❌ Failed to import backup modules")
    print("Make sure you're running from the backend directory")
    sys.exit(1)


async def test_configuration():
    """Test backup configuration"""
    print("\n" + "="*60)
    print("Testing Backup Configuration")
    print("="*60 + "\n")

    try:
        config = BackupConfig()

        print(f"✓ Configuration loaded successfully")
        print(f"  Database: {config.pg_database}@{config.pg_host}:{config.pg_port}")
        print(f"  Backup directory: {config.backup_dir}")
        print(f"  Storage backend: {config.storage_backend}")
        print(f"  Retention: {config.retention_days} days")
        print(f"  Compression: {'Enabled' if config.compression else 'Disabled'}")
        print(f"  Incremental: {'Enabled' if config.enable_incremental else 'Disabled'}")

        # Check if backup directory exists and is writable
        if config.backup_dir.exists():
            print(f"✓ Backup directory exists and is accessible")
        else:
            print(f"⚠ Backup directory will be created: {config.backup_dir}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_storage_backend():
    """Test storage backend connection"""
    print("\n" + "="*60)
    print("Testing Storage Backend")
    print("="*60 + "\n")

    try:
        config = BackupConfig()
        storage = get_storage_backend(config)

        print(f"✓ Storage backend initialized: {config.storage_backend}")

        # Test file operations
        test_file = config.backup_dir / "test_file.txt"
        test_file.write_text("Test content")

        # Test upload
        success = await storage.upload_file(test_file, "test/test_file.txt")

        if success:
            print(f"✓ Upload test successful")
        else:
            print(f"❌ Upload test failed")
            return False

        # Test file exists
        exists = await storage.file_exists("test/test_file.txt")

        if exists:
            print(f"✓ File exists check successful")
        else:
            print(f"❌ File exists check failed")
            return False

        # Test download
        download_path = config.backup_dir / "test_download.txt"
        success = await storage.download_file("test/test_file.txt", download_path)

        if success:
            print(f"✓ Download test successful")
        else:
            print(f"❌ Download test failed")
            return False

        # Cleanup
        test_file.unlink()
        if download_path.exists():
            download_path.unlink()
        await storage.delete_file("test/test_file.txt")

        print(f"✓ Storage backend test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Storage backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("Testing Database Connection")
    print("="*60 + "\n")

    try:
        config = BackupConfig()

        # Try to connect to database
        import asyncpg

        conn = await asyncpg.connect(
            host=config.pg_host,
            port=config.pg_port,
            user=config.pg_user,
            password=config.pg_password,
            database=config.pg_database
        )

        # Test query
        version = await conn.fetchval("SELECT version()")
        print(f"✓ Database connection successful")
        print(f"  PostgreSQL version: {version.split(',')[0]}")

        # Get table counts
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"✓ Found {len(tables)} tables")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            print(f"    {table['table_name']}: {count} rows")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        print(f"\nPlease check:")
        print(f"  1. PostgreSQL is running")
        print(f"  2. Database credentials in .env are correct")
        print(f"  3. Database '{config.pg_database}' exists")
        return False


async def test_database_backup():
    """Test database backup creation"""
    print("\n" + "="*60)
    print("Testing Database Backup")
    print("="*60 + "\n")

    try:
        config = BackupConfig()
        db_backup = DatabaseBackup(config)

        # Create schema backup (faster than full backup)
        print("Creating schema backup (test)...")
        backup_file = await db_backup.create_schema_backup()

        if backup_file:
            print(f"✓ Backup created successfully: {backup_file.name}")
            print(f"  Size: {backup_file.stat().st_size / 1024:.2f} KB")

            # List backups
            backups = await db_backup.list_backups("schema")
            print(f"✓ Found {len(backups)} schema backups")

            return True
        else:
            print(f"❌ Backup creation failed")
            return False

    except Exception as e:
        print(f"❌ Database backup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_file_backup():
    """Test file backup"""
    print("\n" + "="*60)
    print("Testing File Backup")
    print("="*60 + "\n")

    try:
        config = BackupConfig()
        file_backup = FileBackup(config)

        # Create test file
        test_dir = config.uploads_dir
        test_dir.mkdir(parents=True, exist_ok=True)

        test_file = test_dir / "test_video.txt"
        test_file.write_text("This is a test file")

        print(f"Created test file: {test_file}")

        # Backup the file
        success = await file_backup.backup_file(test_file, category="uploads")

        if success:
            print(f"✓ File backup successful")

            # List backed up files
            backups = await file_backup.list_backed_up_files(category="uploads")
            print(f"✓ Found {len(backups)} file backups")

            # Cleanup
            test_file.unlink()

            return True
        else:
            print(f"❌ File backup failed")
            return False

    except Exception as e:
        print(f"❌ File backup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_verification():
    """Test backup verification"""
    print("\n" + "="*60)
    print("Testing Backup Verification")
    print("="*60 + "\n")

    try:
        config = BackupConfig()
        verifier = BackupVerifier(config)

        # Check backup completeness
        report = await verifier.check_backup_completeness()

        print(f"✓ Completeness check completed")
        print(f"  Database backups:")
        print(f"    Full: {report['database_backups']['full']}")
        print(f"    Incremental: {report['database_backups']['incremental']}")
        print(f"    Schema: {report['database_backups']['schema']}")

        print(f"  Storage locations:")
        print(f"    Local: {'✓' if report['storage_locations']['local'] else '✗'}")
        print(f"    Remote: {'✓' if report['storage_locations']['remote'] else '✗'}")

        if report['warnings']:
            print(f"  ⚠ Warnings:")
            for warning in report['warnings']:
                print(f"    - {warning}")

        return True

    except Exception as e:
        print(f"❌ Verification test failed: {e}")
        return False


async def run_all_tests():
    """Run all backup system tests"""
    print("\n" + "="*70)
    print("  SupoClip Backup System Test Suite")
    print("="*70)

    tests = [
        ("Configuration", test_configuration),
        ("Storage Backend", test_storage_backend),
        ("Database Connection", test_database_connection),
        ("Database Backup", test_database_backup),
        ("File Backup", test_file_backup),
        ("Verification", test_verification),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Print summary
    print("\n" + "="*70)
    print("  Test Summary")
    print("="*70 + "\n")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name:.<50} {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Backup system is ready to use.")
        print("\nNext steps:")
        print("  1. Run 'python -m src.backup.cli backup db --full' to create first backup")
        print("  2. Run 'python -m src.backup.cli verify' to verify backups")
        print("  3. Integrate scheduler into your FastAPI app (see integration_example.py)")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Make sure PostgreSQL is running and accessible")
        print("  - Check database credentials in .env file")
        print("  - Verify S3/B2 credentials if using cloud storage")
        print("  - Ensure backup directory has write permissions")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

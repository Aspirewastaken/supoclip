#!/usr/bin/env python3
"""
Database migration runner for SupoClip

This script runs SQL migration files against the PostgreSQL database.
Run with: python run_migration.py <migration_file.sql>
"""

import asyncio
import sys
from pathlib import Path
import asyncpg
from src.config import Config

async def run_migration(migration_file: Path):
    """Run a SQL migration file"""
    config = Config()

    # Parse database URL
    # Expected format: postgresql://user:password@host:port/database
    db_url = config.database_url

    print(f"🚀 Starting migration: {migration_file.name}")
    print(f"📊 Database: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")

    try:
        # Read migration file
        print(f"📖 Reading migration file: {migration_file}")
        with open(migration_file, 'r') as f:
            sql = f.read()

        # Connect to database
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(db_url)

        try:
            # Execute migration
            print("⚡ Executing migration...")
            await conn.execute(sql)

            print("✅ Migration completed successfully!")

            # Verify tables were created
            print("\n📋 Verifying created tables...")
            tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('clip_views', 'clip_performance')
                ORDER BY tablename
            """)

            if tables:
                print(f"✅ Found {len(tables)} analytics tables:")
                for table in tables:
                    print(f"   - {table['tablename']}")

                    # Get row count
                    count_result = await conn.fetchrow(f"SELECT COUNT(*) as count FROM {table['tablename']}")
                    print(f"     Rows: {count_result['count']}")
            else:
                print("⚠️  Warning: No analytics tables found after migration")

        finally:
            await conn.close()
            print("\n🔒 Database connection closed")

    except FileNotFoundError:
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)
    except asyncpg.PostgresError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        print("\nExample:")
        print("  python run_migration.py migrations/001_add_analytics_tables.sql")
        sys.exit(1)

    migration_file = Path(sys.argv[1])

    if not migration_file.exists():
        # Try relative to script directory
        script_dir = Path(__file__).parent
        migration_file = script_dir / sys.argv[1]

    await run_migration(migration_file)


if __name__ == "__main__":
    asyncio.run(main())

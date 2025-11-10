#!/usr/bin/env python3
"""
Migration script to add CDN support to SupoClip.

Usage:
    python migrations/migrate_cdn.py

This script:
1. Adds cdn_url column to generated_clips table
2. Optionally backfills existing clips to CDN
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import AsyncSessionLocal
from src.storage.integrations import upload_clip_to_cdn
from sqlalchemy import text


async def add_cdn_column():
    """Add cdn_url column to generated_clips table"""
    print("📊 Adding cdn_url column to generated_clips table...")

    async with AsyncSessionLocal() as db:
        try:
            # Add column if it doesn't exist
            await db.execute(text("""
                ALTER TABLE generated_clips
                ADD COLUMN IF NOT EXISTS cdn_url VARCHAR(1000)
            """))

            # Add index for faster lookups
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_generated_clips_cdn_url
                ON generated_clips(cdn_url)
            """))

            await db.commit()
            print("✅ Successfully added cdn_url column and index")

            # Verify
            result = await db.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'generated_clips' AND column_name = 'cdn_url'
            """))
            column = result.fetchone()

            if column:
                print(f"✅ Verified: {column.column_name} ({column.data_type}({column.character_maximum_length}))")
            else:
                print("❌ Error: Column not found after migration")
                return False

            return True

        except Exception as e:
            print(f"❌ Error adding column: {e}")
            await db.rollback()
            return False


async def backfill_existing_clips(dry_run=True):
    """
    Backfill existing clips to CDN.

    Args:
        dry_run: If True, only simulate the upload without actually uploading
    """
    print("\n📊 Backfilling existing clips to CDN...")

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be uploaded")

    async with AsyncSessionLocal() as db:
        try:
            # Get all clips without CDN URLs
            result = await db.execute(text("""
                SELECT id, task_id, filename, file_path, created_at
                FROM generated_clips
                WHERE cdn_url IS NULL
                ORDER BY created_at DESC
            """))
            clips = result.fetchall()

            if not clips:
                print("✅ No clips need backfilling")
                return True

            print(f"📊 Found {len(clips)} clips to backfill")

            uploaded_count = 0
            failed_count = 0
            skipped_count = 0

            for i, clip in enumerate(clips, 1):
                print(f"\n[{i}/{len(clips)}] Processing: {clip.filename}")
                print(f"  Task ID: {clip.task_id}")
                print(f"  File: {clip.file_path}")

                # Check if file exists
                if not Path(clip.file_path).exists():
                    print(f"  ⚠️ Skipped - File not found")
                    skipped_count += 1
                    continue

                if dry_run:
                    print(f"  🔍 Would upload to CDN (dry run)")
                    uploaded_count += 1
                else:
                    # Upload to CDN
                    cdn_url = await upload_clip_to_cdn(
                        clip_path=clip.file_path,
                        filename=clip.filename,
                        task_id=clip.task_id
                    )

                    if cdn_url:
                        # Update database
                        await db.execute(
                            text("UPDATE generated_clips SET cdn_url = :cdn_url WHERE id = :id"),
                            {"cdn_url": cdn_url, "id": clip.id}
                        )
                        await db.commit()

                        print(f"  ✅ Uploaded: {cdn_url}")
                        uploaded_count += 1
                    else:
                        print(f"  ❌ Failed to upload")
                        failed_count += 1

            print(f"\n📊 Backfill Summary:")
            print(f"  ✅ Uploaded: {uploaded_count}")
            print(f"  ❌ Failed: {failed_count}")
            print(f"  ⚠️ Skipped: {skipped_count}")

            if dry_run:
                print("\n💡 To actually upload, run: python migrations/migrate_cdn.py --backfill")

            return True

        except Exception as e:
            print(f"❌ Error during backfill: {e}")
            await db.rollback()
            return False


async def check_cdn_config():
    """Check if CDN is properly configured"""
    print("🔍 Checking CDN configuration...")

    from src.storage.cdn import get_cdn_provider

    provider = get_cdn_provider()

    if provider and provider.is_enabled():
        print(f"✅ CDN enabled: {provider.__class__.__name__}")
        print(f"  Base URL: {provider.base_url}")
        return True
    else:
        print("⚠️ CDN not configured or disabled")
        print("  To enable CDN:")
        print("  1. Set CDN_ENABLED=true in .env")
        print("  2. Configure CDN provider (see .env.cdn.example)")
        print("  3. Install dependencies: uv add boto3 aiohttp")
        return False


async def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate SupoClip to support CDN')
    parser.add_argument('--backfill', action='store_true', help='Backfill existing clips to CDN (not dry run)')
    parser.add_argument('--skip-column', action='store_true', help='Skip adding column (if already added)')
    args = parser.parse_args()

    print("🚀 SupoClip CDN Migration")
    print("=" * 60)

    # Check CDN configuration first
    cdn_configured = await check_cdn_config()

    if not cdn_configured and args.backfill:
        print("\n❌ Cannot backfill clips without CDN configuration")
        print("Configure CDN first, then run migration again")
        return

    # Step 1: Add column
    if not args.skip_column:
        success = await add_cdn_column()
        if not success:
            print("\n❌ Migration failed at adding column")
            return
    else:
        print("⏭️ Skipped adding column (--skip-column)")

    # Step 2: Backfill (optional)
    if cdn_configured:
        print("\n" + "=" * 60)
        dry_run = not args.backfill
        await backfill_existing_clips(dry_run=dry_run)

    print("\n" + "=" * 60)
    print("✅ Migration complete!")

    if cdn_configured and not args.backfill:
        print("\n💡 Next steps:")
        print("  1. Review the dry run output above")
        print("  2. Run with --backfill to actually upload clips:")
        print("     python migrations/migrate_cdn.py --backfill")
    elif not cdn_configured:
        print("\n💡 Next steps:")
        print("  1. Configure CDN (see backend/CDN_SETUP_GUIDE.md)")
        print("  2. Set CDN_ENABLED=true in .env")
        print("  3. Run migration again to backfill clips")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Migration interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

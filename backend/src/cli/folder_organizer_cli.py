#!/usr/bin/env python3
"""
CLI tool for managing folder organization.

Usage:
    python -m src.cli.folder_organizer_cli stats
    python -m src.cli.folder_organizer_cli list
    python -m src.cli.folder_organizer_cli list --channel "my_channel"
    python -m src.cli.folder_organizer_cli cleanup --dry-run
    python -m src.cli.folder_organizer_cli cleanup --retention-days 30
    python -m src.cli.folder_organizer_cli organize-task TASK_ID --channel "my_channel"
"""
import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.folder_organizer import FolderOrganizer, organize_task_clips
from src.database import AsyncSessionLocal
from sqlalchemy import text


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def print_statistics(stats: dict):
    """Pretty print folder statistics."""
    print("\n" + "=" * 60)
    print("FOLDER ORGANIZATION STATISTICS")
    print("=" * 60)
    print(f"\nTotal Channels: {stats['total_channels']}")
    print(f"Total Folders:  {stats['total_folders']}")
    print(f"Total Clips:    {stats['total_clips']}")

    if stats['channels']:
        print("\n" + "-" * 60)
        print("CHANNELS:")
        print("-" * 60)

        # Sort channels by clip count
        sorted_channels = sorted(
            stats['channels'].items(),
            key=lambda x: x[1]['clips'],
            reverse=True
        )

        for channel_name, channel_data in sorted_channels:
            print(f"\n{channel_name}")
            print(f"  Folders: {channel_data['folders']}")
            print(f"  Clips:   {channel_data['clips']}")
            print(f"  Dates:   {', '.join(sorted(channel_data['dates'], reverse=True)[:5])}")
            if len(channel_data['dates']) > 5:
                print(f"           ... and {len(channel_data['dates']) - 5} more")

    print("\n" + "=" * 60 + "\n")


def print_folders(folders: list):
    """Pretty print folder list."""
    print("\n" + "=" * 60)
    print("ORGANIZED FOLDERS")
    print("=" * 60)

    if not folders:
        print("\nNo folders found.")
        print("\n" + "=" * 60 + "\n")
        return

    print(f"\nTotal: {len(folders)} folders\n")
    print("-" * 60)

    for folder in folders:
        print(f"\nChannel: {folder['channel']}")
        print(f"Date:    {folder['date']}")
        print(f"Clips:   {folder['clip_count']}")
        print(f"Path:    {folder['path']}")
        if folder['has_manifest']:
            print(f"Manifest: ✓")
        else:
            print(f"Manifest: ✗")

    print("\n" + "=" * 60 + "\n")


def print_cleanup_results(result: dict):
    """Pretty print cleanup results."""
    print("\n" + "=" * 60)
    if result['dry_run']:
        print("CLEANUP DRY RUN (Simulation Only)")
    else:
        print("CLEANUP RESULTS")
    print("=" * 60)

    print(f"\nRetention Period: {result['retention_days']} days")
    print(f"Cutoff Date:      {result['cutoff_date']}")
    print(f"\nDeleted:  {result['deleted_count']} folders")
    print(f"Kept:     {result['kept_count']} folders")
    print(f"Errors:   {result['error_count']}")

    if result['deleted_folders']:
        print("\n" + "-" * 60)
        print("DELETED FOLDERS:")
        print("-" * 60)

        for folder in result['deleted_folders']:
            print(f"\n{folder['channel']}/{folder['date']}")
            print(f"  Age:  {folder['age_days']} days")
            print(f"  Path: {folder['path']}")

    if result['errors']:
        print("\n" + "-" * 60)
        print("ERRORS:")
        print("-" * 60)

        for error in result['errors']:
            print(f"\n{error['path']}")
            print(f"  Error: {error['error']}")

    print("\n" + "=" * 60 + "\n")


async def cmd_stats(args):
    """Show folder statistics."""
    organizer = FolderOrganizer()
    stats = organizer.get_folder_statistics()
    print_statistics(stats)


async def cmd_list(args):
    """List organized folders."""
    organizer = FolderOrganizer()
    folders = organizer.list_folders(
        channel_name=args.channel,
        date_from=args.from_date,
        date_to=args.to_date
    )

    # Limit results
    if args.limit:
        folders = folders[:args.limit]

    print_folders(folders)


async def cmd_cleanup(args):
    """Cleanup old folders."""
    organizer = FolderOrganizer(retention_days=args.retention_days)
    result = organizer.cleanup_old_folders(dry_run=args.dry_run)
    print_cleanup_results(result)


async def cmd_organize_task(args):
    """Organize clips from an existing task."""
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
            task_result = await db.execute(task_query, {"task_id": args.task_id})
            task_row = task_result.fetchone()

            if not task_row:
                print(f"Error: Task not found: {args.task_id}")
                sys.exit(1)

            # Get clips for task
            clips_query = text("""
                SELECT id, filename, file_path
                FROM generated_clips
                WHERE task_id = :task_id
                ORDER BY clip_order
            """)
            clips_result = await db.execute(clips_query, {"task_id": args.task_id})
            clips_rows = clips_result.fetchall()

            if not clips_rows:
                print(f"Error: No clips found for task: {args.task_id}")
                sys.exit(1)

        print(f"\nTask: {task_row.title}")
        print(f"Clips: {len(clips_rows)}")

        # Prepare clip file paths
        clip_files = [row.file_path for row in clips_rows]

        # Determine channel name
        channel_name = args.channel or task_row.channel_name or "unknown_channel"
        print(f"Channel: {channel_name}")

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
            'task_id': args.task_id,
            'user_id': task_row.user_id,
            'title': task_row.title,
            'clip_count': len(clip_files)
        }

        # Organize clips
        print("\nOrganizing clips...")
        result = organize_task_clips(
            task_id=args.task_id,
            clip_files=clip_files,
            channel_name=channel_name,
            video_metadata=video_metadata,
            task_metadata=task_metadata
        )

        print("\n" + "=" * 60)
        print("ORGANIZATION RESULTS")
        print("=" * 60)
        print(f"\nChannel:   {result['channel_name']}")
        print(f"Date:      {result['date']}")
        print(f"Folder:    {result['folder']}")
        print(f"Organized: {result['organized_count']} clips")
        print(f"Failed:    {result['failed_count']} clips")
        print(f"Manifest:  {result['manifest_path']}")

        if result['failed_clips']:
            print("\n" + "-" * 60)
            print("FAILED CLIPS:")
            print("-" * 60)
            for failed in result['failed_clips']:
                print(f"\n{failed['clip'].get('file_path', 'unknown')}")
                print(f"  Error: {failed['error']}")

        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


async def cmd_channels(args):
    """List all channels."""
    organizer = FolderOrganizer()
    stats = organizer.get_folder_statistics()

    print("\n" + "=" * 60)
    print("CHANNELS")
    print("=" * 60)

    if not stats['channels']:
        print("\nNo channels found.")
        print("\n" + "=" * 60 + "\n")
        return

    # Sort channels by clip count
    sorted_channels = sorted(
        stats['channels'].items(),
        key=lambda x: x[1]['clips'],
        reverse=True
    )

    print(f"\nTotal: {len(sorted_channels)} channels\n")
    print("-" * 60)

    for channel_name, channel_data in sorted_channels:
        print(f"\n{channel_name}")
        print(f"  Folders:    {channel_data['folders']}")
        print(f"  Clips:      {channel_data['clips']}")
        print(f"  Date Range: {min(channel_data['dates'])} to {max(channel_data['dates'])}")

    print("\n" + "=" * 60 + "\n")


async def cmd_manifest(args):
    """Show manifest for a folder."""
    organizer = FolderOrganizer()

    from datetime import datetime
    folder_date = datetime.strptime(args.date, "%Y-%m-%d")

    folder_path = organizer.get_dated_folder_path(args.channel, folder_date)
    manifest_path = folder_path / "manifest.json"

    if not manifest_path.exists():
        print(f"Error: Manifest not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print("\n" + "=" * 60)
    print("MANIFEST")
    print("=" * 60)
    print(f"\nChannel:     {manifest['channel_name']}")
    print(f"Folder:      {manifest['folder']}")
    print(f"Created:     {manifest['created_at']}")
    if 'updated_at' in manifest:
        print(f"Updated:     {manifest['updated_at']}")
    print(f"Total Clips: {manifest['total_clips']}")

    if args.verbose:
        print("\n" + "-" * 60)
        print("CLIPS:")
        print("-" * 60)

        for clip in manifest['clips']:
            print(f"\n{clip['filename']}")
            if 'metadata' in clip and clip['metadata']:
                for key, value in clip['metadata'].items():
                    print(f"  {key}: {value}")

    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Folder Organizer CLI - Manage SupoClip folder organization"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show folder statistics')

    # List command
    parser_list = subparsers.add_parser('list', help='List organized folders')
    parser_list.add_argument('--channel', help='Filter by channel name')
    parser_list.add_argument('--from-date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), help='From date (YYYY-MM-DD)')
    parser_list.add_argument('--to-date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), help='To date (YYYY-MM-DD)')
    parser_list.add_argument('--limit', type=int, help='Limit number of results')

    # Cleanup command
    parser_cleanup = subparsers.add_parser('cleanup', help='Cleanup old folders')
    parser_cleanup.add_argument('--retention-days', type=int, default=30, help='Retention period in days (default: 30)')
    parser_cleanup.add_argument('--dry-run', action='store_true', help='Simulate cleanup without deleting')

    # Organize task command
    parser_organize = subparsers.add_parser('organize-task', help='Organize clips from existing task')
    parser_organize.add_argument('task_id', help='Task ID')
    parser_organize.add_argument('--channel', help='Override channel name')

    # Channels command
    parser_channels = subparsers.add_parser('channels', help='List all channels')

    # Manifest command
    parser_manifest = subparsers.add_parser('manifest', help='Show folder manifest')
    parser_manifest.add_argument('channel', help='Channel name')
    parser_manifest.add_argument('date', help='Date (YYYY-MM-DD)')
    parser_manifest.add_argument('--verbose', '-v', action='store_true', help='Show detailed clip information')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Map commands to functions
    commands = {
        'stats': cmd_stats,
        'list': cmd_list,
        'cleanup': cmd_cleanup,
        'organize-task': cmd_organize_task,
        'channels': cmd_channels,
        'manifest': cmd_manifest,
    }

    # Run command
    asyncio.run(commands[args.command](args))


if __name__ == '__main__':
    from datetime import datetime
    main()

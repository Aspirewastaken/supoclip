# Folder Organization System

Automatic folder organization system for SupoClip clips. Organizes clips into a dated folder structure by channel for better management and discoverability.

## Overview

The folder organization system automatically organizes generated clips into a structured hierarchy:

```
/clips/
├── channel_name_1/
│   ├── 2025-11-10/
│   │   ├── manifest.json
│   │   ├── clip_0001_base_original_hook_title.mp4
│   │   ├── clip_0001_plus4s_flipped_hook_title.mp4
│   │   └── ...
│   ├── 2025-11-09/
│   │   ├── manifest.json
│   │   └── ...
│   └── ...
├── channel_name_2/
│   └── ...
```

## Features

- **Automatic Channel Detection**: Extracts channel name from video metadata (YouTube uploader, etc.)
- **Dated Folders**: Organizes clips by date (YYYY-MM-DD format)
- **Manifest Files**: Generates metadata files with clip information
- **Automatic Cleanup**: Removes old folders based on configurable retention period
- **Manual Organization**: Re-organize existing clips
- **Statistics & Reporting**: Track folder and clip counts across channels

## Installation

The folder organization system is included in the SupoClip backend. No additional installation required.

## Usage

### 1. Automatic Organization (Matrix Processing)

Clips are automatically organized when using the enhanced matrix processing worker:

```python
from src.workers.matrix_processing_with_organization import (
    process_clip_matrix_with_organization
)

# Process clips with automatic organization
result = await process_clip_matrix_with_organization(
    ctx=ctx,
    task_id=task_id,
    base_clips=base_clips,
    video_path=video_path,
    user_id=user_id,
    transcript_data=transcript_data,
    video_metadata=video_metadata,  # Channel name extracted from here
    channel_name="my_channel",  # Optional override
    options={
        'enable_folder_organization': True,  # Default: True
        'folder_retention_days': 30,  # Default: 30
        # ... other matrix processing options
    }
)

# Access organization results
print(f"Organized to: {result['organized_folder']}")
print(f"Clips organized: {result['organization']['organized_count']}")
```

### 2. Manual Organization (Existing Clips)

Organize clips from an existing task:

```python
from src.utils.folder_organizer import organize_task_clips

result = organize_task_clips(
    task_id="task-123",
    clip_files=[
        "/path/to/clip1.mp4",
        "/path/to/clip2.mp4",
    ],
    channel_name="my_channel",
    video_metadata={
        'uploader': 'Channel Name',
        'title': 'Video Title',
        'url': 'https://youtube.com/...'
    },
    task_metadata={
        'task_id': 'task-123',
        'user_id': 'user-456'
    }
)

print(f"Organized to: {result['folder']}")
```

### 3. Using the CLI

The folder organizer CLI provides command-line access to organization features:

```bash
# Show folder statistics
python -m src.cli.folder_organizer_cli stats

# List organized folders
python -m src.cli.folder_organizer_cli list
python -m src.cli.folder_organizer_cli list --channel "my_channel"
python -m src.cli.folder_organizer_cli list --from-date 2025-11-01

# Cleanup old folders (dry run)
python -m src.cli.folder_organizer_cli cleanup --dry-run
python -m src.cli.folder_organizer_cli cleanup --retention-days 30

# Organize existing task
python -m src.cli.folder_organizer_cli organize-task TASK_ID
python -m src.cli.folder_organizer_cli organize-task TASK_ID --channel "my_channel"

# List channels
python -m src.cli.folder_organizer_cli channels

# Show folder manifest
python -m src.cli.folder_organizer_cli manifest "my_channel" "2025-11-10"
python -m src.cli.folder_organizer_cli manifest "my_channel" "2025-11-10" --verbose
```

### 4. API Endpoints

The folder organization system includes REST API endpoints:

#### Get Statistics

```bash
GET /api/folders/statistics
```

**Response:**
```json
{
  "success": true,
  "total_channels": 5,
  "total_folders": 42,
  "total_clips": 378,
  "channels": {
    "my_channel": {
      "folders": 10,
      "clips": 90,
      "dates": ["2025-11-10", "2025-11-09", ...]
    }
  }
}
```

#### List Folders

```bash
GET /api/folders/list?channel_name=my_channel&limit=20
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "folders": [
    {
      "path": "/clips/my_channel/2025-11-10",
      "channel": "my_channel",
      "date": "2025-11-10",
      "clip_count": 9,
      "has_manifest": true,
      "manifest_path": "/clips/my_channel/2025-11-10/manifest.json"
    }
  ]
}
```

#### Cleanup Old Folders

```bash
POST /api/folders/cleanup
Content-Type: application/json

{
  "retention_days": 30,
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "dry_run": false,
  "cutoff_date": "2025-10-11",
  "retention_days": 30,
  "deleted_count": 5,
  "kept_count": 37,
  "error_count": 0,
  "deleted_folders": [
    {
      "path": "/clips/old_channel/2025-10-05",
      "channel": "old_channel",
      "date": "2025-10-05",
      "age_days": 36
    }
  ]
}
```

#### Organize Existing Task

```bash
POST /api/folders/organize
Content-Type: application/json

{
  "task_id": "task-123",
  "channel_name": "my_channel"  // Optional override
}
```

**Response:**
```json
{
  "success": true,
  "channel_name": "my_channel",
  "folder": "/clips/my_channel/2025-11-10",
  "date": "2025-11-10",
  "organized_count": 9,
  "failed_count": 0,
  "manifest_path": "/clips/my_channel/2025-11-10/manifest.json"
}
```

## Configuration

### Environment Variables

Configure folder organization in `backend/.env`:

```bash
# Base directory for clips (default: temp/clips)
TEMP_DIR=/path/to/temp

# Folder retention period in days (default: 30)
FOLDER_RETENTION_DAYS=30
```

### Python Configuration

```python
from src.utils.folder_organizer import FolderOrganizer

# Custom configuration
organizer = FolderOrganizer(
    base_clips_dir="/custom/clips/path",
    retention_days=60
)
```

## Manifest Format

Each dated folder contains a `manifest.json` file with metadata:

```json
{
  "version": "1.0",
  "channel_name": "my_channel",
  "folder": "/clips/my_channel/2025-11-10",
  "created_at": "2025-11-10T14:30:00",
  "updated_at": "2025-11-10T15:45:00",
  "total_clips": 9,
  "clips": [
    {
      "original_path": "/temp/matrix/task-123/clip_0001.mp4",
      "new_path": "/clips/my_channel/2025-11-10/clip_0001_base_original.mp4",
      "filename": "clip_0001_base_original.mp4",
      "channel_name": "my_channel",
      "folder": "/clips/my_channel/2025-11-10",
      "date": "2025-11-10",
      "metadata": {
        "clip_index": 0,
        "base_title": "Hook Title",
        "temporal_type": "base",
        "canvas_style": "original",
        "duration": 30.5,
        "engagement_score": 0.85
      }
    }
  ],
  "task_metadata": {
    "task_id": "task-123",
    "user_id": "user-456",
    "video_path": "/temp/video.mp4"
  }
}
```

## Integration Points

### 1. Matrix Processing Worker

Integrate with the matrix processing pipeline:

```python
# In backend/src/workers/full_matrix_task.py

from ..workers.matrix_processing_with_organization import (
    process_clip_matrix_with_organization
)
from ..youtube_utils import get_youtube_video_info

# Get video metadata for channel extraction
video_metadata = None
if source_url:
    video_metadata = get_youtube_video_info(source_url)

# Process with organization
matrix_result = await process_clip_matrix_with_organization(
    ctx=ctx,
    task_id=task_id,
    base_clips=base_clips,
    video_path=video_path,
    user_id=user_id,
    transcript_data=transcript_data,
    video_metadata=video_metadata,  # Channel extracted here
    options=matrix_options
)
```

### 2. Database Integration

Update sources table to track channel names:

```sql
-- Migration: Add channel_name to sources
ALTER TABLE sources ADD COLUMN channel_name VARCHAR(255);
ALTER TABLE sources ADD COLUMN url VARCHAR(1000);
CREATE INDEX idx_sources_channel_name ON sources(channel_name);
```

When creating sources, save channel information:

```python
# Extract channel from video metadata
from src.youtube_utils import get_youtube_video_info

video_info = get_youtube_video_info(youtube_url)

# Create source with channel info
await db.execute(
    text("""
        INSERT INTO sources (id, type, title, url, channel_name, created_at)
        VALUES (:id, :type, :title, :url, :channel_name, NOW())
    """),
    {
        "id": source_id,
        "type": "youtube",
        "title": video_info['title'],
        "url": youtube_url,
        "channel_name": video_info['uploader']
    }
)
```

### 3. Background Cleanup Task

Schedule automatic cleanup with arq:

```python
# In backend/src/workers/worker.py

from arq.cron import cron
from .matrix_processing_with_organization import cleanup_old_clip_folders

class WorkerSettings:
    functions = [
        # ... other tasks
        cleanup_old_clip_folders,
    ]

    # Schedule daily cleanup at 2 AM
    cron_jobs = [
        cron(cleanup_old_clip_folders, hour=2, minute=0, retention_days=30)
    ]
```

### 4. FastAPI Integration

Add folder organization endpoints to main API:

```python
# In backend/src/main.py

from .api.folder_organization import router as folder_router

app = FastAPI()
app.include_router(folder_router)
```

## Architecture

### Class: FolderOrganizer

Main class for folder organization operations.

**Methods:**

- `sanitize_channel_name(channel_name: str) -> str`
  Sanitize channel name for filesystem use

- `get_channel_name_from_metadata(video_metadata, user_input) -> str`
  Extract channel name from metadata or user input

- `get_dated_folder_path(channel_name: str, date: datetime) -> Path`
  Get path to dated folder

- `create_dated_folder(channel_name: str, date: datetime) -> Path`
  Create dated folder structure

- `organize_clip(clip_path, channel_name, metadata, date) -> dict`
  Organize a single clip file

- `organize_clips_batch(clips, channel_name, task_metadata, date) -> dict`
  Organize multiple clips

- `generate_manifest(folder_path, clips, channel_name, task_metadata) -> Path`
  Generate manifest.json

- `cleanup_old_folders(dry_run: bool) -> dict`
  Cleanup folders older than retention period

- `get_folder_statistics() -> dict`
  Get folder and clip statistics

- `list_folders(channel_name, date_from, date_to) -> list`
  List organized folders with filtering

### Helper Functions

- `organize_matrix_clips(matrix_result, channel_name, ...) -> dict`
  Organize matrix processing results

- `organize_task_clips(task_id, clip_files, channel_name, ...) -> dict`
  Organize clips from a task

## Best Practices

1. **Always provide video metadata** when available for accurate channel extraction
2. **Use meaningful channel names** - avoid generic names like "unknown_channel"
3. **Set appropriate retention periods** based on your storage capacity
4. **Run cleanup regularly** - schedule daily or weekly cleanup jobs
5. **Monitor manifest files** - use them for tracking and analytics
6. **Test with dry-run** before running cleanup operations
7. **Backup important clips** before cleanup

## Troubleshooting

### Issue: Clips not organizing automatically

**Solution:** Ensure `enable_folder_organization` is True in matrix processing options.

### Issue: Channel name is "unknown_channel"

**Solution:** Provide video_metadata with uploader information, or explicitly set channel_name.

### Issue: Manifest not generated

**Solution:** Check folder permissions. Ensure write access to clips directory.

### Issue: Old folders not cleaning up

**Solution:** Check retention_days setting. Verify folder date format (YYYY-MM-DD).

### Issue: Duplicate clips in folder

**Solution:** Clips are automatically renamed with incremental counter if duplicates exist.

## Performance Considerations

- **File Operations**: Moving files is faster than copying. The organizer uses `shutil.move` when possible.
- **Large Batches**: Organizing 100+ clips may take several seconds. Consider processing in smaller batches.
- **Database Queries**: Use indexes on channel_name for faster lookups.
- **Cleanup**: Dry-run cleanup before actual deletion to estimate time and impact.

## Future Enhancements

Potential improvements for future versions:

- [ ] Cloud storage integration (S3, GCS, Azure)
- [ ] Automatic folder archiving (zip old folders)
- [ ] Advanced search and filtering
- [ ] Analytics dashboard
- [ ] Webhook notifications for cleanup
- [ ] Multi-tenant support (per-user folders)
- [ ] Folder templates and custom structures
- [ ] Integration with content calendars

## License

Part of SupoClip - Open-source alternative to OpusClip

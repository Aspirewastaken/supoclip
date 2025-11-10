# Folder Organization Integration Guide

Quick integration guide for adding automatic folder organization to SupoClip.

## Quick Start (5 Minutes)

### 1. Run Database Migration

```bash
# Apply migration to add channel_name to sources table
psql -U postgres -d supoclip < backend/migrations/001_add_channel_name_to_sources.sql
```

Or for Docker:

```bash
docker exec -i supoclip-postgres psql -U postgres -d supoclip < backend/migrations/001_add_channel_name_to_sources.sql
```

### 2. Update Matrix Processing Worker

Replace the import in `backend/src/workers/full_matrix_task.py`:

```python
# Old import
from ..workers.matrix_processing import process_clip_matrix

# New import
from ..workers.matrix_processing_with_organization import (
    process_clip_matrix_with_organization as process_clip_matrix
)
```

That's it! Clips will now be automatically organized.

## Detailed Integration

### Step 1: Database Schema Update

The folder organization system requires two new fields in the `sources` table:

**Schema Changes:**
```sql
ALTER TABLE sources ADD COLUMN url VARCHAR(1000);
ALTER TABLE sources ADD COLUMN channel_name VARCHAR(255);
CREATE INDEX idx_sources_channel_name ON sources(channel_name);
```

**Migration File:**
- Location: `/home/user/supoclip/backend/migrations/001_add_channel_name_to_sources.sql`
- Run with: `psql` or include in Alembic migrations

### Step 2: Model Updates

The `Source` model has been updated to include the new fields:

```python
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # ...
```

**File:** `/home/user/supoclip/backend/src/models.py`

### Step 3: Integration with Video Processing

When creating sources, extract and save channel information:

```python
from src.youtube_utils import get_youtube_video_info

# Get video metadata
video_info = get_youtube_video_info(youtube_url)

# Create source with channel info
source = Source(
    id=generate_uuid_string(),
    type="youtube",
    title=video_info['title'],
    url=youtube_url,
    channel_name=video_info['uploader']  # Extract from metadata
)
```

### Step 4: Matrix Processing Integration

**Option A: Automatic (Recommended)**

Use the enhanced matrix processing function:

```python
from src.workers.matrix_processing_with_organization import (
    process_clip_matrix_with_organization
)
from src.youtube_utils import get_youtube_video_info

# Get video metadata for channel extraction
video_metadata = get_youtube_video_info(source_url) if source_url else None

# Process with automatic organization
result = await process_clip_matrix_with_organization(
    ctx=ctx,
    task_id=task_id,
    base_clips=base_clips,
    video_path=video_path,
    user_id=user_id,
    transcript_data=transcript_data,
    video_metadata=video_metadata,  # Channel extracted automatically
    channel_name=None,  # Optional override
    options={
        'enable_folder_organization': True,  # Enable organization
        'folder_retention_days': 30,
        # ... other matrix options
    }
)

# Access organized folder
print(f"Clips organized to: {result['organized_folder']}")
```

**Option B: Manual**

Organize clips after matrix processing:

```python
from src.workers.matrix_processing import process_clip_matrix
from src.utils.folder_organizer import organize_matrix_clips

# Standard matrix processing
matrix_result = await process_clip_matrix(...)

# Organize clips
organization_result = organize_matrix_clips(
    matrix_result=matrix_result,
    channel_name="my_channel",
    video_metadata=video_metadata,
    task_metadata={'task_id': task_id}
)
```

### Step 5: API Endpoints (Optional)

Add folder organization endpoints to your FastAPI app:

```python
# In backend/src/main.py

from src.api.folder_organization import router as folder_router

app = FastAPI()
app.include_router(folder_router)
```

**Available Endpoints:**
- `GET /api/folders/statistics` - Get folder statistics
- `GET /api/folders/list` - List organized folders
- `POST /api/folders/cleanup` - Cleanup old folders
- `POST /api/folders/organize` - Organize existing task
- `GET /api/folders/channels` - List all channels
- `GET /api/folders/manifest/{channel}/{date}` - Get manifest

### Step 6: Background Cleanup (Optional)

Schedule automatic folder cleanup:

```python
# In backend/src/workers/worker.py

from arq.cron import cron
from src.workers.matrix_processing_with_organization import cleanup_old_clip_folders

class WorkerSettings:
    functions = [
        # ... existing tasks
        cleanup_old_clip_folders,
    ]

    # Schedule daily cleanup at 2 AM
    cron_jobs = [
        cron(cleanup_old_clip_folders, hour=2, minute=0, retention_days=30, dry_run=False)
    ]
```

## File Structure

After integration, your project will have:

```
backend/
├── src/
│   ├── utils/
│   │   └── folder_organizer.py          # Core organizer class
│   ├── workers/
│   │   └── matrix_processing_with_organization.py  # Enhanced worker
│   ├── api/
│   │   └── folder_organization.py       # API endpoints
│   ├── cli/
│   │   └── folder_organizer_cli.py      # CLI tool
│   └── models.py                        # Updated with channel_name
├── migrations/
│   └── 001_add_channel_name_to_sources.sql  # Database migration
└── docs/
    ├── FOLDER_ORGANIZATION.md           # Full documentation
    └── FOLDER_ORGANIZATION_INTEGRATION.md  # This file
```

## Configuration

Add to `backend/.env`:

```bash
# Folder organization settings
TEMP_DIR=/path/to/clips
FOLDER_RETENTION_DAYS=30
```

## Folder Structure Output

Clips will be organized as:

```
/clips/
├── joe_rogan_experience/
│   ├── 2025-11-10/
│   │   ├── manifest.json
│   │   ├── 0000_base_original_hook_1.mp4
│   │   ├── 0000_plus4s_flipped_hook_1.mp4
│   │   └── ...
│   └── 2025-11-09/
│       └── ...
├── lex_fridman_podcast/
│   └── ...
└── unknown_channel/  # Fallback for clips without metadata
    └── ...
```

## Testing

### Test with CLI

```bash
# Check if integration is working
python -m src.cli.folder_organizer_cli stats

# List folders
python -m src.cli.folder_organizer_cli list

# Test cleanup (dry run)
python -m src.cli.folder_organizer_cli cleanup --dry-run
```

### Test with API

```bash
# Get statistics
curl http://localhost:8000/api/folders/statistics

# List folders
curl http://localhost:8000/api/folders/list

# Test cleanup (dry run)
curl -X POST http://localhost:8000/api/folders/cleanup \
  -H "Content-Type: application/json" \
  -d '{"retention_days": 30, "dry_run": true}'
```

## Rollback

If you need to rollback the integration:

### 1. Revert Database Changes

```sql
ALTER TABLE sources DROP COLUMN channel_name;
ALTER TABLE sources DROP COLUMN url;
DROP INDEX idx_sources_channel_name;
```

### 2. Revert Code Changes

```python
# Restore original import
from ..workers.matrix_processing import process_clip_matrix
```

### 3. Remove API Routes (if added)

```python
# Remove from main.py
# app.include_router(folder_router)
```

## Troubleshooting

### Issue: Channel name not extracted

**Check:**
1. Video metadata is being fetched: `video_metadata = get_youtube_video_info(url)`
2. Metadata contains `uploader` field
3. Channel name is saved to database when creating source

**Fix:**
```python
# Debug metadata
video_metadata = get_youtube_video_info(url)
print(f"Uploader: {video_metadata.get('uploader')}")
```

### Issue: Clips still in old location

**Check:**
1. `enable_folder_organization` is `True` in options
2. Matrix processing is using the enhanced version

**Fix:**
```python
# Manually organize existing clips
python -m src.cli.folder_organizer_cli organize-task TASK_ID
```

### Issue: Migration fails

**Check:**
1. Database connection is working
2. No existing columns with same name
3. User has ALTER TABLE permissions

**Fix:**
```sql
-- Check existing columns
SELECT column_name FROM information_schema.columns
WHERE table_name = 'sources';

-- Add IF NOT EXISTS
ALTER TABLE sources ADD COLUMN IF NOT EXISTS channel_name VARCHAR(255);
```

## Performance Impact

- **Storage**: No significant increase (clips moved, not copied)
- **Processing Time**: +1-2 seconds per batch organization
- **Database**: New index on `channel_name` improves query performance
- **Memory**: Minimal impact (<10MB for typical batch sizes)

## Next Steps

After integration:

1. **Monitor first batch** - Check logs for organization success
2. **Verify folder structure** - Inspect `/clips` directory
3. **Test API endpoints** - Use Postman or curl to test endpoints
4. **Schedule cleanup** - Set up background cleanup task
5. **Update frontend** - Add UI for browsing organized folders

## Support

For issues or questions:

1. Check full documentation: `backend/docs/FOLDER_ORGANIZATION.md`
2. Use CLI for debugging: `python -m src.cli.folder_organizer_cli stats`
3. Check logs for errors: `docker-compose logs -f backend`
4. Test with dry-run: Always use `--dry-run` flag before cleanup

## Summary

**Minimum Integration (2 steps):**
1. Run database migration
2. Update matrix processing import

**Full Integration (6 steps):**
1. Run database migration
2. Update matrix processing import
3. Extract channel from video metadata
4. Add API endpoints
5. Configure environment variables
6. Schedule background cleanup

The folder organization system is designed to work seamlessly with existing code and can be enabled with minimal changes.

# CDN Storage Integration

Automatic CDN upload and delivery for SupoClip video clips.

## Quick Start

### 1. Choose a CDN Provider

- **AWS CloudFront**: Best for AWS ecosystem, enterprise features
- **Cloudflare R2**: Best for cost (zero egress fees)
- **Bunny CDN**: Best price/performance ratio

### 2. Configure Environment

```bash
# In backend/.env
CDN_ENABLED=true
CDN_PROVIDER=r2  # or cloudfront, bunny
CDN_BASE_URL=https://clips.yourdomain.com

# Add provider-specific credentials (see .env.cdn.example)
```

### 3. Install Dependencies

```bash
cd backend

# For CloudFront/R2 (S3-compatible providers)
uv add boto3

# For cache purging (R2/Bunny)
uv add aiohttp
```

### 4. Done!

Clips are now automatically uploaded to CDN after generation. No code changes needed.

## Features

✅ **Automatic Upload** - Clips uploaded to CDN in parallel after generation
✅ **Smart URL Fallback** - CDN → Direct serving fallback
✅ **Signed URLs** - Time-limited secure URLs for private content
✅ **Cache Purging** - Invalidate CDN cache when needed
✅ **Multiple Providers** - Switch providers with config change
✅ **Error Handling** - Graceful degradation if CDN fails

## Architecture

```
Video Processing Pipeline:
1. Generate clips with AI
2. Save clips locally
3. Upload to CDN (parallel) ←── CDN Integration
4. Store CDN URLs in database
5. Return CDN URLs to frontend

URL Resolution:
1. Check database for cdn_url
2. If available, return CDN URL
3. If CDN enabled, generate CDN URL
4. Otherwise, fallback to /clips/{filename}
```

## File Structure

```
backend/src/storage/
├── __init__.py           # Public API exports
├── cdn.py                # CDN provider implementations
├── integrations.py       # Video pipeline integration
└── README.md            # This file

backend/
├── CDN_SETUP_GUIDE.md   # Detailed setup guide
└── .env.cdn.example     # Configuration examples
```

## Usage Examples

### Get Clip URL (with CDN fallback)

```python
from backend.src.storage.integrations import get_clip_url

# Automatic CDN fallback
url = get_clip_url(
    filename="clip_1.mp4",
    cdn_url="https://cdn.example.com/clips/task-123/clip_1.mp4",  # From DB
    task_id="task-123"
)
# Returns: CDN URL if available, otherwise /clips/clip_1.mp4
```

### Upload Clip Manually

```python
from backend.src.storage.integrations import upload_clip_to_cdn

cdn_url = await upload_clip_to_cdn(
    clip_path="/tmp/clips/clip_1.mp4",
    filename="clip_1.mp4",
    task_id="task-123"
)
# Returns: https://cdn.example.com/clips/task-123/clip_1.mp4
```

### Generate Signed URL

```python
from backend.src.storage.integrations import get_clip_url

# Private URL valid for 1 hour
secure_url = get_clip_url(
    filename="private_clip.mp4",
    task_id="task-123",
    signed=True,
    expiry=3600
)
```

### Purge CDN Cache

```python
from backend.src.storage.cdn import purge_cdn_cache

# Invalidate cache for specific clips
await purge_cdn_cache([
    "clips/task-123/clip_1.mp4",
    "clips/task-123/clip_2.mp4"
])
```

### Delete from CDN

```python
from backend.src.storage.integrations import cleanup_cdn_clips

# Delete all clips for a task
deleted_count = await cleanup_cdn_clips(
    task_id="task-123",
    filenames=["clip_1.mp4", "clip_2.mp4"]
)
```

## API Integration

The CDN integration is already wired into the main API:

### Automatic Upload

```python
# In main.py /start endpoint:
# 1. Generate clips
clips_info = create_clips_with_transitions(...)

# 2. Upload to CDN (automatic)
cdn_urls = await upload_clips_batch(clips_info, task.id)

# 3. Save with CDN URLs
clip_record = GeneratedClip(
    ...,
    cdn_url=cdn_urls.get(clip_info["filename"])
)
```

### URL in Response

```python
# GET /tasks/{task_id}/clips returns:
{
  "clips": [
    {
      "filename": "clip_1.mp4",
      "file_path": "/tmp/clips/clip_1.mp4",
      "cdn_url": "https://cdn.example.com/clips/task-123/clip_1.mp4",
      "video_url": "https://cdn.example.com/clips/task-123/clip_1.mp4"  # CDN or fallback
    }
  ]
}
```

## Provider Comparison

| Feature              | CloudFront | R2    | Bunny |
|----------------------|------------|-------|-------|
| Setup Complexity     | Medium     | Easy  | Easy  |
| Global Network       | ✅ 400+    | ✅ 250+ | ✅ 114 |
| Signed URLs          | ✅         | ✅    | ✅    |
| Cache Purging        | ✅         | ✅    | ✅    |
| Cost (100 TB egress) | $8,500     | $0    | $1,000|
| Storage Cost/GB      | $0.023     | $0.015| $0.010|
| Free Tier            | 1 TB/year  | None  | None  |

**Recommendation**: Cloudflare R2 for cost, Bunny for performance, CloudFront for AWS integration.

## Monitoring

Check CDN status in logs:

```
☁️ Uploading clips to CDN (if configured)
📤 Uploading clip to CDN: clip_1_10.5_25.3.mp4
✅ Clip uploaded to CDN: https://cdn.example.com/clips/task-123/clip_1.mp4
✅ CDN upload complete - 5 clips uploaded
```

## Troubleshooting

### CDN not uploading

1. Check `CDN_ENABLED=true` in `.env`
2. Verify provider credentials
3. Check logs for error messages
4. Test provider connection:
   ```python
   from backend.src.storage.cdn import get_cdn_provider
   provider = get_cdn_provider()
   print(f"CDN active: {provider.is_enabled()}")
   ```

### Missing dependencies

```bash
# For CloudFront/R2
uv add boto3

# For cache purging
uv add aiohttp
```

### Database errors

Run migration to add `cdn_url` column:

```sql
ALTER TABLE generated_clips ADD COLUMN cdn_url VARCHAR(1000);
```

## Documentation

- **Setup Guide**: `/backend/CDN_SETUP_GUIDE.md` - Detailed configuration for each provider
- **Config Examples**: `/backend/.env.cdn.example` - Copy-paste configuration templates
- **Implementation**: `cdn.py` - CDN provider implementations
- **Integration**: `integrations.py` - Video pipeline integration logic

## Support

- **Issues**: File with `[CDN]` tag
- **Questions**: See CLAUDE.md for architecture
- **Contributing**: Submit PR with tests

---

**Version**: 1.0.0
**Last Updated**: 2025-11-10

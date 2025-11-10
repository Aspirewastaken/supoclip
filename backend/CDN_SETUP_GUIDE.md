# SupoClip CDN Integration Setup Guide

This guide explains how to configure and use CDN (Content Delivery Network) integration for SupoClip clip delivery.

## Overview

SupoClip supports automatic CDN upload for generated video clips with the following features:

- **Multiple CDN Providers**: AWS CloudFront, Cloudflare R2, Bunny CDN
- **Automatic Upload**: Clips are uploaded to CDN immediately after generation
- **Signed URLs**: Generate time-limited, secure URLs for private clips
- **Cache Purging**: Invalidate CDN cache when clips are updated or deleted
- **Fallback Support**: Automatically falls back to direct serving if CDN is unavailable

## Supported CDN Providers

### 1. AWS CloudFront (with S3 backend)

**Best for**: Enterprise applications, AWS infrastructure, advanced features

**Features**:
- Global edge network with 400+ locations
- Integration with AWS S3 for storage
- CloudFront signed URLs for private content
- Cache invalidation support
- Pay-as-you-go pricing

**Cost**: ~$0.085/GB (first 10 TB), ~$0.020/GB (10 GB free tier on S3)

### 2. Cloudflare R2

**Best for**: Cost-effective solution, zero egress fees

**Features**:
- S3-compatible API
- Zero egress fees (only storage costs)
- Cloudflare's global CDN network
- Custom domain support
- Presigned URL support

**Cost**: $0.015/GB storage, $0 egress (significant savings at scale)

### 3. Bunny CDN

**Best for**: Best price/performance ratio, simple setup

**Features**:
- High-performance CDN with 114 PoPs
- Integrated storage (Bunny Storage)
- Token-based authentication
- Volume zone support
- Very competitive pricing

**Cost**: $0.01/GB CDN, $0.01/GB storage (varies by region)

## Configuration

### Environment Variables

All CDN configuration is done via environment variables in your `backend/.env` file.

#### General CDN Settings

```bash
# Enable CDN integration
CDN_ENABLED=true

# CDN provider: cloudfront, r2, or bunny
CDN_PROVIDER=cloudfront

# CDN base URL (your CloudFront/R2/Bunny CDN domain)
CDN_BASE_URL=https://d123456789.cloudfront.net
```

### Provider-Specific Configuration

#### AWS CloudFront Configuration

```bash
# AWS credentials
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1

# S3 bucket name (backend storage for CloudFront)
AWS_S3_BUCKET=supoclip-clips

# CloudFront distribution ID (for cache invalidation)
CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC

# CloudFront signed URLs (optional, for private content)
CLOUDFRONT_KEY_ID=your_key_pair_id
CLOUDFRONT_PRIVATE_KEY_PATH=/path/to/private_key.pem

# CDN base URL (CloudFront distribution domain)
CDN_BASE_URL=https://d123456789.cloudfront.net
```

**Setup Steps**:

1. Create an S3 bucket:
   ```bash
   aws s3 mb s3://supoclip-clips --region us-east-1
   ```

2. Create a CloudFront distribution:
   - Origin: Your S3 bucket
   - Origin Access Control: Enable (recommended for security)
   - Default Cache Behavior: CachingOptimized
   - Viewer Protocol Policy: Redirect HTTP to HTTPS

3. (Optional) Generate CloudFront key pair for signed URLs:
   - Go to AWS Console → Account → Security Credentials
   - Create CloudFront Key Pair
   - Download private key and note the Access Key ID

4. Set bucket policy to allow CloudFront access:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "AllowCloudFrontServicePrincipal",
         "Effect": "Allow",
         "Principal": {
           "Service": "cloudfront.amazonaws.com"
         },
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::supoclip-clips/*",
         "Condition": {
           "StringEquals": {
             "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT-ID:distribution/DISTRIBUTION-ID"
           }
         }
       }
     ]
   }
   ```

#### Cloudflare R2 Configuration

```bash
# Cloudflare account ID
CLOUDFLARE_ACCOUNT_ID=your_account_id

# R2 access credentials
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=supoclip-clips

# R2 public URL (custom domain or r2.dev subdomain)
R2_PUBLIC_URL=https://clips.yourdomain.com
# OR use R2.dev domain:
# R2_PUBLIC_URL=https://your-bucket.r2.cloudflarestorage.com

# Cloudflare Zone ID (for cache purging via Cloudflare CDN)
CLOUDFLARE_ZONE_ID=your_zone_id

# Cloudflare API token (with Cache Purge permission)
CLOUDFLARE_API_TOKEN=your_api_token

# CDN base URL
CDN_BASE_URL=https://clips.yourdomain.com
```

**Setup Steps**:

1. Create an R2 bucket:
   - Go to Cloudflare Dashboard → R2
   - Create bucket: `supoclip-clips`

2. Generate R2 API tokens:
   - In R2 bucket settings → Manage R2 API Tokens
   - Create API token with Read & Write permissions

3. (Optional) Set up custom domain:
   - In R2 bucket settings → Settings → Public Access
   - Connect custom domain (e.g., `clips.yourdomain.com`)
   - Cloudflare will automatically provide CDN acceleration

4. (Optional) Create Cloudflare API token for cache purging:
   - Dashboard → My Profile → API Tokens
   - Create token with "Zone.Cache Purge" permission

#### Bunny CDN Configuration

```bash
# Bunny Storage configuration
BUNNY_STORAGE_ZONE_NAME=supoclip-clips
BUNNY_STORAGE_API_KEY=your_storage_api_key

# Bunny CDN API key (for cache purging)
BUNNY_CDN_API_KEY=your_cdn_api_key

# Storage region: de (Europe), ny (New York), la (Los Angeles), sg (Singapore), etc.
BUNNY_STORAGE_REGION=de

# Pull Zone ID (for cache purging)
BUNNY_PULL_ZONE_ID=12345

# CDN base URL (Pull Zone URL or custom domain)
CDN_BASE_URL=https://supoclip.b-cdn.net
# OR custom domain:
# CDN_BASE_URL=https://clips.yourdomain.com
```

**Setup Steps**:

1. Create a Storage Zone:
   - Bunny Dashboard → Storage → Add Storage Zone
   - Name: `supoclip-clips`
   - Region: Choose closest to your users
   - Note the FTP & API Password (this is your Storage API Key)

2. Create a Pull Zone:
   - Bunny Dashboard → CDN → Add Pull Zone
   - Type: Storage Zone
   - Origin: Select your `supoclip-clips` storage zone
   - Note the Pull Zone URL (e.g., `supoclip.b-cdn.net`)

3. Get API credentials:
   - Storage API Key: From Storage Zone settings
   - CDN API Key: Account → API (this is your account-wide API key)
   - Pull Zone ID: From Pull Zone settings URL

4. (Optional) Add custom domain:
   - Pull Zone → Hostnames → Add Hostname
   - Add DNS CNAME record: `clips.yourdomain.com` → `supoclip.b-cdn.net`

## Usage

### Automatic Upload

Once configured, CDN upload is automatic:

1. User submits video for processing
2. SupoClip generates clips with AI
3. **Clips are automatically uploaded to CDN** (in parallel)
4. CDN URLs are stored in database
5. API returns CDN URLs to frontend

No additional code needed - it's fully integrated into the video processing pipeline!

### URL Priority

The system uses intelligent URL fallback:

1. **CDN URL** (if stored in database and CDN is configured)
2. **Generated CDN URL** (if CDN provider is active)
3. **Direct serving** (fallback via FastAPI static files)

Example:
```python
# In your application
clip_url = get_clip_url(
    filename="clip_1.mp4",
    cdn_url="https://cdn.example.com/clips/task-123/clip_1.mp4",  # From database
    task_id="task-123",
    signed=False  # Set to True for private URLs
)
# Returns: CDN URL if available, falls back to /clips/clip_1.mp4
```

### Signed URLs (Private Clips)

For private/secure content, generate time-limited signed URLs:

```python
from backend.src.storage.integrations import get_clip_url

# Generate signed URL valid for 1 hour
secure_url = get_clip_url(
    filename="private_clip.mp4",
    task_id="task-123",
    signed=True,
    expiry=3600  # 1 hour in seconds
)
```

**How it works**:
- **CloudFront**: Uses RSA-signed cookies/URLs with private key
- **R2**: Uses S3-compatible presigned URLs
- **Bunny**: Uses token-based authentication with SHA256 signature

### Cache Purging

Invalidate CDN cache when clips are updated or deleted:

```python
from backend.src.storage.cdn import purge_cdn_cache

# Purge specific clips
await purge_cdn_cache([
    "clips/task-123/clip_1.mp4",
    "clips/task-123/clip_2.mp4"
])
```

**Provider behavior**:
- **CloudFront**: Creates invalidation request (charges apply: $0.005/path beyond first 1,000/month)
- **R2**: Purges via Cloudflare API (requires Zone ID and API token)
- **Bunny**: Purges via Bunny API (instant, no charges)

### Deleting Clips

Delete clips from CDN when tasks are deleted:

```python
from backend.src.storage.integrations import cleanup_cdn_clips

# Delete all clips for a task
deleted_count = await cleanup_cdn_clips(
    task_id="task-123",
    filenames=["clip_1.mp4", "clip_2.mp4", "clip_3.mp4"]
)
```

## Database Schema

The CDN integration adds a `cdn_url` field to the `generated_clips` table:

```sql
ALTER TABLE generated_clips
ADD COLUMN cdn_url VARCHAR(1000);
```

**Migration**: Run this migration if upgrading from a previous version:

```bash
# Using alembic (recommended)
cd backend
alembic revision --autogenerate -m "Add CDN URL to clips"
alembic upgrade head

# OR manual SQL
psql -U your_user -d supoclip -c "ALTER TABLE generated_clips ADD COLUMN cdn_url VARCHAR(1000);"
```

## Cost Optimization

### Tips for Reducing CDN Costs

1. **Choose the right provider**:
   - High traffic (>10 TB/month): Cloudflare R2 (zero egress)
   - Moderate traffic: Bunny CDN (best price/performance)
   - AWS ecosystem: CloudFront (if already using AWS)

2. **Enable compression**: All providers support Brotli/Gzip compression
   - Reduces bandwidth by 60-80% for text/metadata
   - Video already compressed (H.264), minimal benefit

3. **Set long cache times**: Clips are immutable
   ```python
   ExtraArgs={'CacheControl': 'public, max-age=31536000'}  # 1 year
   ```

4. **Use object lifecycle policies**:
   - Archive old clips to cheaper storage tiers
   - Auto-delete clips after X days (if ephemeral)

5. **Cloudflare R2 advantages**:
   - Zero egress fees = 80-90% cost savings at scale
   - Example: 100 TB/month egress = $0 (vs $8,500 on CloudFront)

### Cost Comparison (100 TB egress/month)

| Provider      | Storage (1 TB) | Egress (100 TB) | Cache Invalidations | Total/Month |
|---------------|----------------|-----------------|---------------------|-------------|
| CloudFront    | $23            | $8,500          | ~$5                 | **$8,528**  |
| R2            | $15            | $0              | $0                  | **$15**     |
| Bunny CDN     | $10            | $1,000          | $0                  | **$1,010**  |

**Recommendation**: For video delivery at scale, Cloudflare R2 offers the best value.

## Monitoring

### Logging

CDN operations are logged with emoji prefixes for easy identification:

```
☁️ Uploading clips to CDN (if configured)
✅ CDN upload complete - 5 clips uploaded
📤 Uploading clip to CDN: clip_1_10.5_25.3.mp4
✅ Clip uploaded to CDN: https://cdn.example.com/clips/task-123/clip_1.mp4
```

### Health Checks

Monitor CDN health:

```python
from backend.src.storage.cdn import get_cdn_provider

provider = get_cdn_provider()
if provider and provider.is_enabled():
    print(f"✅ CDN active: {provider.__class__.__name__}")
else:
    print("⚠️ CDN not configured, using direct serving")
```

### Error Handling

The system gracefully handles CDN failures:

1. If CDN upload fails, clip is still saved locally
2. API returns local URL as fallback
3. Errors are logged but don't break video processing
4. Retry logic can be added in `upload_clips_batch()`

## Troubleshooting

### Common Issues

#### 1. "CDN not configured, skipping upload"

**Cause**: `CDN_ENABLED=false` or missing provider configuration

**Fix**: Set `CDN_ENABLED=true` and configure provider variables

#### 2. "Failed to upload to CDN: Access Denied"

**Cause**: Invalid credentials or missing IAM permissions

**Fix**:
- **CloudFront**: Verify AWS credentials and S3 bucket policy
- **R2**: Verify R2 API tokens have Read & Write permissions
- **Bunny**: Verify Storage API Key is correct

#### 3. "boto3 not installed"

**Cause**: Required dependency missing (for CloudFront/R2)

**Fix**:
```bash
cd backend
uv add boto3
# OR
pip install boto3
```

#### 4. "aiohttp not installed"

**Cause**: Required dependency missing (for R2/Bunny cache purging)

**Fix**:
```bash
cd backend
uv add aiohttp
# OR
pip install aiohttp
```

#### 5. Signed URLs not working

**Cause**: Missing or incorrect signing keys

**Fix**:
- **CloudFront**: Verify `CLOUDFRONT_KEY_ID` and `CLOUDFRONT_PRIVATE_KEY_PATH`
- **R2**: Verify bucket has public access disabled
- **Bunny**: Verify `BUNNY_CDN_API_KEY` is set

#### 6. Cache not purging

**Cause**: Missing cache purge credentials

**Fix**:
- **CloudFront**: Verify `CLOUDFRONT_DISTRIBUTION_ID` is set
- **R2**: Verify `CLOUDFLARE_ZONE_ID` and `CLOUDFLARE_API_TOKEN` are set
- **Bunny**: Verify `BUNNY_PULL_ZONE_ID` and `BUNNY_CDN_API_KEY` are set

## Advanced Usage

### Custom CDN Provider

Extend the `CDNProvider` base class to add custom providers:

```python
from backend.src.storage.cdn import CDNProvider

class CustomCDNProvider(CDNProvider):
    async def upload(self, local_path: str, remote_path: str, content_type: str = 'video/mp4') -> bool:
        # Your upload logic
        pass

    def get_url(self, remote_path: str, signed: bool = False, expiry: int = 3600) -> str:
        # Your URL generation logic
        pass

    async def delete(self, remote_path: str) -> bool:
        # Your deletion logic
        pass

    async def purge(self, paths: list) -> bool:
        # Your cache purging logic
        pass
```

### Multiple CDN Regions

For global users, deploy multiple CDN endpoints:

```python
# In production, use geo-routing or load balancer
CDN_PROVIDERS = {
    'us': 'cloudfront',
    'eu': 'bunny',
    'asia': 'cloudfront'
}

def get_cdn_for_region(region: str):
    return get_cdn_provider(CDN_PROVIDERS.get(region, 'cloudfront'))
```

### Performance Optimization

For maximum upload speed, increase parallel uploads:

```python
# In storage/integrations.py, adjust concurrency
async def upload_clips_batch(clips_info: list, task_id: str):
    # Upload up to 10 clips in parallel
    semaphore = asyncio.Semaphore(10)

    async def upload_with_limit(clip):
        async with semaphore:
            return await upload_clip_to_cdn(
                clip_path=clip['path'],
                filename=clip['filename'],
                task_id=task_id
            )

    upload_tasks = [upload_with_limit(clip) for clip in clips_info]
    cdn_urls = await asyncio.gather(*upload_tasks)
```

## Security Best Practices

1. **Use signed URLs for private content**: Don't expose sensitive clips publicly
2. **Rotate API keys regularly**: Especially for storage access
3. **Enable HTTPS only**: Force HTTPS on CDN distributions
4. **Implement rate limiting**: Prevent abuse of signed URL generation
5. **Monitor access logs**: Track unusual download patterns
6. **Use IAM roles** (AWS): Avoid hardcoded credentials in production

## Migration Guide

### Migrating from Direct Serving to CDN

1. **Add CDN configuration** to `.env`
2. **Run database migration** to add `cdn_url` column
3. **Enable CDN**: Set `CDN_ENABLED=true`
4. **Test with one video**: Process a test video and verify CDN upload
5. **Monitor logs**: Check for CDN upload success
6. **(Optional) Backfill existing clips**: Upload old clips to CDN

### Backfilling Old Clips

```python
# Script to upload existing clips to CDN
import asyncio
from pathlib import Path
from backend.src.storage.integrations import upload_clip_to_cdn
from backend.src.database import AsyncSessionLocal
from sqlalchemy import text

async def backfill_clips():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT id, task_id, filename, file_path FROM generated_clips WHERE cdn_url IS NULL")
        )
        clips = result.fetchall()

        for clip in clips:
            if Path(clip.file_path).exists():
                cdn_url = await upload_clip_to_cdn(
                    clip_path=clip.file_path,
                    filename=clip.filename,
                    task_id=clip.task_id
                )

                if cdn_url:
                    await db.execute(
                        text("UPDATE generated_clips SET cdn_url = :cdn_url WHERE id = :id"),
                        {"cdn_url": cdn_url, "id": clip.id}
                    )
        await db.commit()

# Run: python -c "import asyncio; from backfill import backfill_clips; asyncio.run(backfill_clips())"
```

## Support

- **Documentation**: See `/backend/src/storage/cdn.py` for implementation details
- **Issues**: File a GitHub issue with `[CDN]` prefix
- **Questions**: Check CLAUDE.md for architecture overview

---

**Last Updated**: 2025-11-10
**Version**: 1.0.0

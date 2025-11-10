# Social Media Integration Guide

This guide provides detailed instructions for integrating SupoClip with TikTok, Instagram, YouTube Shorts, and Twitter/X APIs.

---

## Table of Contents

1. [Overview](#overview)
2. [TikTok Integration](#tiktok-integration)
3. [Instagram Integration](#instagram-integration)
4. [YouTube Shorts Integration](#youtube-shorts-integration)
5. [Twitter/X Integration](#twitterx-integration)
6. [Environment Configuration](#environment-configuration)
7. [API Usage](#api-usage)
8. [Scheduler Setup](#scheduler-setup)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The SupoClip social media integration system enables:

- **OAuth 2.0 authentication** for multiple platforms
- **Automated video posting** to TikTok, Instagram, YouTube, and Twitter/X
- **Scheduled posting** with queue management
- **Retry logic** with exponential backoff for failed posts
- **Post status tracking** and analytics

### Architecture

```
┌─────────────┐
│   SupoClip  │
│   Backend   │
└─────┬───────┘
      │
      ├─── OAuth Flows ───┬─── TikTok
      │                   ├─── Instagram
      │                   ├─── YouTube
      │                   └─── Twitter/X
      │
      ├─── Redis Queue ───── Scheduled Posts
      │
      └─── PostgreSQL ────── Tokens, Posts, Attempts
```

---

## TikTok Integration

### 1. Create TikTok Developer Account

1. Go to [TikTok for Developers](https://developers.tiktok.com/)
2. Sign in with your TikTok account
3. Complete developer verification

### 2. Create App

1. Navigate to **My Apps** → **Create an App**
2. Fill in app details:
   - **App Name**: SupoClip
   - **App Type**: Web App
   - **Category**: Entertainment

### 3. Configure OAuth

1. In your app settings, go to **Login Kit**
2. Add **Redirect URI**: `https://yourdomain.com/api/social/callback/tiktok`
3. Select **Scopes**:
   - `user.info.basic`
   - `video.upload`
   - `video.publish`

### 4. Get Credentials

- **Client Key** (Client ID)
- **Client Secret**

### 5. Environment Variables

```bash
TIKTOK_CLIENT_ID=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_REDIRECT_URI=https://yourdomain.com/api/social/callback/tiktok
```

### TikTok API Specifics

- **Video Requirements**:
  - Format: MP4
  - Max size: 287 MB
  - Max duration: 10 minutes
  - Min duration: 3 seconds
  - Resolution: 540x960 or higher (9:16 aspect ratio preferred)

- **Title Limits**: 150 characters
- **Upload Process**: 3-step (Initialize → Upload → Publish)
- **Privacy Options**: `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `SELF_ONLY`

### Example TikTok Config

```json
{
  "privacy_level": "PUBLIC_TO_EVERYONE",
  "disable_duet": false,
  "disable_stitch": false,
  "disable_comment": false,
  "cover_timestamp_ms": 1000
}
```

---

## Instagram Integration

### 1. Create Facebook Developer Account

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a developer account
3. Complete business verification (required for Instagram API)

### 2. Create App

1. Navigate to **My Apps** → **Create App**
2. Select **Business** as app type
3. Fill in app details:
   - **App Name**: SupoClip
   - **Contact Email**: your@email.com

### 3. Configure Instagram Basic Display

1. Add **Instagram Basic Display** product
2. Create new **Instagram App**
3. Configure OAuth settings:
   - **Valid OAuth Redirect URIs**: `https://yourdomain.com/api/social/callback/instagram`

### 4. Get Permissions

Request these permissions:
- `instagram_basic`
- `instagram_content_publish`
- `pages_read_engagement`

### 5. Connect Instagram Business Account

1. Your Instagram account must be:
   - **Business** or **Creator** account
   - Connected to a **Facebook Page**
2. Get the Facebook Page reviewed for permissions

### 6. Get Credentials

- **App ID** (Client ID)
- **App Secret** (Client Secret)

### 7. Environment Variables

```bash
INSTAGRAM_CLIENT_ID=your_app_id
INSTAGRAM_CLIENT_SECRET=your_app_secret
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/api/social/callback/instagram
```

### Instagram API Specifics

- **Video Requirements**:
  - Format: MP4
  - Max size: 100 MB
  - Max duration: 90 seconds (for Reels)
  - Min duration: 3 seconds
  - Aspect ratio: 9:16 (vertical)
  - Video must be hosted at a **public URL** (Instagram fetches from URL)

- **Caption Limits**: 2,200 characters
- **Upload Process**: Create Container → Wait for Processing → Publish
- **Token Lifetime**: 60 days (must refresh before expiry)

### Example Instagram Config

```json
{
  "share_to_feed": true,
  "video_url": "https://yourdomain.com/clips/video.mp4"
}
```

### Important Notes

- Videos must be **publicly accessible** via HTTPS
- Instagram **fetches** the video from the URL (doesn't accept direct upload)
- Consider using CDN or temporary public storage (S3, Cloudflare R2)
- Processing can take 1-5 minutes depending on video length

---

## YouTube Shorts Integration

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3**

### 2. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Fill in app information:
   - **App name**: SupoClip
   - **User support email**: your@email.com
4. Add scopes:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`

### 3. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. Select **Web application**
4. Add **Authorized redirect URIs**:
   - `https://yourdomain.com/api/social/callback/youtube`

### 4. Get Credentials

- **Client ID**
- **Client Secret**

### 5. Environment Variables

```bash
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=https://yourdomain.com/api/social/callback/youtube
```

### YouTube API Specifics

- **Video Requirements**:
  - Format: MP4
  - Max size: 256 GB (or 12 hours, whichever is less)
  - Shorts requirements:
    - Duration: ≤ 60 seconds
    - Aspect ratio: 9:16 (vertical)
    - Resolution: 1080x1920 recommended

- **Title Limits**: 100 characters
- **Description Limits**: 5,000 characters
- **Tags**: Up to 500 tags (comma-separated)
- **Upload Process**: Multipart upload (metadata + video)

### Example YouTube Config

```json
{
  "title": "Amazing Short Video",
  "category_id": "22",
  "privacy_status": "public",
  "made_for_kids": false,
  "is_short": true
}
```

### Making Videos Appear as Shorts

To ensure videos appear as Shorts:
1. Duration **must be ≤ 60 seconds**
2. Aspect ratio **must be 9:16** (vertical)
3. Add `#shorts` tag
4. YouTube will automatically categorize it as a Short

---

## Twitter/X Integration

### 1. Create Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Apply for developer access
3. Complete application (may take 1-3 days for approval)

### 2. Create App

1. Navigate to **Apps** → **Create App**
2. Fill in app details:
   - **App Name**: SupoClip
   - **Description**: AI-powered video clipping tool
   - **Website URL**: https://yourdomain.com

### 3. Configure OAuth 2.0

1. Go to your app's **Settings**
2. Enable **OAuth 2.0**
3. Set **Type of App**: Web App
4. Add **Callback URI**: `https://yourdomain.com/api/social/callback/twitter`

### 4. Get Permissions

Select these scopes:
- `tweet.read`
- `tweet.write`
- `users.read`
- `offline.access` (for refresh tokens)

### 5. Get Credentials

- **Client ID**
- **Client Secret**

### 6. Environment Variables

```bash
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
TWITTER_REDIRECT_URI=https://yourdomain.com/api/social/callback/twitter
```

### Twitter API Specifics

- **Video Requirements**:
  - Format: MP4
  - Max size: 512 MB
  - Max duration: 2 minutes 20 seconds
  - Min duration: 0.5 seconds
  - Aspect ratio: Any (9:16 recommended for vertical)

- **Tweet Limits**: 280 characters
- **Upload Process**: 3-step chunked upload (INIT → APPEND → FINALIZE)
- **Processing Time**: Can take 1-5 minutes for longer videos

### Example Twitter Config

```json
{
  "media_category": "tweet_video"
}
```

---

## Environment Configuration

### Complete `.env` File

Create `/home/user/supoclip/backend/.env` with all credentials:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/supoclip

# Redis
REDIS_URL=redis://localhost:6379

# TikTok
TIKTOK_CLIENT_ID=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_REDIRECT_URI=https://yourdomain.com/api/social/callback/tiktok

# Instagram (Meta)
INSTAGRAM_CLIENT_ID=your_instagram_app_id
INSTAGRAM_CLIENT_SECRET=your_instagram_app_secret
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/api/social/callback/instagram

# YouTube
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REDIRECT_URI=https://yourdomain.com/api/social/callback/youtube

# Twitter/X
TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
TWITTER_REDIRECT_URI=https://yourdomain.com/api/social/callback/twitter

# Other
TEMP_DIR=/tmp
LLM=openai:gpt-4
OPENAI_API_KEY=your_openai_key
```

---

## API Usage

### 1. Connect Platform

**GET** `/social/connect/{platform}`

```bash
curl -X GET "http://localhost:8000/social/connect/tiktok" \
  -H "user_id: user-uuid-here"
```

**Response:**
```json
{
  "authorization_url": "https://www.tiktok.com/v2/auth/authorize/?client_key=...",
  "state": "abc123..."
}
```

**User Flow:**
1. Redirect user to `authorization_url`
2. User authorizes app
3. Platform redirects back to your callback URL with `code` parameter

### 2. Handle OAuth Callback

**POST** `/social/callback/{platform}`

```bash
curl -X POST "http://localhost:8000/social/callback/tiktok" \
  -H "user_id: user-uuid-here" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "authorization_code_from_callback",
    "state": "state_from_connect_request"
  }'
```

**Response:**
```json
{
  "id": "account-uuid",
  "platform": "tiktok",
  "platform_username": "user123",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 3. List Connected Accounts

**GET** `/social/accounts`

```bash
curl -X GET "http://localhost:8000/social/accounts" \
  -H "user_id: user-uuid-here"
```

### 4. Post Immediately

**POST** `/social/post`

```bash
curl -X POST "http://localhost:8000/social/post" \
  -H "user_id: user-uuid-here" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "clip-uuid",
    "platforms": ["tiktok", "instagram", "youtube", "twitter"],
    "caption": "Check out this amazing clip!",
    "hashtags": ["viral", "trending", "supoclip"],
    "platform_config": {
      "tiktok": {
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "disable_duet": false
      },
      "instagram": {
        "share_to_feed": true,
        "video_url": "https://cdn.example.com/clips/video.mp4"
      },
      "youtube": {
        "title": "Amazing Short Video",
        "privacy_status": "public",
        "is_short": true
      }
    }
  }'
```

### 5. Schedule Post

Same as posting immediately, but include `scheduled_for`:

```json
{
  "clip_id": "clip-uuid",
  "platforms": ["tiktok", "youtube"],
  "caption": "Check out this clip!",
  "hashtags": ["viral"],
  "scheduled_for": "2024-01-20T15:00:00Z"
}
```

### 6. List Scheduled Posts

**GET** `/social/scheduled`

```bash
curl -X GET "http://localhost:8000/social/scheduled?status=scheduled&limit=50" \
  -H "user_id: user-uuid-here"
```

### 7. Get Post Details

**GET** `/social/scheduled/{post_id}`

```bash
curl -X GET "http://localhost:8000/social/scheduled/{post_id}" \
  -H "user_id: user-uuid-here"
```

### 8. Get Post Attempts (for debugging)

**GET** `/social/scheduled/{post_id}/attempts`

```bash
curl -X GET "http://localhost:8000/social/scheduled/{post_id}/attempts" \
  -H "user_id: user-uuid-here"
```

**Response:**
```json
[
  {
    "id": "attempt-uuid",
    "platform": "tiktok",
    "attempt_number": 1,
    "status": "success",
    "platform_post_id": "7123456789",
    "platform_url": "https://www.tiktok.com/@user/video/7123456789",
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "attempt-uuid-2",
    "platform": "instagram",
    "attempt_number": 2,
    "status": "failed",
    "error_message": "Video processing timeout",
    "created_at": "2024-01-15T10:35:00Z"
  }
]
```

### 9. Cancel Scheduled Post

**DELETE** `/social/scheduled/{post_id}`

```bash
curl -X DELETE "http://localhost:8000/social/scheduled/{post_id}" \
  -H "user_id: user-uuid-here"
```

---

## Scheduler Setup

### Running the Scheduler

The scheduler can be run in two ways:

#### Option 1: Integrated with Main App (Development)

The scheduler starts automatically when the FastAPI app starts. No additional setup needed.

#### Option 2: Standalone Worker (Production)

Run the scheduler as a separate process/container:

```bash
cd /home/user/supoclip/backend
python -m src.integrations.scheduler
```

Or with Docker:

```dockerfile
# Dockerfile.scheduler
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "-m", "src.integrations.scheduler"]
```

### Docker Compose

Add scheduler service to `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile.scheduler
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/supoclip
      - REDIS_URL=redis://redis:6379
      - TIKTOK_CLIENT_ID=${TIKTOK_CLIENT_ID}
      - TIKTOK_CLIENT_SECRET=${TIKTOK_CLIENT_SECRET}
      # ... other env vars ...
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
```

### Scheduler Jobs

The scheduler runs these jobs:

1. **Process Due Posts** (every 1 minute)
   - Finds posts scheduled for now or earlier
   - Adds them to Redis queue
   - Processes queue

2. **Retry Failed Posts** (every 5 minutes)
   - Finds failed attempts eligible for retry
   - Uses exponential backoff
   - Max retries: 3 (configurable)

3. **Cleanup Old Posts** (daily at 2 AM)
   - Removes completed/cancelled posts older than 30 days

### Monitoring Queue Status

Check queue status via API (add this endpoint if needed):

```python
@router.get("/queue/status")
async def get_queue_status():
    status = await scheduler.get_queue_status()
    return status
```

---

## Troubleshooting

### Common Issues

#### 1. "Integration not configured" Error

**Problem**: OAuth credentials not set in environment variables.

**Solution**: Ensure all required environment variables are set:
```bash
echo $TIKTOK_CLIENT_ID  # Should print your client ID
```

#### 2. "Token expired" Error

**Problem**: Access token expired and refresh token not available.

**Solution**:
- User needs to reconnect their account
- Ensure `offline_access` scope is requested (YouTube, Twitter)

#### 3. "Video processing timeout" (Instagram)

**Problem**: Instagram couldn't fetch video from URL.

**Solution**:
- Ensure video is publicly accessible via HTTPS
- Check video meets Instagram requirements (max 100MB, 90s)
- Use CDN or cloud storage with public access

#### 4. "Upload failed" (TikTok)

**Problem**: Video doesn't meet TikTok requirements.

**Solution**:
- Check video format (MP4)
- Verify resolution (minimum 540x960)
- Ensure duration is 3s - 10min

#### 5. Posts Not Being Processed

**Problem**: Scheduler not running or Redis connection issues.

**Solution**:
```bash
# Check Redis connection
redis-cli ping  # Should return "PONG"

# Check scheduler logs
docker logs supoclip-scheduler
```

#### 6. "Invalid redirect URI" Error

**Problem**: Callback URL doesn't match registered URI.

**Solution**:
- Ensure redirect URI in environment matches platform settings
- Include protocol (https://)
- No trailing slashes

### Testing OAuth Flows

Use ngrok for local testing:

```bash
ngrok http 8000
```

Update redirect URIs to:
```
https://your-ngrok-url.ngrok.io/api/social/callback/{platform}
```

### Database Queries for Debugging

```sql
-- Check connected accounts
SELECT * FROM social_media_accounts WHERE user_id = 'your-user-id';

-- Check scheduled posts
SELECT * FROM scheduled_posts WHERE user_id = 'your-user-id' ORDER BY created_at DESC;

-- Check failed attempts
SELECT * FROM post_attempts WHERE status = 'failed' ORDER BY created_at DESC;

-- Check posts awaiting retry
SELECT * FROM post_attempts
WHERE status = 'failed'
  AND next_retry_at IS NOT NULL
  AND next_retry_at > NOW();
```

### Logging

Enable debug logging:

```python
# In backend/src/integrations/social_media.py
logging.basicConfig(level=logging.DEBUG)
```

Check logs:
```bash
# Backend logs
tail -f logs/backend.log

# Docker logs
docker logs -f supoclip-backend
docker logs -f supoclip-scheduler
```

---

## Rate Limits

### Platform Limits

| Platform  | Rate Limit                | Notes                          |
|-----------|---------------------------|--------------------------------|
| TikTok    | 100 videos/day per user   | Resets daily at midnight UTC   |
| Instagram | 25 posts/day per user     | Business account limits        |
| YouTube   | 10,000 units/day          | Upload = 1,600 units           |
| Twitter   | 300 tweets/3 hours        | Includes video tweets          |

### Handling Rate Limits

The system automatically:
- Detects rate limit errors
- Schedules retry after rate limit resets
- Returns appropriate error messages

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all sensitive data
3. **Encrypt tokens** at rest (optional, but recommended for production)
4. **Use HTTPS** for all callback URLs
5. **Validate OAuth state** parameter to prevent CSRF
6. **Rotate secrets** periodically
7. **Monitor failed attempts** for suspicious activity

---

## Next Steps

1. **Set up OAuth apps** for each platform
2. **Configure environment variables**
3. **Run database migration** to create tables
4. **Start scheduler** worker
5. **Test OAuth flows** with ngrok
6. **Deploy to production** with proper SSL certificates
7. **Monitor logs** and queue status

---

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/yourusername/supoclip/issues
- **Documentation**: https://supoclip.com/docs
- **Email**: support@supoclip.com

---

## API Reference Summary

| Endpoint                           | Method | Description                  |
|------------------------------------|--------|------------------------------|
| `/social/connect/{platform}`       | GET    | Get OAuth authorization URL  |
| `/social/callback/{platform}`      | POST   | Handle OAuth callback        |
| `/social/accounts`                 | GET    | List connected accounts      |
| `/social/accounts/{account_id}`    | DELETE | Disconnect account           |
| `/social/post`                     | POST   | Post or schedule clip        |
| `/social/scheduled`                | GET    | List scheduled posts         |
| `/social/scheduled/{post_id}`      | GET    | Get post details             |
| `/social/scheduled/{post_id}`      | DELETE | Cancel scheduled post        |
| `/social/scheduled/{post_id}/attempts` | GET | Get post attempts (debug) |

---

## License

MIT License - See LICENSE file for details.

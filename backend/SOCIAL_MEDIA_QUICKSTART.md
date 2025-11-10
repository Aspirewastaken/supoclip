# Social Media Integration - Quick Start Guide

Get your social media posting system up and running in minutes.

## Prerequisites

- SupoClip backend running
- PostgreSQL database
- Redis server
- OAuth credentials for desired platforms

## 1. Database Setup

Run the migration to create social media tables:

```bash
cd /home/user/supoclip

# Apply migration (if using Alembic)
# alembic upgrade head

# OR manually run SQL
psql -U supoclip -d supoclip -f migrations/002_social_media_integrations.sql
```

## 2. Configure Environment Variables

Edit `/home/user/supoclip/backend/.env`:

```bash
# Redis (required)
REDIS_URL=redis://localhost:6379

# TikTok (optional - only if using TikTok)
TIKTOK_CLIENT_ID=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_REDIRECT_URI=https://yourdomain.com/api/social/callback/tiktok

# Instagram (optional - only if using Instagram)
INSTAGRAM_CLIENT_ID=your_app_id
INSTAGRAM_CLIENT_SECRET=your_app_secret
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/api/social/callback/instagram

# YouTube (optional - only if using YouTube)
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=https://yourdomain.com/api/social/callback/youtube

# Twitter (optional - only if using Twitter)
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
TWITTER_REDIRECT_URI=https://yourdomain.com/api/social/callback/twitter
```

## 3. Install Dependencies

```bash
cd /home/user/supoclip/backend

# Install with uv
uv sync

# OR with pip
pip install apscheduler
```

## 4. Start Services

### Option A: All-in-One (Development)

The scheduler starts automatically with the backend:

```bash
cd /home/user/supoclip/backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Separate Processes (Production)

**Terminal 1 - Backend:**
```bash
cd /home/user/supoclip/backend
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Scheduler:**
```bash
cd /home/user/supoclip/backend
python -m src.integrations.scheduler
```

### Option C: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  scheduler:
    build:
      context: ./backend
    command: python -m src.integrations.scheduler
    environment:
      - DATABASE_URL=postgresql://supoclip:supoclip_password@postgres:5432/supoclip
      - REDIS_URL=redis://redis:6379
      - TIKTOK_CLIENT_ID=${TIKTOK_CLIENT_ID}
      - TIKTOK_CLIENT_SECRET=${TIKTOK_CLIENT_SECRET}
      # ... other env vars ...
    depends_on:
      - postgres
      - redis
```

Start all services:
```bash
docker-compose up -d
```

## 5. Test the Integration

### Connect a Platform

```bash
# Get authorization URL
curl -X GET "http://localhost:8000/social/connect/tiktok" \
  -H "user_id: test-user-id"

# Response will include authorization_url
# Visit that URL in browser to authorize
```

### Post a Clip Immediately

```bash
curl -X POST "http://localhost:8000/social/post" \
  -H "user_id: test-user-id" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "your-clip-id",
    "platforms": ["tiktok"],
    "caption": "Test post from SupoClip!",
    "hashtags": ["test", "supoclip"]
  }'
```

### Schedule a Post

```bash
curl -X POST "http://localhost:8000/social/post" \
  -H "user_id: test-user-id" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "your-clip-id",
    "platforms": ["tiktok", "youtube"],
    "caption": "Scheduled post!",
    "hashtags": ["scheduled"],
    "scheduled_for": "2024-01-20T15:00:00Z"
  }'
```

### List Scheduled Posts

```bash
curl -X GET "http://localhost:8000/social/scheduled?status=scheduled" \
  -H "user_id: test-user-id"
```

## 6. Verify Scheduler is Running

Check logs:

```bash
# If running via uvicorn
# Look for: "✅ Social media scheduler started successfully"

# If running via Docker
docker logs supoclip-scheduler

# Should see:
# 🚀 Starting social media scheduler worker...
# ✅ Social media scheduler started successfully
```

## Troubleshooting

### Scheduler not processing posts

**Check Redis connection:**
```bash
redis-cli ping
# Should return: PONG
```

**Check scheduled posts in database:**
```sql
SELECT * FROM scheduled_posts WHERE status = 'scheduled' AND scheduled_for <= NOW();
```

### OAuth callback not working

**For local development, use ngrok:**
```bash
ngrok http 8000
```

Update redirect URIs to use ngrok URL:
```
https://abc123.ngrok.io/api/social/callback/tiktok
```

### Posts failing

**Check attempt logs:**
```bash
curl -X GET "http://localhost:8000/social/scheduled/{post_id}/attempts" \
  -H "user_id: test-user-id"
```

**Check database:**
```sql
SELECT * FROM post_attempts WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;
```

## Platform-Specific Setup

### TikTok
1. Go to https://developers.tiktok.com/
2. Create app → Select "Login Kit" and "Content Posting API"
3. Add scopes: `user.info.basic`, `video.upload`, `video.publish`

### Instagram
1. Go to https://developers.facebook.com/
2. Create Business app
3. Add Instagram product
4. **Important**: Instagram account must be Business/Creator account connected to Facebook Page
5. Video must be hosted at public URL (use S3/R2)

### YouTube
1. Go to https://console.cloud.google.com/
2. Create project → Enable YouTube Data API v3
3. Create OAuth credentials → Add authorized redirect URIs
4. Videos ≤60s with 9:16 ratio appear as Shorts

### Twitter/X
1. Go to https://developer.twitter.com/
2. Create app → Enable OAuth 2.0
3. Add scopes: `tweet.read`, `tweet.write`, `users.read`, `offline.access`

## Next Steps

1. ✅ Database migration applied
2. ✅ Environment variables configured
3. ✅ Services running
4. ✅ Test connection successful
5. ⏭️ Set up platform OAuth apps
6. ⏭️ Deploy to production
7. ⏭️ Monitor logs and metrics

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/social/connect/{platform}` | GET | Get OAuth URL |
| `/social/callback/{platform}` | POST | Handle OAuth callback |
| `/social/accounts` | GET | List connected accounts |
| `/social/post` | POST | Post or schedule clip |
| `/social/scheduled` | GET | List scheduled posts |
| `/social/scheduled/{id}` | GET | Get post details |
| `/social/scheduled/{id}/attempts` | GET | Get posting attempts |
| `/social/scheduled/{id}` | DELETE | Cancel post |

## Support

- Full documentation: `/home/user/supoclip/SOCIAL_MEDIA_INTEGRATION_GUIDE.md`
- API docs: http://localhost:8000/docs
- Issues: https://github.com/yourusername/supoclip/issues

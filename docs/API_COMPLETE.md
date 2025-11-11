# SupoClip API Documentation - Complete Reference

**Version**: 1.0.0 (Extended)
**Base URL**: `http://localhost:8000` (Development) | `https://api.supoclip.com` (Production)
**Last Updated**: 2025-11-10

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Codes](#error-codes)
5. [Core Endpoints](#core-endpoints)
   - [Video Processing](#video-processing)
   - [Task Management](#task-management)
   - [Mass Generation](#mass-generation)
6. [AI & Intelligence](#ai--intelligence)
   - [AI Title Generation](#ai-title-generation)
   - [Posting Helper](#posting-helper)
   - [Thumbnails](#thumbnails)
7. [Analytics & Metrics](#analytics--metrics)
   - [Analytics](#analytics)
   - [Experiments (A/B Testing)](#experiments-ab-testing)
8. [Content Management](#content-management)
   - [Watermarks](#watermarks)
   - [Resources](#resources)
9. [Integrations](#integrations)
   - [Calendar Scheduling](#calendar-scheduling)
   - [Social Media](#social-media)
   - [Webhooks](#webhooks)
10. [System & Admin](#system--admin)
    - [Quota Management](#quota-management)
    - [Billing](#billing)
    - [Performance Monitoring](#performance-monitoring)
11. [Code Examples](#code-examples)
12. [Migration Guide](#migration-guide)

---

## Overview

SupoClip API is an AI-powered video clipping service that transforms long-form content into viral short clips.

### Key Features

- **🎬 Video Processing**: Automatic clipping with AI-powered segment selection
- **🤖 5-Model AI Council**: Advanced clip selection using multiple LLMs
- **📊 Matrix Generation**: Create variations with different styles and formats
- **🎨 Customization**: Fonts, subtitles, transitions, watermarks
- **📈 Analytics**: Track performance across platforms
- **📅 Scheduling**: Calendar and social media integration
- **🔬 A/B Testing**: Experiment with clip variations
- **🎯 Smart Thumbnails**: AI-powered thumbnail generation

---

## NEW FEATURES (Not in Original Docs)

### Mass Generation with AI Council

Generate hundreds of clips using a 5-model AI council system:
- Adaptive targeting (50/250/500 clips based on video duration)
- 5 AI models: Claude Sonnet, Claude Opus, GPT-4, Gemini, DeepSeek
- Democratic voting on best clips
- Matrix processing with temporal and canvas variations

### Quota Management

Per-user quota system with three tiers:
- **Free**: 10 clips/month
- **Pro**: 500 clips/month
- **Admin**: Unlimited

### A/B Testing (Experiments)

Statistical testing framework for clip variations:
- Chi-square and t-tests
- Bayesian analysis
- Auto winner declaration
- Confidence thresholds

### Smart Thumbnails

AI-powered thumbnail generation with:
- Face detection and tracking
- Motion analysis
- Multiple style variations
- AI scoring for virality

### Performance Monitoring

Real-time system monitoring with:
- GPU acceleration detection
- Worker autoscaling
- Cache management
- Health checks

---

## Authentication

**Method**: Header-based (user_id)

```http
user_id: your-user-uuid
```

⚠️ **Security Note**: Current implementation is trust-based. JWT authentication coming soon.

---

## Rate Limiting

| Endpoint Category | Rate Limit |
|------------------|------------|
| Video Processing | 10 req/hour |
| Mass Generation | 5 req/hour |
| AI Operations | 50 req/hour |
| Analytics | 100 req/min |
| Other | 100 req/min |

⚠️ **Note**: Rate limiting is not currently enforced but will be in production.

---

## Error Codes

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message",
  "error_code": "OPTIONAL_CODE",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

# Core Endpoints

## Video Processing

### POST /start

Process video synchronously. Returns results immediately.

**Request:**
```json
{
  "source": {
    "url": "https://youtube.com/watch?v=..."
  },
  "font_options": {
    "font_family": "TikTokSans-Regular",
    "font_size": 24,
    "font_color": "#FFFFFF"
  }
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "relevant_segments": [...],
  "clips": [...],
  "summary": "Video summary",
  "key_topics": ["topic1", "topic2"]
}
```

---

### POST /start-with-progress

Process video asynchronously with SSE progress updates.

**Request:** Same as /start

**Response:**
```json
{
  "task_id": "uuid",
  "message": "Task started"
}
```

**Progress Tracking:** Use `GET /tasks/{task_id}/progress` for SSE updates.

---

### POST /upload

Upload video file for processing.

**Request:** Multipart form data

```bash
curl -F "video=@video.mp4" http://localhost:8000/upload
```

**Response:**
```json
{
  "message": "Video uploaded",
  "video_path": "/tmp/uploads/uuid.mp4"
}
```

---

## Task Management

### GET /tasks/

List all tasks for authenticated user.

**Query Parameters:**
- `limit` (int): Max results (default: 50)

**Response:**
```json
{
  "tasks": [{
    "id": "uuid",
    "source_title": "Title",
    "status": "completed",
    "clips_count": 5,
    "created_at": "ISO-8601"
  }],
  "total": 1
}
```

---

### POST /tasks/

Create new task.

**Request:**
```json
{
  "source": {"url": "..."},
  "font_options": {...}
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "job_id": "job-uuid",
  "message": "Task created"
}
```

---

### GET /tasks/{task_id}

Get task details.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "source_title": "Title",
  "status": "completed",
  "clips_count": 5,
  "font_family": "TikTokSans-Regular",
  "created_at": "ISO-8601"
}
```

---

### GET /tasks/{task_id}/clips

Get all clips for task.

**Response:**
```json
{
  "task_id": "uuid",
  "clips": [{
    "id": "uuid",
    "filename": "clip.mp4",
    "video_url": "/clips/clip.mp4",
    "duration": 15.0,
    "relevance_score": 95
  }],
  "total_clips": 5
}
```

---

### GET /tasks/{task_id}/progress

Server-Sent Events stream for real-time progress.

**SSE Events:**
```
event: progress
data: {"progress": 50, "message": "Processing..."}

event: close
data: {"status": "completed"}
```

---

### PATCH /tasks/{task_id}

Update task (title).

**Request:**
```json
{
  "title": "New Title"
}
```

---

### DELETE /tasks/{task_id}

Delete task and all clips.

---

### DELETE /tasks/{task_id}/clips/{clip_id}

Delete specific clip.

---

## Mass Generation

### POST /mass/generate

Start mass clip generation with 5-model AI council.

**Request:**
```json
{
  "uploaded_file_path": "/app/uploads/video.mp4",
  "source_type": "upload",
  "user_notes": "Focus on emotional moments"
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "job_id": "uuid",
  "message": "Mass generation started",
  "info": "Adaptive targeting: 50/250/500 clips"
}
```

**Features:**
- AI Council with 5 models (Sonnet, Opus, GPT-4, Gemini, DeepSeek)
- Adaptive clip targeting based on video duration:
  - Short (< 10 min): 50 clips
  - Medium (10-30 min): 250 clips
  - Long (> 30 min): 500 clips
- Democratic voting on segment selection

---

### POST /mass/generate-matrix

Full matrix generation with all variations.

**Request:**
```json
{
  "uploaded_file_path": "/app/uploads/video.mp4",
  "source_type": "upload",
  "user_notes": "...",
  "matrix_options": {
    "enable_watermark": true,
    "enable_title_card": true,
    "enable_music": true,
    "enable_captions": true,
    "title_style": "tt3",
    "canvas_styles": ["original", "flipped", "blurry_bg"]
  }
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "job_id": "uuid",
  "message": "Full matrix generation started",
  "info": "Creates 9 variations per clip (3 temporal × 3 canvas)"
}
```

**Matrix Variations:**
- **Temporal**: Normal speed, Fast (1.2x), Very fast (1.5x)
- **Canvas**: Original, Flipped, Blurry background
- **Effects**: Watermarks, title cards, music, captions

---

### GET /mass/status/{task_id}

Get mass generation status.

**Response:**
```json
{
  "task_id": "uuid",
  "status": "processing",
  "progress": 45,
  "message": "Generating clips...",
  "clips_generated": 150
}
```

---

### GET /mass/status/{task_id}/stream

SSE stream for real-time progress.

**JavaScript Example:**
```javascript
const eventSource = new EventSource('/mass/status/task-id/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.progress, data.message);
};
```

---

### GET /mass/list

List all mass generation tasks.

**Query Parameters:**
- `limit` (int): Max results (default: 50)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "tasks": [{
    "id": "uuid",
    "status": "completed",
    "source_title": "Title",
    "clips_count": 250,
    "created_at": "ISO-8601"
  }],
  "total": 10
}
```

---

# AI & Intelligence

## AI Title Generation

### POST /ai/generate-titles

Generate viral titles using multiple AI models.

**Request:**
```json
{
  "transcript_text": "In this clip...",
  "platform": "tiktok",
  "target_audience": "young entrepreneurs",
  "num_variations": 10,
  "include_styles": ["question", "shocking"]
}
```

**Response:**
```json
{
  "titles": [{
    "text": "The Secret Nobody Tells You",
    "virality_score": 95,
    "style": "curiosity",
    "character_count": 30
  }],
  "best_title": {...},
  "platform": "tiktok",
  "total_generated": 10
}
```

---

### POST /ai/generate-titles/clip/{clip_id}

Generate titles for existing clip.

**Query Parameters:**
- `platform` (string): tiktok, instagram, youtube, twitter, linkedin
- `num_variations` (int): 3-15 (default: 8)

---

### POST /ai/generate-titles/batch

Batch title generation for multiple clips.

**Request:**
```json
{
  "clip_ids": ["uuid1", "uuid2"],
  "platform": "youtube",
  "num_variations": 5
}
```

**Response:**
```json
{
  "results": {
    "uuid1": {
      "titles": [...]
    }
  },
  "total_clips": 2,
  "successful": 2,
  "failed": 0
}
```

---

### GET /ai/title-styles

Get available title styles.

**Response:**
```json
{
  "styles": {
    "question": {
      "name": "Question",
      "description": "Creates curiosity",
      "example": "Why Are People Obsessed?"
    },
    "shocking": {...},
    "how_to": {...}
  },
  "total": 8
}
```

**Available Styles:**
- question, shocking, how_to, listicle
- story, direct, curiosity, emotional

---

### GET /ai/platforms

Get supported platforms with character limits.

**Response:**
```json
{
  "platforms": {
    "tiktok": {
      "name": "TikTok",
      "character_limit": 150,
      "style": "Casual, trendy",
      "optimal_length": "50-100 characters"
    }
  }
}
```

---

## Posting Helper

### POST /posting/analyze-screenshot

Analyze screenshot with vision AI.

**Request:** Multipart form data

```bash
curl -F "file=@screenshot.png" /posting/analyze-screenshot
```

**Response:**
```json
{
  "account_type": "fitness",
  "platform": "tiktok",
  "suggestions": {
    "title": "Transform Your Body",
    "hashtags": ["#fitness", "#workout"],
    "description": "..."
  }
}
```

---

### POST /posting/generate-content

Generate platform content without screenshot.

**Query Parameters:**
- `platform`: tiktok, instagram, youtube_shorts
- `video_title`: Optional title
- `video_description`: Optional description

**Response:**
```json
{
  "platform": "tiktok",
  "content": {
    "title": "...",
    "hashtags": [...],
    "description": "..."
  }
}
```

---

## Thumbnails

### POST /thumbnails/generate

Generate thumbnails from video.

**Request:**
```json
{
  "video_path": "/tmp/video.mp4",
  "text": "AMAZING RESULT!",
  "methods": ["face_closeup", "high_motion"],
  "styles": ["youtube_premium", "bold_yellow"],
  "sizes": [
    {"width": 1080, "height": 1920},
    {"width": 1280, "height": 720}
  ],
  "enable_ai_scoring": true,
  "video_title": "My Video",
  "return_format": "base64"
}
```

**Response:**
```json
{
  "success": true,
  "thumbnails": [{
    "id": "thumb_0",
    "method": "face_closeup",
    "style": "YouTube Premium",
    "timestamp": 15.5,
    "score": 95.3,
    "size": {"width": 1080, "height": 1920},
    "image_data": "base64...",
    "metadata": {}
  }],
  "total_generated": 12,
  "best_thumbnail": {...},
  "generation_time_seconds": 3.5
}
```

**Extraction Methods:**
- `face_closeup`: Largest, most centered face
- `high_motion`: Highest action frame
- `first_frame`, `middle_frame`, `last_frame`
- `best_composition`: Best quality frame

**Styles:**
- YouTube Premium, MrBeast Style, Bold Yellow
- TikTok Style, Instagram Modern, Clean Minimal

---

### GET /thumbnails/styles

Get available thumbnail styles.

**Query Parameters:**
- `position`: top, middle, bottom
- `with_glow`: true/false
- `with_background`: true/false
- `popular_only`: true/false

**Response:**
```json
{
  "styles": [{
    "name": "YouTube Premium",
    "font_size": 76,
    "font_color": "#FFFFFF",
    "stroke_width": 6,
    "position": "middle",
    "has_shadow": true
  }],
  "total": 10
}
```

---

### GET /thumbnails/methods

Get extraction methods with descriptions.

**Response:**
```json
{
  "methods": [{
    "value": "face_closeup",
    "name": "Face Closeup",
    "description": "Extracts frame with largest face"
  }],
  "total": 6
}
```

---

### GET /thumbnails/preview

Preview thumbnail style without video.

**Query Parameters:**
- `style_name`: Style to preview
- `text`: Text to overlay (default: "Preview Text")

**Response:** JPEG image

---

# Analytics & Metrics

## Analytics

### POST /analytics/record

Record metrics for a clip.

**Request:**
```json
{
  "view_metrics": {
    "clip_id": "uuid",
    "platform": "tiktok",
    "views": 10000,
    "likes": 1500,
    "comments": 200,
    "shares": 300,
    "date": "2025-11-10"
  },
  "performance_metrics": {
    "clip_id": "uuid",
    "engagement_rate": 15.5,
    "watch_time": 12.3,
    "retention_rate": 85.0
  }
}
```

**Response (201):**
```json
{
  "message": "Metrics recorded",
  "results": {
    "view_metrics": {
      "status": "created",
      "id": "uuid"
    },
    "performance_metrics": {
      "status": "created",
      "id": "uuid"
    }
  }
}
```

---

### GET /analytics/clip/{clip_id}

Get comprehensive clip performance.

**Response:**
```json
{
  "clip_id": "uuid",
  "total_views": 15000,
  "total_likes": 2000,
  "avg_engagement_rate": 18.3,
  "platforms": ["tiktok", "instagram"],
  "view_metrics_by_platform": {
    "tiktok": {
      "views": 10000,
      "likes": 1500,
      "date": "2025-11-10"
    }
  }
}
```

---

### GET /analytics/dashboard

Aggregated analytics dashboard.

**Query Parameters:**
- `user_id`: Filter by user
- `task_id`: Filter by task
- `limit`: Number of top clips (default: 10)

**Response:**
```json
{
  "total_clips": 25,
  "total_views": 150000,
  "avg_engagement_rate": 18.3,
  "top_performing_clips": [{
    "clip_id": "uuid",
    "total_views": 50000,
    "engagement_rate": 22.4
  }],
  "platform_breakdown": {
    "tiktok": {
      "clips_count": 15,
      "total_views": 100000
    }
  }
}
```

---

## Experiments (A/B Testing)

### POST /experiments/create

Create A/B test experiment.

**Request:**
```json
{
  "name": "Font Style Test",
  "description": "TikTok Sans vs Arial Bold",
  "variations": [
    {
      "clip_id": "uuid1",
      "variation_name": "TikTok Sans"
    },
    {
      "clip_id": "uuid2",
      "variation_name": "Arial Bold"
    }
  ],
  "confidence_threshold": 0.95
}
```

**Response (201):**
```json
{
  "experiment_id": "uuid",
  "message": "Experiment created",
  "variations": [...]
}
```

---

### GET /experiments/

List all experiments for user.

**Response:**
```json
{
  "experiments": [{
    "id": "uuid",
    "name": "Font Style Test",
    "status": "running",
    "winner_variation_id": null,
    "started_at": "ISO-8601"
  }],
  "total": 1
}
```

---

### GET /experiments/{experiment_id}

Get experiment details.

**Response:**
```json
{
  "id": "uuid",
  "name": "Font Style Test",
  "variations": [...],
  "status": "running",
  "results": [...]
}
```

---

### GET /experiments/{experiment_id}/results

Get statistical analysis.

**Response:**
```json
{
  "experiment_id": "uuid",
  "variations": [{
    "variation_id": "uuid",
    "variation_name": "TikTok Sans",
    "metrics": {
      "views": 10000,
      "clicks": 1500,
      "conversion_rate": 15.0,
      "engagement_rate": 18.5
    }
  }],
  "statistical_tests": [{
    "test_type": "chi_square",
    "p_value": 0.03,
    "is_significant": true,
    "winning_variation": "uuid"
  }],
  "overall_winner": "uuid",
  "overall_confidence": 0.97,
  "should_declare_winner": true,
  "recommendation": "Variation A is statistically better"
}
```

**Statistical Tests:**
- Chi-square test for categorical data
- T-test for continuous metrics
- Bayesian probability calculation

---

### POST /experiments/{experiment_id}/declare-winner

Manually declare winner.

**Request:**
```json
{
  "winner_variation_id": "uuid"
}
```

---

### POST /experiments/{experiment_id}/update-metrics

Update variation metrics.

**Request:**
```json
{
  "variation_id": "uuid",
  "metrics": {
    "views": 10000,
    "clicks": 1500,
    "conversions": 300
  }
}
```

---

### POST /experiments/{experiment_id}/pause

Pause running experiment.

---

### POST /experiments/{experiment_id}/resume

Resume paused experiment.

---

# Content Management

## Watermarks

### POST /watermarks/upload

Upload watermark video.

**Request:** Multipart form data

```bash
curl -F "account_id=my_account" -F "watermark=@watermark.mp4" /watermarks/upload
```

**Response:**
```json
{
  "message": "Watermark uploaded",
  "account_id": "my_account",
  "filename": "my_account.mp4",
  "video_info": {
    "format": "mp4",
    "codec": "h264",
    "duration": 2.5,
    "width": 1080,
    "height": 1920
  },
  "green_screen": {
    "has_green_screen": true,
    "confidence": 0.85
  }
}
```

**Features:**
- MP4 format validation
- Green screen detection
- Minimum resolution: 100x100
- Minimum duration: 0.1s

---

### GET /watermarks/

List all watermarks.

**Response:**
```json
{
  "watermarks": [{
    "account_id": "default",
    "filename": "default.mp4",
    "file_size_mb": 1.0,
    "is_default": true,
    "video_info": {...}
  }],
  "total": 1
}
```

---

### GET /watermarks/{account_id}

Download watermark file.

**Response:** MP4 video file

Falls back to default.mp4 if account-specific not found.

---

### DELETE /watermarks/{account_id}

Delete watermark.

Cannot delete default.mp4.

---

### PUT /watermarks/{account_id}/metadata

Update watermark settings.

**Request:**
```json
{
  "position": "bottom_right",
  "scale": 0.15,
  "opacity": 1.0
}
```

**Position Options:**
- top_left, top_right
- bottom_left, bottom_right
- center

**Scale**: 0.01-1.0 (percentage of video width)
**Opacity**: 0.0-1.0

---

## Resources

### GET /fonts

List available fonts.

**Response:**
```json
{
  "fonts": [{
    "name": "TikTokSans-Regular",
    "display_name": "TikTok Sans Regular",
    "file_path": "/app/fonts/TikTokSans-Regular.ttf"
  }]
}
```

---

### GET /fonts/{font_name}

Download font file.

**Response:** TTF font file

---

### GET /transitions

List transition effects.

**Response:**
```json
{
  "transitions": [{
    "name": "swipe_left",
    "display_name": "Swipe Left",
    "file_path": "/app/transitions/swipe_left.mp4"
  }]
}
```

---

# Integrations

## Calendar Scheduling

### GET /calendar/oauth/google/url

Get Google OAuth authorization URL.

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

---

### POST /calendar/oauth/google/callback

Handle OAuth callback.

**Request:**
```json
{
  "code": "auth_code",
  "state": "user_id"
}
```

---

### POST /calendar/credentials/caldav

Add CalDAV credentials.

**Request:**
```json
{
  "provider": "icloud",
  "username": "user@icloud.com",
  "password": "app-specific-password",
  "calendar_name": "Calendar"
}
```

**Supported Providers:**
- icloud (auto URL)
- caldav (custom URL)
- nextcloud

---

### GET /calendar/credentials

List calendar credentials.

---

### DELETE /calendar/credentials/{credential_id}

Delete credential.

---

### POST /calendar/schedule

Schedule clip posting.

**Request:**
```json
{
  "clip_id": "uuid",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"
}
```

---

### GET /calendar/events

List scheduled posts.

**Query Parameters:**
- `status`: scheduled, published, failed, cancelled
- `start_date`, `end_date`: ISO format
- `limit`: Max results (default: 50)

---

### PATCH /calendar/events/{scheduled_post_id}

Update scheduled post.

**Request:**
```json
{
  "scheduled_time": "2025-11-16T10:00:00Z",
  "status": "cancelled"
}
```

---

### DELETE /calendar/events/{scheduled_post_id}

Cancel scheduled post.

---

## Social Media

### GET /social/connect/{platform}

Get OAuth authorization URL.

**Path Parameters:**
- platform: tiktok, instagram, youtube, twitter

**Response:**
```json
{
  "authorization_url": "https://...",
  "state": "security_token"
}
```

---

### POST /social/callback/{platform}

Handle OAuth callback.

**Request:**
```json
{
  "code": "auth_code",
  "state": "security_token"
}
```

---

### GET /social/accounts

List connected accounts.

**Response:**
```json
{
  "accounts": [{
    "id": "uuid",
    "platform": "tiktok",
    "platform_username": "@username",
    "is_active": true,
    "last_used_at": "ISO-8601"
  }]
}
```

---

### DELETE /social/accounts/{account_id}

Disconnect account.

---

### POST /social/post

Post or schedule clip.

**Request:**
```json
{
  "clip_id": "uuid",
  "platforms": ["tiktok", "instagram"],
  "caption": "Check this out!",
  "hashtags": ["viral", "trending"],
  "scheduled_for": "2025-11-15T10:00:00Z",
  "platform_config": {
    "tiktok": {"privacy": "public"},
    "instagram": {"location": "New York"}
  }
}
```

**Response:**
```json
{
  "post_id": "uuid",
  "status": "scheduled",
  "scheduled_for": "ISO-8601",
  "platforms": ["tiktok", "instagram"]
}
```

---

### GET /social/scheduled

List scheduled posts.

**Query Parameters:**
- `status`: scheduled, posted, failed
- `limit`: Max results (default: 100)
- `offset`: Pagination (default: 0)

---

### GET /social/scheduled/{post_id}

Get scheduled post details.

---

### GET /social/scheduled/{post_id}/attempts

Get posting attempts (for debugging).

**Response:**
```json
{
  "attempts": [{
    "id": "uuid",
    "platform": "tiktok",
    "attempt_number": 1,
    "status": "success",
    "platform_post_id": "tiktok-id",
    "platform_url": "https://tiktok.com/...",
    "created_at": "ISO-8601"
  }]
}
```

---

### DELETE /social/scheduled/{post_id}

Cancel scheduled post.

---

## Webhooks

### POST /webhooks

Create webhook.

**Request:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["task.completed", "clips.ready"],
  "secret": "optional-custom-secret"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "url": "https://example.com/webhook",
  "events": ["task.completed"],
  "secret": "auto-generated-secret",
  "active": true
}
```

**Webhook Payload:**
```json
{
  "event": "task.completed",
  "timestamp": "ISO-8601",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "clips": [...]
  }
}
```

**Security:**
- HMAC-SHA256 signature in `X-Webhook-Signature` header
- Verify signature: `HMAC-SHA256(secret, payload)`

---

### GET /webhooks

List webhooks.

**Query Parameters:**
- `active_only`: true/false (default: true)

---

### GET /webhooks/{webhook_id}

Get webhook details.

---

### PATCH /webhooks/{webhook_id}

Update webhook.

**Request:**
```json
{
  "url": "https://new-url.com/webhook",
  "events": ["task.completed"],
  "active": false
}
```

---

### DELETE /webhooks/{webhook_id}

Delete webhook.

---

### GET /webhooks/events/supported

Get supported events.

**Response:**
```json
{
  "events": ["task.completed", "task.failed", "clips.ready"],
  "descriptions": {
    "task.completed": "When processing completes",
    "task.failed": "When processing fails",
    "clips.ready": "When clips are generated"
  }
}
```

---

# System & Admin

## Quota Management

### GET /quota/check

Check user quota.

**Response:**
```json
{
  "has_quota": true,
  "current_usage": 5,
  "quota_limit": 10,
  "remaining": 5,
  "role": "free",
  "percentage_used": 50.0
}
```

---

### GET /quota/stats

Get usage statistics.

**Response:**
```json
{
  "current_month": {
    "usage": 5,
    "quota": 10,
    "remaining": 5
  },
  "history": [{
    "month": "2025-11",
    "usage": 5,
    "quota": 10
  }]
}
```

---

### GET /quota/limits

Get quota limits for all roles.

**Response:**
```json
{
  "quotas": {
    "free": 10,
    "pro": 500,
    "admin": -1
  },
  "descriptions": {
    "free": "10 clips per month",
    "pro": "500 clips per month",
    "admin": "Unlimited clips"
  }
}
```

---

### POST /quota/admin/update-role

Update user role (admin only).

**Request:**
```json
{
  "role": "pro"
}
```

**Query Parameters:**
- `target_user_id`: User to update

---

### GET /quota/user/{user_id}/info

Get user quota info (admin only).

---

## Billing

⚠️ **Note**: Billing endpoints are currently stubs. Stripe integration in progress.

### GET /billing/pricing

Get pricing plans.

**Response:**
```json
{
  "plans": [{
    "id": "free",
    "name": "Free",
    "price": 0,
    "interval": "month",
    "features": ["10 clips per month", "AI selection"],
    "quota": 10
  }, {
    "id": "pro_monthly",
    "name": "Pro (Monthly)",
    "price": 29,
    "price_id": "price_pro_monthly",
    "quota": 500,
    "recommended": true
  }]
}
```

---

### POST /billing/create-checkout-session

Create Stripe checkout (stub).

**Request:**
```json
{
  "price_id": "price_pro_monthly",
  "success_url": "https://app.com/success",
  "cancel_url": "https://app.com/cancel"
}
```

---

### POST /billing/create-portal-session

Create customer portal (stub).

**Request:**
```json
{
  "return_url": "https://app.com/settings"
}
```

---

### GET /billing/subscription

Get subscription status.

---

### POST /billing/webhook

Stripe webhook handler (stub).

---

### POST /billing/cancel-subscription

Cancel subscription (stub).

---

## Performance Monitoring

### GET /performance/gpu-info

Get GPU acceleration info.

**Response:**
```json
{
  "available": true,
  "name": "NVIDIA GeForce RTX 3080",
  "driver_version": "470.86",
  "cuda_available": true,
  "nvenc_available": true,
  "recommended_encoder": "h264_nvenc"
}
```

---

### GET /performance/system-metrics

Get system resource metrics.

**Response:**
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "memory_available_gb": 8.5,
  "disk_percent": 70.1,
  "disk_free_gb": 150.0
}
```

---

### GET /performance/queue-stats

Get preprocessing queue stats.

**Response:**
```json
{
  "queue_size": 5,
  "active_tasks": 2,
  "max_concurrent_tasks": 4,
  "pending_tasks": 3
}
```

---

### GET /performance/worker-recommendations

Get worker autoscaling recommendations.

**Query Parameters:**
- `avg_processing_time_seconds`: Average time per video (default: 120)

**Response:**
```json
{
  "recommended_workers": 6,
  "current_workers": 4,
  "max_workers": 8,
  "scaling_recommendations": {
    "should_scale_up": true,
    "scale_up_reason": "Queue backlog detected",
    "should_scale_down": false
  }
}
```

---

### GET /performance/cache-stats

Get video cache statistics.

**Response:**
```json
{
  "cache_dir": "/tmp/cache",
  "exists": true,
  "file_count": 150,
  "total_size_mb": 2500
}
```

---

### POST /performance/cache/clear

Clear old cache entries.

**Query Parameters:**
- `max_age_hours`: Max age in hours (default: 24)

---

### GET /performance/metrics/recent

Get recent performance metrics.

**Query Parameters:**
- `limit`: Max metrics (default: 100)

---

### POST /performance/metrics/save

Save metrics to file.

---

### GET /performance/health

Comprehensive health check.

**Response:**
```json
{
  "status": "healthy",
  "warnings": [],
  "system_metrics": {...},
  "queue_stats": {...},
  "gpu_available": true
}
```

---

# Code Examples

## Python - Complete Workflow

```python
import requests
import json
from typing import Dict, List

class SupoClipClient:
    def __init__(self, base_url: str, user_id: str):
        self.base_url = base_url
        self.user_id = user_id
        self.headers = {"user_id": user_id}

    def process_video(self, youtube_url: str) -> Dict:
        """Process video and get clips."""
        response = requests.post(
            f"{self.base_url}/start",
            headers=self.headers,
            json={"source": {"url": youtube_url}}
        )
        return response.json()

    def generate_mass_clips(self, video_path: str, notes: str) -> str:
        """Start mass generation and return task_id."""
        response = requests.post(
            f"{self.base_url}/mass/generate",
            headers=self.headers,
            json={
                "uploaded_file_path": video_path,
                "user_notes": notes
            }
        )
        return response.json()["task_id"]

    def track_progress(self, task_id: str):
        """Track progress via SSE."""
        import sseclient

        url = f"{self.base_url}/mass/status/{task_id}/stream"
        response = requests.get(url, stream=True, headers=self.headers)
        client = sseclient.SSEClient(response)

        for event in client.events():
            data = json.loads(event.data)
            print(f"Progress: {data['progress']}% - {data['message']}")

            if data.get('status') in ['completed', 'error']:
                break

    def generate_titles(self, clip_id: str, platform: str = "tiktok") -> List:
        """Generate titles for clip."""
        response = requests.post(
            f"{self.base_url}/ai/generate-titles/clip/{clip_id}",
            headers=self.headers,
            params={"platform": platform, "num_variations": 10}
        )
        return response.json()["titles"]

    def record_analytics(self, clip_id: str, platform: str, views: int):
        """Record clip performance."""
        response = requests.post(
            f"{self.base_url}/analytics/record",
            headers=self.headers,
            json={
                "view_metrics": {
                    "clip_id": clip_id,
                    "platform": platform,
                    "views": views
                }
            }
        )
        return response.json()

    def create_experiment(self, name: str, clip_ids: List[str]) -> str:
        """Create A/B test."""
        variations = [
            {"clip_id": cid, "variation_name": f"Variation {i+1}"}
            for i, cid in enumerate(clip_ids)
        ]

        response = requests.post(
            f"{self.base_url}/experiments/create",
            headers=self.headers,
            json={
                "name": name,
                "variations": variations
            }
        )
        return response.json()["experiment_id"]

# Usage
client = SupoClipClient("http://localhost:8000", "user-uuid")

# Process video
result = client.process_video("https://youtube.com/watch?v=...")
print(f"Generated {len(result['clips'])} clips")

# Generate mass clips
task_id = client.generate_mass_clips("/tmp/video.mp4", "Focus on emotional moments")
client.track_progress(task_id)

# Generate titles
titles = client.generate_titles(clip_id="clip-uuid", platform="tiktok")
print(f"Best title: {titles[0]['text']}")

# Record analytics
client.record_analytics("clip-uuid", "tiktok", 10000)

# Create A/B test
exp_id = client.create_experiment("Font Test", ["clip1", "clip2"])
```

---

## JavaScript - React Hook

```javascript
import { useState, useEffect } from 'react';

function useSupoClipAPI(baseUrl, userId) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);

  const headers = {
    'user_id': userId,
    'Content-Type': 'application/json'
  };

  // Process video with progress
  const processVideo = async (youtubeUrl) => {
    setLoading(true);

    try {
      // Start processing
      const response = await fetch(`${baseUrl}/start-with-progress`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          source: { url: youtubeUrl }
        })
      });

      const { task_id } = await response.json();

      // Subscribe to progress
      const eventSource = new EventSource(
        `${baseUrl}/tasks/${task_id}/progress`
      );

      return new Promise((resolve, reject) => {
        eventSource.addEventListener('progress', (event) => {
          const data = JSON.parse(event.data);
          console.log(`Progress: ${data.progress}%`);
        });

        eventSource.addEventListener('close', async (event) => {
          eventSource.close();
          setLoading(false);

          if (event.data.status === 'completed') {
            const clipsResponse = await fetch(
              `${baseUrl}/tasks/${task_id}/clips`,
              { headers }
            );
            const { clips } = await clipsResponse.json();
            resolve(clips);
          } else {
            reject(new Error('Processing failed'));
          }
        });
      });
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  // Generate thumbnails
  const generateThumbnails = async (videoPath, text) => {
    const response = await fetch(`${baseUrl}/thumbnails/generate`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        video_path: videoPath,
        text: text,
        methods: ['face_closeup', 'high_motion'],
        styles: ['youtube_premium'],
        enable_ai_scoring: true
      })
    });

    return await response.json();
  };

  // Record analytics
  const recordAnalytics = async (clipId, platform, metrics) => {
    await fetch(`${baseUrl}/analytics/record`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        view_metrics: {
          clip_id: clipId,
          platform: platform,
          ...metrics
        }
      })
    });
  };

  return {
    processVideo,
    generateThumbnails,
    recordAnalytics,
    loading,
    tasks
  };
}

// Usage in component
function VideoProcessor() {
  const api = useSupoClipAPI('http://localhost:8000', 'user-uuid');

  const handleProcess = async () => {
    try {
      const clips = await api.processVideo('https://youtube.com/watch?v=...');
      console.log(`Generated ${clips.length} clips`);
    } catch (error) {
      console.error('Processing failed:', error);
    }
  };

  return (
    <div>
      <button onClick={handleProcess} disabled={api.loading}>
        {api.loading ? 'Processing...' : 'Process Video'}
      </button>
    </div>
  );
}
```

---

## cURL - Quick Reference

```bash
# Process video
curl -X POST http://localhost:8000/start \
  -H "user_id: user-uuid" \
  -H "Content-Type: application/json" \
  -d '{"source": {"url": "https://youtube.com/watch?v=..."}}'

# Generate mass clips
curl -X POST http://localhost:8000/mass/generate \
  -H "user_id: user-uuid" \
  -H "Content-Type: application/json" \
  -d '{"uploaded_file_path": "/tmp/video.mp4", "user_notes": "Focus on action"}'

# Generate thumbnails
curl -X POST http://localhost:8000/thumbnails/generate \
  -H "user_id: user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/tmp/video.mp4",
    "text": "AMAZING!",
    "methods": ["face_closeup"],
    "styles": ["youtube_premium"]
  }'

# Generate titles
curl -X POST http://localhost:8000/ai/generate-titles \
  -H "user_id: user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "In this video...",
    "platform": "tiktok",
    "num_variations": 10
  }'

# Record analytics
curl -X POST http://localhost:8000/analytics/record \
  -H "user_id: user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "view_metrics": {
      "clip_id": "clip-uuid",
      "platform": "tiktok",
      "views": 10000,
      "likes": 1500
    }
  }'

# Create webhook
curl -X POST http://localhost:8000/webhooks \
  -H "X-User-Id: user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "events": ["task.completed"]
  }'

# Check quota
curl http://localhost:8000/quota/check \
  -H "user_id: user-uuid"

# Get system health
curl http://localhost:8000/performance/health
```

---

# Migration Guide

## From v0.x to v1.0

### Breaking Changes

1. **Authentication**
   - Old: No authentication
   - New: Requires `user_id` header

2. **Task Status**
   - Old: Synchronous only
   - New: Supports both sync and async

3. **Clip URLs**
   - Old: File paths only
   - New: CDN URLs with fallback

### New Endpoints

- Mass generation (/mass)
- Quota management (/quota)
- Experiments (/experiments)
- Thumbnails (/thumbnails)
- Performance monitoring (/performance)
- Social media (/social)

### Deprecated

None yet. All v0.x endpoints still supported.

---

## Support

- **Documentation**: https://docs.supoclip.com
- **API Reference**: https://api.supoclip.com/docs
- **GitHub**: https://github.com/supoclip/api
- **Discord**: https://discord.gg/supoclip
- **Email**: support@supoclip.com

---

## Changelog

### v1.0.0 (2025-11-10)

**New Features:**
- Mass generation with 5-model AI council
- Matrix processing with variations
- A/B testing framework
- Smart thumbnail generation
- Performance monitoring
- Quota management
- Webhook support

**Improvements:**
- Enhanced analytics dashboard
- Better error handling
- Comprehensive documentation

**Coming Soon:**
- JWT authentication
- Rate limiting enforcement
- Complete billing integration
- Social media posting (full implementation)

---

## License

MIT License - See LICENSE file for details.

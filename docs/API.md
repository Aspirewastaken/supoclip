# SupoClip API Documentation

**Version**: 1.0.0
**Base URL**: `http://localhost:8000` (Development) | `https://api.supoclip.com` (Production)

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Codes](#error-codes)
5. [Endpoints](#endpoints)
   - [Video Processing](#video-processing)
   - [Task Management](#task-management)
   - [AI Titles](#ai-titles)
   - [Analytics](#analytics)
   - [Calendar Scheduling](#calendar-scheduling)
   - [Watermarks](#watermarks)
   - [Posting Helper](#posting-helper)
   - [Resources](#resources)
6. [Code Examples](#code-examples)
7. [Webhooks](#webhooks)

---

## Overview

SupoClip API is an AI-powered video clipping service that transforms long-form content into viral short clips. The API provides:

- **Intelligent Video Processing**: Automatic transcript generation and AI-powered segment selection
- **9:16 Vertical Format**: Optimized for TikTok, Instagram Reels, and YouTube Shorts
- **Smart Cropping**: Face-detection and intelligent framing
- **Custom Subtitles**: Word-level synchronized captions with custom fonts
- **Analytics Tracking**: Monitor clip performance across platforms
- **Calendar Integration**: Schedule posts to Google Calendar, iCloud, or CalDAV
- **AI Title Generation**: Platform-optimized viral titles using multiple LLMs

---

## Authentication

All endpoints (except `/`, `/docs`, and `/health/db`) require authentication via the `user_id` header.

### Header Format

```
user_id: your-user-uuid
```

### Example Request

```bash
curl -X GET "http://localhost:8000/tasks" \
  -H "user_id: 550e8400-e29b-41d4-a716-446655440000"
```

### Error Response (401 Unauthorized)

```json
{
  "detail": "User authentication required"
}
```

---

## Rate Limiting

Rate limits are enforced per user:

| Endpoint Type | Rate Limit |
|--------------|------------|
| Video Processing (`/start`, `/start-with-progress`, `/upload`) | 10 requests/hour |
| AI Operations (`/ai/*`) | 50 requests/hour |
| Analytics (`/analytics/*`) | 100 requests/minute |
| Other Endpoints | 100 requests/minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1636387200
```

### Rate Limit Error (429)

```json
{
  "detail": "Rate limit exceeded. Try again in 3600 seconds."
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

---

## Endpoints

### Video Processing

#### POST /start

Process a video synchronously and return all clips immediately.

**Authentication**: Required

**Request Body**:
```json
{
  "source": {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  },
  "font_options": {
    "font_family": "TikTokSans-Regular",
    "font_size": 24,
    "font_color": "#FFFFFF"
  }
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source.url | string | Yes | YouTube URL or uploaded file path |
| source.title | string | No | Custom title for uploaded videos |
| font_options.font_family | string | No | Font name (default: "TikTokSans-Regular") |
| font_options.font_size | integer | No | Font size in pixels (default: 24) |
| font_options.font_color | string | No | Font color hex code (default: "#FFFFFF") |

**Response (200 OK)**:
```json
{
  "message": "Task started successfully",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "relevant_segments": [
    {
      "start_time": 10.5,
      "end_time": 25.3,
      "text": "In this moment I reveal the secret to...",
      "relevance_score": 95,
      "reasoning": "Strong hook with valuable insight"
    }
  ],
  "clips": [
    {
      "filename": "clip_1_10.5_25.3.mp4",
      "path": "/tmp/clips/clip_1_10.5_25.3.mp4",
      "start_time": 10.5,
      "end_time": 25.3,
      "duration": 14.8,
      "text": "In this moment I reveal...",
      "relevance_score": 95,
      "reasoning": "Strong hook with valuable insight"
    }
  ],
  "summary": "Video discusses productivity tips and life hacks",
  "key_topics": ["productivity", "time management", "habits"]
}
```

---

#### POST /start-with-progress

Process a video asynchronously with real-time progress updates via Server-Sent Events (SSE).

**Authentication**: Required

**Request Body**: Same as `/start`

**Response (200 OK)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task started successfully"
}
```

**Progress Tracking**: Use GET `/tasks/{task_id}/progress` for SSE updates.

---

#### POST /upload

Upload a video file for processing.

**Authentication**: Required

**Request**: Multipart form data

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "user_id: your-user-id" \
  -F "video=@/path/to/video.mp4"
```

**Response (200 OK)**:
```json
{
  "message": "Video uploaded successfully",
  "video_path": "/tmp/uploads/550e8400-e29b-41d4-a716-446655440000.mp4"
}
```

**Supported Formats**: MP4, MOV, AVI, MKV
**Max File Size**: 500 MB

---

### Task Management

#### GET /tasks

List all tasks for the authenticated user.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 50 | Maximum number of tasks to return |

**Response (200 OK)**:
```json
{
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source_title": "My YouTube Video",
      "source_type": "youtube",
      "status": "completed",
      "clips_count": 5,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T10:15:00Z"
    }
  ],
  "total": 1
}
```

---

#### GET /tasks/{task_id}

Get detailed information about a specific task.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "source_id": "source-456",
  "source_title": "My YouTube Video",
  "source_type": "youtube",
  "status": "completed",
  "clips_count": 5,
  "font_family": "TikTokSans-Regular",
  "font_size": 24,
  "font_color": "#FFFFFF",
  "created_at": "2025-11-10T10:00:00Z",
  "updated_at": "2025-11-10T10:15:00Z"
}
```

---

#### GET /tasks/{task_id}/clips

Get all clips for a specific task.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "clips": [
    {
      "id": "clip-1",
      "filename": "clip_1_10.5_25.3.mp4",
      "file_path": "/tmp/clips/clip_1_10.5_25.3.mp4",
      "video_url": "/clips/clip_1_10.5_25.3.mp4",
      "start_time": 10.5,
      "end_time": 25.3,
      "duration": 14.8,
      "text": "Transcript text...",
      "relevance_score": 95,
      "reasoning": "Strong hook",
      "clip_order": 1,
      "created_at": "2025-11-10T10:15:00Z"
    }
  ],
  "total_clips": 1
}
```

---

#### GET /tasks/{task_id}/progress

Real-time progress updates via Server-Sent Events (SSE).

**Authentication**: Required

**Response**: SSE stream

**Event Types**:
- `status`: Initial status
- `progress`: Progress update (0-100)
- `close`: Task completed or failed

**Example SSE Events**:
```
event: status
data: {"task_id": "550e8400-e29b-41d4-a716-446655440000", "status": "processing", "progress": 0}

event: progress
data: {"task_id": "550e8400-e29b-41d4-a716-446655440000", "status": "processing", "progress": 25, "message": "Downloading video..."}

event: progress
data: {"task_id": "550e8400-e29b-41d4-a716-446655440000", "status": "processing", "progress": 50, "message": "Generating transcript..."}

event: close
data: {"status": "completed"}
```

---

#### PATCH /tasks/{task_id}

Update task details (title).

**Authentication**: Required

**Request Body**:
```json
{
  "title": "New Title"
}
```

**Response (200 OK)**:
```json
{
  "message": "Task updated successfully",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### DELETE /tasks/{task_id}

Delete a task and all associated clips.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "message": "Task deleted successfully"
}
```

---

#### DELETE /tasks/{task_id}/clips/{clip_id}

Delete a specific clip.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "message": "Clip deleted successfully"
}
```

---

### AI Titles

#### POST /ai/generate-titles

Generate viral titles for a video clip using multiple AI models.

**Authentication**: Required

**Request Body**:
```json
{
  "transcript_text": "In this clip I reveal the secret to...",
  "platform": "tiktok",
  "target_audience": "young entrepreneurs",
  "key_topics": ["business", "success"],
  "duration_seconds": 15,
  "num_variations": 10,
  "include_styles": ["question", "shocking", "curiosity"]
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| transcript_text | string | Yes | Transcript text of the clip |
| platform | string | No | Target platform (tiktok, instagram, youtube, twitter, linkedin) |
| target_audience | string | No | Description of target audience |
| key_topics | array | No | List of key topics/themes |
| duration_seconds | float | No | Clip duration in seconds |
| num_variations | integer | No | Number of titles to generate (3-15, default: 8) |
| include_styles | array | No | Specific title styles to use |

**Response (200 OK)**:
```json
{
  "titles": [
    {
      "text": "The Secret Nobody Tells You About Success",
      "virality_score": 95,
      "style": "curiosity",
      "character_count": 42
    },
    {
      "text": "How I Discovered This One Simple Trick",
      "virality_score": 92,
      "style": "how_to",
      "character_count": 39
    }
  ],
  "best_title": {
    "text": "The Secret Nobody Tells You About Success",
    "virality_score": 95,
    "style": "curiosity",
    "character_count": 42
  },
  "platform": "tiktok",
  "total_generated": 10,
  "generation_time_ms": 1250
}
```

---

#### POST /ai/generate-titles/clip/{clip_id}

Generate titles for an existing clip by ID.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| platform | string | No | tiktok | Target platform |
| target_audience | string | No | - | Target audience |
| num_variations | integer | No | 8 | Number of variations |

**Example**:
```bash
curl -X POST "http://localhost:8000/ai/generate-titles/clip/clip-123?platform=instagram&num_variations=10" \
  -H "user_id: your-user-id"
```

**Response**: Same as `/ai/generate-titles`

---

#### GET /ai/title-styles

Get all available title styles with descriptions.

**Authentication**: Not required

**Response (200 OK)**:
```json
{
  "styles": {
    "question": {
      "name": "Question",
      "description": "Starts with a question to create curiosity",
      "example": "Why Are People Obsessed With This Simple Trick?"
    },
    "shocking": {
      "name": "Shocking",
      "description": "Uses shocking or surprising elements",
      "example": "This One Mistake Cost Me Everything"
    }
  },
  "total": 8
}
```

---

#### GET /ai/platforms

Get all supported social media platforms.

**Authentication**: Not required

**Response (200 OK)**:
```json
{
  "platforms": {
    "tiktok": {
      "name": "TikTok",
      "character_limit": 150,
      "style": "Casual, trendy, uses current slang",
      "optimal_length": "50-100 characters"
    },
    "instagram": {
      "name": "Instagram",
      "character_limit": 125,
      "style": "Visual-first, lifestyle focus",
      "optimal_length": "40-90 characters"
    }
  },
  "total": 5
}
```

---

### Analytics

#### POST /analytics/record

Record analytics metrics for a clip.

**Authentication**: Required

**Request Body**:
```json
{
  "view_metrics": {
    "clip_id": "clip-123",
    "platform": "tiktok",
    "views": 10000,
    "likes": 1500,
    "comments": 200,
    "shares": 300,
    "date": "2025-11-10"
  },
  "performance_metrics": {
    "clip_id": "clip-123",
    "engagement_rate": 15.5,
    "watch_time": 12.3,
    "retention_rate": 85.0
  }
}
```

**Response (201 Created)**:
```json
{
  "message": "Metrics recorded successfully",
  "results": {
    "view_metrics": {
      "status": "created",
      "id": "view-metric-123"
    },
    "performance_metrics": {
      "status": "created",
      "id": "perf-metric-456"
    }
  }
}
```

---

#### GET /analytics/clip/{clip_id}

Get comprehensive performance metrics for a specific clip.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "clip_id": "clip-123",
  "clip_filename": "clip_1_10.5_25.3.mp4",
  "clip_duration": 14.8,
  "total_views": 15000,
  "total_likes": 2000,
  "total_comments": 300,
  "total_shares": 450,
  "avg_engagement_rate": 18.3,
  "avg_watch_time": 12.5,
  "avg_retention_rate": 84.5,
  "platforms": ["tiktok", "instagram"],
  "view_metrics_by_platform": {
    "tiktok": {
      "views": 10000,
      "likes": 1500,
      "comments": 200,
      "shares": 300,
      "date": "2025-11-10",
      "last_updated": "2025-11-10T15:00:00Z"
    }
  },
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T15:00:00Z"
}
```

---

#### GET /analytics/dashboard

Get aggregated analytics dashboard statistics.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| user_id | string | No | - | Filter by user |
| task_id | string | No | - | Filter by task |
| limit | integer | No | 10 | Number of top clips |

**Response (200 OK)**:
```json
{
  "total_clips": 25,
  "total_clips_with_metrics": 20,
  "total_views": 150000,
  "total_likes": 20000,
  "total_comments": 3000,
  "total_shares": 4500,
  "total_engagements": 27500,
  "avg_engagement_rate": 18.3,
  "avg_watch_time": 12.5,
  "avg_retention_rate": 84.5,
  "top_performing_clips": [
    {
      "clip_id": "clip-123",
      "filename": "clip_1_10.5_25.3.mp4",
      "duration": 14.8,
      "relevance_score": 95,
      "total_views": 50000,
      "total_likes": 8000,
      "total_comments": 1200,
      "total_shares": 2000,
      "engagement_rate": 22.4,
      "retention_rate": 90.0,
      "video_url": "/clips/clip_1_10.5_25.3.mp4"
    }
  ],
  "platform_breakdown": {
    "tiktok": {
      "clips_count": 15,
      "total_views": 100000,
      "total_likes": 15000,
      "total_comments": 2000,
      "total_shares": 3000,
      "total_engagements": 20000
    }
  }
}
```

---

### Calendar Scheduling

#### GET /calendar/oauth/google/url

Get Google OAuth authorization URL.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

---

#### POST /calendar/oauth/google/callback

Handle Google OAuth callback and store credentials.

**Authentication**: Not required (uses state parameter)

**Request Body**:
```json
{
  "code": "authorization_code_from_google",
  "state": "user_id"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "credential_id": "cred-123",
  "provider": "google"
}
```

---

#### POST /calendar/credentials/caldav

Add CalDAV calendar credentials (iCloud, Nextcloud, etc.).

**Authentication**: Required

**Request Body**:
```json
{
  "provider": "icloud",
  "username": "apple_id@icloud.com",
  "password": "app-specific-password",
  "calendar_name": "Calendar"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "credential_id": "cred-123",
  "provider": "icloud"
}
```

---

#### POST /calendar/schedule

Schedule a clip to be posted at a specific time.

**Authentication**: Required

**Request Body**:
```json
{
  "clip_id": "clip-123",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "scheduled_post_id": "post-123",
  "calendar_event_id": "event-456",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"
}
```

---

#### GET /calendar/events

List scheduled posts for the authenticated user.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter by status (scheduled, published, failed, cancelled) |
| start_date | string | No | Filter by start date (ISO format) |
| end_date | string | No | Filter by end date (ISO format) |
| limit | integer | No | Maximum number of results (default: 50) |

**Response (200 OK)**:
```json
{
  "scheduled_posts": [
    {
      "id": "post-123",
      "clip_id": "clip-456",
      "task_id": "task-789",
      "scheduled_time": "2025-11-15T10:00:00Z",
      "title": "Post to TikTok",
      "status": "scheduled",
      "calendar_provider": "google",
      "calendar_event_id": "event-123",
      "clip_metadata": {},
      "created_at": "2025-11-10T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Watermarks

#### POST /watermarks/upload

Upload a watermark video for a specific account.

**Authentication**: Required

**Request**: Multipart form data

```bash
curl -X POST "http://localhost:8000/watermarks/upload" \
  -H "user_id: your-user-id" \
  -F "account_id=my_account" \
  -F "watermark=@/path/to/watermark.mp4"
```

**Response (200 OK)**:
```json
{
  "message": "Watermark uploaded successfully",
  "account_id": "my_account",
  "filename": "my_account.mp4",
  "file_path": "/app/watermarks/my_account.mp4",
  "video_info": {
    "format": "mov,mp4,m4a,3gp,3g2,mj2",
    "codec": "h264",
    "duration": 2.5,
    "width": 1080,
    "height": 1920
  },
  "green_screen": {
    "has_green_screen": true,
    "confidence": 0.85,
    "avg_green_ratio": 0.72,
    "note": "Green screen detected"
  }
}
```

---

#### GET /watermarks

List all available watermarks.

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "watermarks": [
    {
      "account_id": "default",
      "filename": "default.mp4",
      "file_path": "/app/watermarks/default.mp4",
      "file_size_bytes": 1048576,
      "file_size_mb": 1.0,
      "is_default": true,
      "video_info": {
        "format": "mov,mp4",
        "codec": "h264",
        "duration": 2.5,
        "width": 1080,
        "height": 1920
      }
    }
  ],
  "total": 1,
  "watermarks_dir": "/app/watermarks"
}
```

---

### Posting Helper

#### POST /posting/analyze-screenshot

Analyze a screenshot using vision AI to generate posting suggestions.

**Authentication**: Required

**Request**: Multipart form data

```bash
curl -X POST "http://localhost:8000/posting/analyze-screenshot" \
  -H "user_id: your-user-id" \
  -F "file=@/path/to/screenshot.png"
```

**Response (200 OK)**:
```json
{
  "account_type": "fitness",
  "platform": "tiktok",
  "suggestions": {
    "title": "Transform Your Body in 30 Days",
    "hashtags": ["#fitness", "#workout", "#transformation"],
    "description": "Follow this simple routine to see amazing results"
  }
}
```

---

#### POST /posting/generate-content

Generate platform-specific content without screenshot analysis.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| platform | string | Yes | Target platform (tiktok, instagram, youtube_shorts) |
| video_title | string | No | Video title |
| video_description | string | No | Video description |

**Response (200 OK)**:
```json
{
  "platform": "tiktok",
  "content": {
    "title": "Amazing Video Title",
    "hashtags": ["#viral", "#trending"],
    "description": "Check out this amazing content"
  }
}
```

---

### Resources

#### GET /fonts

List all available font families for subtitle customization.

**Authentication**: Not required

**Response (200 OK)**:
```json
{
  "fonts": [
    {
      "name": "TikTokSans-Regular",
      "display_name": "TikTok Sans Regular",
      "file_path": "/app/fonts/TikTokSans-Regular.ttf"
    }
  ]
}
```

---

#### GET /fonts/{font_name}

Serve a specific font file.

**Authentication**: Not required

**Response**: Font file (font/ttf)

---

#### GET /transitions

List all available transition effects.

**Authentication**: Not required

**Response (200 OK)**:
```json
{
  "transitions": [
    {
      "name": "swipe_left",
      "display_name": "Swipe Left",
      "file_path": "/app/transitions/swipe_left.mp4"
    }
  ]
}
```

---

## Code Examples

### Python

#### Process a YouTube Video

```python
import requests

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "your-user-uuid"

# Headers
headers = {
    "user_id": USER_ID,
    "Content-Type": "application/json"
}

# Request body
data = {
    "source": {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    },
    "font_options": {
        "font_family": "TikTokSans-Regular",
        "font_size": 24,
        "font_color": "#FFFFFF"
    }
}

# Make request
response = requests.post(
    f"{API_BASE_URL}/start",
    headers=headers,
    json=data
)

# Handle response
if response.status_code == 200:
    result = response.json()
    task_id = result["task_id"]
    clips = result["clips"]

    print(f"Task ID: {task_id}")
    print(f"Generated {len(clips)} clips")

    for clip in clips:
        print(f"  - {clip['filename']}: {clip['duration']}s")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

#### Upload and Process a Video

```python
import requests

API_BASE_URL = "http://localhost:8000"
USER_ID = "your-user-uuid"

# Step 1: Upload video
with open("my_video.mp4", "rb") as video_file:
    upload_response = requests.post(
        f"{API_BASE_URL}/upload",
        headers={"user_id": USER_ID},
        files={"video": video_file}
    )

if upload_response.status_code == 200:
    video_path = upload_response.json()["video_path"]
    print(f"Uploaded to: {video_path}")

    # Step 2: Process uploaded video
    process_response = requests.post(
        f"{API_BASE_URL}/start",
        headers={"user_id": USER_ID, "Content-Type": "application/json"},
        json={
            "source": {"url": video_path}
        }
    )

    if process_response.status_code == 200:
        result = process_response.json()
        print(f"Task ID: {result['task_id']}")
```

#### Track Progress with SSE

```python
import requests
import json

API_BASE_URL = "http://localhost:8000"
USER_ID = "your-user-uuid"

# Start async processing
response = requests.post(
    f"{API_BASE_URL}/start-with-progress",
    headers={"user_id": USER_ID, "Content-Type": "application/json"},
    json={
        "source": {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    }
)

task_id = response.json()["task_id"]
print(f"Task started: {task_id}")

# Subscribe to progress updates
sse_url = f"{API_BASE_URL}/tasks/{task_id}/progress"
response = requests.get(sse_url, stream=True, headers={"user_id": USER_ID})

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(f"Progress: {data.get('progress', 0)}% - {data.get('message', '')}")

            if data.get('status') in ['completed', 'error']:
                break
```

---

### JavaScript (Node.js)

#### Process a YouTube Video

```javascript
const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';
const USER_ID = 'your-user-uuid';

async function processVideo() {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/start`,
      {
        source: {
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        },
        font_options: {
          font_family: 'TikTokSans-Regular',
          font_size: 24,
          font_color: '#FFFFFF'
        }
      },
      {
        headers: {
          'user_id': USER_ID,
          'Content-Type': 'application/json'
        }
      }
    );

    const { task_id, clips } = response.data;
    console.log(`Task ID: ${task_id}`);
    console.log(`Generated ${clips.length} clips`);

    clips.forEach(clip => {
      console.log(`  - ${clip.filename}: ${clip.duration}s`);
    });
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

processVideo();
```

#### Track Progress with EventSource

```javascript
const axios = require('axios');
const EventSource = require('eventsource');

const API_BASE_URL = 'http://localhost:8000';
const USER_ID = 'your-user-uuid';

async function processWithProgress() {
  try {
    // Start async processing
    const response = await axios.post(
      `${API_BASE_URL}/start-with-progress`,
      {
        source: {
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
      },
      {
        headers: {
          'user_id': USER_ID,
          'Content-Type': 'application/json'
        }
      }
    );

    const taskId = response.data.task_id;
    console.log(`Task started: ${taskId}`);

    // Subscribe to progress updates
    const eventSource = new EventSource(
      `${API_BASE_URL}/tasks/${taskId}/progress`,
      {
        headers: { 'user_id': USER_ID }
      }
    );

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      console.log(`Progress: ${data.progress}% - ${data.message}`);
    });

    eventSource.addEventListener('close', (event) => {
      const data = JSON.parse(event.data);
      console.log(`Task ${data.status}`);
      eventSource.close();
    });

    eventSource.addEventListener('error', (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
    });
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

processWithProgress();
```

---

### JavaScript (Browser/Frontend)

#### Process Video with Progress

```javascript
async function processVideo(youtubeUrl) {
  const API_BASE_URL = 'http://localhost:8000';
  const USER_ID = 'your-user-uuid';

  try {
    // Start processing
    const response = await fetch(`${API_BASE_URL}/start-with-progress`, {
      method: 'POST',
      headers: {
        'user_id': USER_ID,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source: { url: youtubeUrl }
      })
    });

    const { task_id } = await response.json();
    console.log(`Task started: ${task_id}`);

    // Subscribe to progress
    const eventSource = new EventSource(
      `${API_BASE_URL}/tasks/${task_id}/progress`
    );

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);

      // Update UI
      document.getElementById('progress-bar').style.width = `${data.progress}%`;
      document.getElementById('status-text').textContent = data.message;
    });

    eventSource.addEventListener('close', async (event) => {
      const data = JSON.parse(event.data);
      eventSource.close();

      if (data.status === 'completed') {
        // Fetch clips
        const clipsResponse = await fetch(
          `${API_BASE_URL}/tasks/${task_id}/clips`,
          {
            headers: { 'user_id': USER_ID }
          }
        );

        const { clips } = await clipsResponse.json();
        displayClips(clips);
      }
    });

  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

### cURL

#### Process a YouTube Video

```bash
curl -X POST "http://localhost:8000/start" \
  -H "user_id: your-user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "source": {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    },
    "font_options": {
      "font_family": "TikTokSans-Regular",
      "font_size": 24,
      "font_color": "#FFFFFF"
    }
  }'
```

#### Upload a Video

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "user_id: your-user-uuid" \
  -F "video=@/path/to/video.mp4"
```

#### List Tasks

```bash
curl -X GET "http://localhost:8000/tasks?limit=10" \
  -H "user_id: your-user-uuid"
```

#### Get Task Details

```bash
curl -X GET "http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "user_id: your-user-uuid"
```

#### Generate AI Titles

```bash
curl -X POST "http://localhost:8000/ai/generate-titles" \
  -H "user_id: your-user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "In this clip I reveal the secret to...",
    "platform": "tiktok",
    "num_variations": 10
  }'
```

#### Record Analytics

```bash
curl -X POST "http://localhost:8000/analytics/record" \
  -H "user_id: your-user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "view_metrics": {
      "clip_id": "clip-123",
      "platform": "tiktok",
      "views": 10000,
      "likes": 1500,
      "comments": 200,
      "shares": 300
    }
  }'
```

---

## Webhooks

### Coming Soon

Webhook support for asynchronous notifications is planned for v1.1.0.

**Planned Events**:
- `task.created`
- `task.completed`
- `task.failed`
- `clip.generated`
- `analytics.updated`

---

## Support

- **Documentation**: [https://supoclip.com/docs](https://supoclip.com/docs)
- **GitHub**: [https://github.com/yourusername/supoclip](https://github.com/yourusername/supoclip)
- **Issues**: [https://github.com/yourusername/supoclip/issues](https://github.com/yourusername/supoclip/issues)
- **Email**: support@supoclip.com

---

## License

MIT License - See LICENSE file for details.

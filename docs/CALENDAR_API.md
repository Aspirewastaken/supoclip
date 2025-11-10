# Calendar API Reference

Quick reference for SupoClip's Calendar Integration API.

## Base URL

```
http://localhost:8000/calendar
```

## Authentication

All endpoints require authentication via session cookies and `user_id` header.

**Headers:**
```
user_id: <user_uuid>
Cookie: session=<session_token>
```

---

## OAuth Endpoints

### Get Google OAuth URL

Get the authorization URL to connect Google Calendar.

```http
GET /calendar/oauth/google/url
```

**Response 200:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=..."
}
```

---

### Handle Google OAuth Callback

Exchange authorization code for tokens and store credentials.

```http
POST /calendar/oauth/google/callback
```

**Request Body:**
```json
{
  "code": "4/0AeanNXXXXXXXXX",
  "state": "user_uuid"
}
```

**Response 200:**
```json
{
  "success": true,
  "credential_id": "cred_uuid",
  "provider": "google"
}
```

**Error Responses:**
- `400` - Missing code or state
- `500` - Token exchange failed

---

## Credential Management

### Add CalDAV Credentials

Add iCloud Calendar or generic CalDAV credentials.

```http
POST /calendar/credentials/caldav
```

**Request Body (iCloud):**
```json
{
  "provider": "icloud",
  "username": "apple_id@icloud.com",
  "password": "xxxx-xxxx-xxxx-xxxx",
  "calendar_name": "Calendar"
}
```

**Request Body (CalDAV):**
```json
{
  "provider": "caldav",
  "url": "https://caldav.example.com",
  "username": "user@example.com",
  "password": "password",
  "calendar_name": "My Calendar"
}
```

**Response 200:**
```json
{
  "success": true,
  "credential_id": "cred_uuid",
  "provider": "icloud"
}
```

**Error Responses:**
- `400` - Missing required fields
- `401` - Invalid credentials
- `500` - Connection failed

---

### List Credentials

Get all calendar credentials for the authenticated user.

```http
GET /calendar/credentials
```

**Response 200:**
```json
{
  "credentials": [
    {
      "id": "cred_uuid",
      "provider": "google",
      "is_active": true,
      "calendar_name": null,
      "created_at": "2025-11-10T12:00:00Z"
    },
    {
      "id": "cred_uuid_2",
      "provider": "icloud",
      "is_active": true,
      "calendar_name": "Calendar",
      "created_at": "2025-11-09T10:00:00Z"
    }
  ]
}
```

---

### Delete Credential

Remove a calendar credential.

```http
DELETE /calendar/credentials/{credential_id}
```

**Response 200:**
```json
{
  "success": true
}
```

**Error Responses:**
- `404` - Credential not found
- `403` - Access denied

---

## Scheduling

### Schedule Post

Schedule a clip to be posted at a specific time.

```http
POST /calendar/schedule
```

**Request Body:**
```json
{
  "clip_id": "clip_uuid",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"
}
```

**Fields:**
- `clip_id` (required) - UUID of the clip to schedule
- `scheduled_time` (required) - ISO 8601 datetime in UTC
- `provider` (optional) - Calendar provider to use (defaults to active credential)

**Response 200:**
```json
{
  "success": true,
  "scheduled_post_id": "post_uuid",
  "calendar_event_id": "google_event_id",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"
}
```

**Error Responses:**
- `400` - Missing required fields or invalid date format
- `403` - User doesn't own the clip
- `404` - Clip not found
- `401` - Calendar authentication failed

---

### List Scheduled Posts

Get scheduled posts with optional filtering.

```http
GET /calendar/events
```

**Query Parameters:**
- `status` (optional) - Filter by status: `scheduled`, `published`, `failed`, `cancelled`
- `start_date` (optional) - ISO 8601 datetime (filter events after this date)
- `end_date` (optional) - ISO 8601 datetime (filter events before this date)
- `limit` (optional) - Max results (default: 50, max: 100)

**Example:**
```http
GET /calendar/events?status=scheduled&start_date=2025-11-10T00:00:00Z&limit=20
```

**Response 200:**
```json
{
  "scheduled_posts": [
    {
      "id": "post_uuid",
      "clip_id": "clip_uuid",
      "task_id": "task_uuid",
      "scheduled_time": "2025-11-15T10:00:00Z",
      "title": "Post Clip: viral_moment.mp4",
      "status": "scheduled",
      "calendar_provider": "google",
      "calendar_event_id": "google_event_id",
      "clip_metadata": {
        "filename": "viral_moment.mp4",
        "duration": 30.5,
        "start_time": "00:45",
        "end_time": "01:15",
        "relevance_score": 0.92,
        "text": "This is the transcript of the clip..."
      },
      "created_at": "2025-11-10T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Update Scheduled Post

Update the time or status of a scheduled post.

```http
PATCH /calendar/events/{scheduled_post_id}
```

**Request Body:**
```json
{
  "scheduled_time": "2025-11-16T15:00:00Z",
  "status": "cancelled"
}
```

**Fields (all optional):**
- `scheduled_time` - New scheduled time (ISO 8601 UTC)
- `status` - New status: `scheduled`, `published`, `failed`, `cancelled`

**Response 200:**
```json
{
  "success": true,
  "scheduled_post": {
    "id": "post_uuid",
    "scheduled_time": "2025-11-16T15:00:00Z",
    "status": "cancelled"
  }
}
```

**Error Responses:**
- `400` - Invalid date format or status
- `404` - Scheduled post not found
- `403` - Access denied

---

### Delete Scheduled Post

Delete a scheduled post and remove it from the calendar.

```http
DELETE /calendar/events/{scheduled_post_id}
```

**Response 200:**
```json
{
  "success": true
}
```

**Error Responses:**
- `404` - Scheduled post not found
- `403` - Access denied

**Note:** This will attempt to delete the calendar event from the provider. If the calendar event deletion fails, the database record will still be removed.

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required or failed |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Event Metadata Structure

Calendar events created by SupoClip include the following metadata:

**Google Calendar (Extended Properties):**
```json
{
  "clip_id": "clip_uuid",
  "task_id": "task_uuid",
  "user_id": "user_uuid",
  "scheduled_by": "supoclip",
  "filename": "clip.mp4",
  "duration": "30.5",
  "relevance_score": "0.92"
}
```

**CalDAV/iCloud (Description Field):**
```
📹 SupoClip - Scheduled Post

Filename: clip.mp4
Duration: 30.5s
Original Timestamp: 00:45 - 01:15
AI Relevance Score: 0.92

Transcript:
This is the transcript of the clip...

Clip ID: clip_uuid
Task ID: task_uuid
```

---

## Rate Limits

- **OAuth endpoints:** 10 requests per minute per user
- **Credential endpoints:** 20 requests per minute per user
- **Scheduling endpoints:** 30 requests per minute per user

Exceeding rate limits returns:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## Webhooks (Future Feature)

Planned webhook support for automatic posting:

```http
POST /calendar/webhooks
```

This will enable automatic posting when scheduled time arrives.

---

## Code Examples

### JavaScript/TypeScript

```typescript
// Schedule a post
const schedulePost = async (clipId: string, scheduledTime: string) => {
  const response = await fetch('http://localhost:8000/calendar/schedule', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'user_id': userId,
    },
    credentials: 'include',
    body: JSON.stringify({
      clip_id: clipId,
      scheduled_time: scheduledTime,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to schedule post');
  }

  return await response.json();
};

// List scheduled posts
const listScheduledPosts = async (status?: string) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);

  const response = await fetch(
    `http://localhost:8000/calendar/events?${params}`,
    {
      headers: { 'user_id': userId },
      credentials: 'include',
    }
  );

  return await response.json();
};
```

### Python

```python
import requests
from datetime import datetime, timedelta

# Schedule a post
def schedule_post(clip_id: str, scheduled_time: datetime):
    response = requests.post(
        'http://localhost:8000/calendar/schedule',
        headers={'user_id': user_id},
        cookies={'session': session_token},
        json={
            'clip_id': clip_id,
            'scheduled_time': scheduled_time.isoformat(),
        }
    )
    response.raise_for_status()
    return response.json()

# List scheduled posts
def list_scheduled_posts(status: str = None):
    params = {}
    if status:
        params['status'] = status

    response = requests.get(
        'http://localhost:8000/calendar/events',
        headers={'user_id': user_id},
        cookies={'session': session_token},
        params=params
    )
    response.raise_for_status()
    return response.json()
```

### cURL

```bash
# Schedule a post
curl -X POST "http://localhost:8000/calendar/schedule" \
  -H "Content-Type: application/json" \
  -H "user_id: user_uuid" \
  --cookie "session=token" \
  -d '{
    "clip_id": "clip_uuid",
    "scheduled_time": "2025-11-15T10:00:00Z"
  }'

# List scheduled posts
curl "http://localhost:8000/calendar/events?status=scheduled" \
  -H "user_id: user_uuid" \
  --cookie "session=token"

# Delete scheduled post
curl -X DELETE "http://localhost:8000/calendar/events/post_uuid" \
  -H "user_id: user_uuid" \
  --cookie "session=token"
```

---

## Environment Variables

Required environment variables for calendar integration:

```bash
# Google Calendar (optional)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/supoclip

# API
API_URL=http://localhost:8000
```

---

## Testing

Test the API with the provided FastAPI docs:

```
http://localhost:8000/docs
```

Or use the interactive API explorer at:

```
http://localhost:8000/redoc
```

---

## Support

- **Documentation:** `/docs/CALENDAR_INTEGRATION.md`
- **API Docs:** `http://localhost:8000/docs`
- **Issues:** GitHub Issues
- **Discord:** Community Discord Server

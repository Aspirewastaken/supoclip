# Calendar Integration Guide

Complete guide for integrating SupoClip with calendar services to schedule posts.

## Overview

SupoClip's calendar integration allows you to schedule your generated clips to be posted at specific times by creating events in your calendar (Google Calendar, iCloud Calendar, or any CalDAV-compatible calendar service).

### Supported Calendar Services

- **Google Calendar** - OAuth 2.0 authentication
- **iCloud Calendar** - CalDAV with app-specific passwords
- **Generic CalDAV** - Any CalDAV-compatible service (Nextcloud, OwnCloud, etc.)

## Architecture

### Backend Components

```
backend/src/integrations/
├── __init__.py                  # Module exports
├── calendar.py                  # Base classes and interfaces
├── google_calendar.py           # Google Calendar integration
└── caldav_calendar.py           # CalDAV/iCloud integration

backend/src/api/routes/
└── calendar.py                  # Calendar API endpoints

backend/src/models.py            # Database models
└── CalendarCredential           # Stores calendar credentials
└── ScheduledPost                # Stores scheduled posts
```

### Database Schema

#### CalendarCredential Table

Stores calendar provider credentials for users.

```sql
CREATE TABLE calendar_credentials (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) CHECK (provider IN ('google', 'icloud', 'caldav')),

    -- OAuth credentials (Google)
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMP WITH TIME ZONE,

    -- CalDAV credentials (iCloud, CalDAV)
    caldav_url VARCHAR(500),
    caldav_username VARCHAR(255),
    caldav_password TEXT,
    calendar_name VARCHAR(255),

    -- Metadata
    metadata JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### ScheduledPost Table

Stores scheduled posts linked to calendar events.

```sql
CREATE TABLE scheduled_posts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    clip_id VARCHAR(36) REFERENCES generated_clips(id) ON DELETE CASCADE,
    task_id VARCHAR(36) REFERENCES tasks(id) ON DELETE CASCADE,
    calendar_credential_id VARCHAR(36) REFERENCES calendar_credentials(id) ON DELETE CASCADE,

    -- Calendar event details
    calendar_event_id VARCHAR(500),
    calendar_provider VARCHAR(20) CHECK (calendar_provider IN ('google', 'icloud', 'caldav')),

    -- Scheduling details
    scheduled_time TIMESTAMP WITH TIME ZONE,
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(20) CHECK (status IN ('scheduled', 'published', 'failed', 'cancelled')),

    -- Post metadata
    clip_metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Setup Instructions

### 1. Install Dependencies

The calendar integration requires several Python packages:

```bash
cd backend
uv sync  # This will install all dependencies from pyproject.toml
```

Required packages:
- `google-api-python-client` - Google Calendar API
- `google-auth-oauthlib` - Google OAuth 2.0
- `google-auth-httplib2` - Google Auth HTTP
- `caldav` - CalDAV protocol support
- `icalendar` - iCalendar format support
- `pytz` - Timezone support

### 2. Database Migration

Apply the database migration to create the calendar tables:

```bash
# If using PostgreSQL directly
psql -U your_user -d supoclip_db -f backend/migrations/001_add_calendar_tables.sql

# Or use Docker
docker exec -i supoclip-postgres psql -U postgres -d supoclip < backend/migrations/001_add_calendar_tables.sql
```

### 3. Configure Google Calendar OAuth (Optional)

If you want to support Google Calendar, you need to:

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Calendar API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:3000/auth/google/callback` (development)
     - `https://yourdomain.com/auth/google/callback` (production)
   - Save the Client ID and Client Secret

4. **Configure Environment Variables**

Add to `backend/.env`:

```bash
# Google Calendar OAuth
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

Add to `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Configure iCloud Calendar (Optional)

For iCloud Calendar, users need to generate an app-specific password:

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with Apple ID
3. Navigate to Security > App-Specific Passwords
4. Click "Generate Password"
5. Enter "SupoClip" as the app name
6. Copy the generated password

Users will enter their Apple ID and app-specific password in the frontend.

## API Reference

### OAuth Endpoints

#### Get Google OAuth URL

```http
GET /calendar/oauth/google/url
```

**Headers:**
- `user_id`: Authenticated user ID

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

#### Handle Google OAuth Callback

```http
POST /calendar/oauth/google/callback
```

**Body:**
```json
{
  "code": "authorization_code_from_google",
  "state": "user_id"
}
```

**Response:**
```json
{
  "success": true,
  "credential_id": "credential_uuid",
  "provider": "google"
}
```

### Credential Management Endpoints

#### Add CalDAV Credentials

```http
POST /calendar/credentials/caldav
```

**Headers:**
- `user_id`: Authenticated user ID

**Body:**
```json
{
  "provider": "icloud",  // or "caldav"
  "url": "https://caldav.icloud.com",  // optional for iCloud
  "username": "apple_id@icloud.com",
  "password": "app-specific-password",
  "calendar_name": "Calendar"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "credential_id": "credential_uuid",
  "provider": "icloud"
}
```

#### List Credentials

```http
GET /calendar/credentials
```

**Headers:**
- `user_id`: Authenticated user ID

**Response:**
```json
{
  "credentials": [
    {
      "id": "credential_uuid",
      "provider": "google",
      "is_active": true,
      "calendar_name": null,
      "created_at": "2025-11-10T12:00:00Z"
    }
  ]
}
```

#### Delete Credential

```http
DELETE /calendar/credentials/{credential_id}
```

**Headers:**
- `user_id`: Authenticated user ID

**Response:**
```json
{
  "success": true
}
```

### Scheduling Endpoints

#### Schedule Post

```http
POST /calendar/schedule
```

**Headers:**
- `user_id`: Authenticated user ID

**Body:**
```json
{
  "clip_id": "clip_uuid",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"  // optional, uses active credential
}
```

**Response:**
```json
{
  "success": true,
  "scheduled_post_id": "post_uuid",
  "calendar_event_id": "google_event_id",
  "scheduled_time": "2025-11-15T10:00:00Z",
  "provider": "google"
}
```

#### List Scheduled Posts

```http
GET /calendar/events?status=scheduled&start_date=2025-11-10T00:00:00Z&end_date=2025-11-20T00:00:00Z&limit=50
```

**Headers:**
- `user_id`: Authenticated user ID

**Query Parameters:**
- `status` (optional): Filter by status (`scheduled`, `published`, `failed`, `cancelled`)
- `start_date` (optional): Filter by start date (ISO format)
- `end_date` (optional): Filter by end date (ISO format)
- `limit` (optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "scheduled_posts": [
    {
      "id": "post_uuid",
      "clip_id": "clip_uuid",
      "task_id": "task_uuid",
      "scheduled_time": "2025-11-15T10:00:00Z",
      "title": "Post Clip: clip_filename.mp4",
      "status": "scheduled",
      "calendar_provider": "google",
      "calendar_event_id": "google_event_id",
      "clip_metadata": {
        "filename": "clip_filename.mp4",
        "duration": 30.5,
        "relevance_score": 0.85
      },
      "created_at": "2025-11-10T12:00:00Z"
    }
  ],
  "total": 1
}
```

#### Update Scheduled Post

```http
PATCH /calendar/events/{scheduled_post_id}
```

**Headers:**
- `user_id`: Authenticated user ID

**Body:**
```json
{
  "scheduled_time": "2025-11-16T15:00:00Z",  // optional
  "status": "cancelled"  // optional
}
```

**Response:**
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

#### Delete Scheduled Post

```http
DELETE /calendar/events/{scheduled_post_id}
```

**Headers:**
- `user_id`: Authenticated user ID

**Response:**
```json
{
  "success": true
}
```

## Frontend Integration

### Using the Calendar Scheduler Component

Add the scheduler to any clip view:

```tsx
import { CalendarScheduler } from "@/components/calendar-scheduler";

function ClipView({ clip }) {
  return (
    <div>
      {/* Clip display */}
      <video src={clip.url} controls />

      {/* Calendar scheduler */}
      <CalendarScheduler
        clipId={clip.id}
        clipTitle={clip.filename}
        onScheduled={() => {
          console.log("Clip scheduled!");
        }}
      />
    </div>
  );
}
```

### Using the Calendar View Component

Display all scheduled posts:

```tsx
import { CalendarView } from "@/components/calendar-view";

function ScheduledPostsPage() {
  return (
    <div className="container">
      <h1>Scheduled Posts</h1>
      <CalendarView showFilters={true} limit={50} />
    </div>
  );
}
```

### Complete Calendar Page

A full calendar management page is available at `/calendar`:

```tsx
// Already implemented at frontend/src/app/calendar/page.tsx
// Access at: http://localhost:3000/calendar
```

## Usage Examples

### Python SDK Example

```python
from backend.src.integrations.calendar import CalendarIntegration, CalendarProvider
from datetime import datetime, timedelta

# Create Google Calendar integration
google_cal = CalendarIntegration.get_calendar_integration(
    provider=CalendarProvider.GOOGLE,
    user_id="user_uuid",
    credentials={
        "access_token": "google_access_token",
        "refresh_token": "google_refresh_token",
        "client_id": "google_client_id",
        "client_secret": "google_client_secret",
    }
)

# Authenticate
await google_cal.authenticate()

# Schedule a post
scheduled_post = await google_cal.schedule_post(
    clip_id="clip_uuid",
    task_id="task_uuid",
    scheduled_time=datetime.now() + timedelta(days=1),
    clip_metadata={
        "filename": "clip.mp4",
        "duration": 30.5,
        "relevance_score": 0.85,
    }
)

print(f"Event created: {scheduled_post.calendar_event_id}")
```

### iCloud Calendar Example

```python
# Create iCloud Calendar integration
icloud_cal = CalendarIntegration.get_calendar_integration(
    provider=CalendarProvider.ICLOUD,
    user_id="user_uuid",
    credentials={
        "url": "https://caldav.icloud.com",
        "username": "apple_id@icloud.com",
        "password": "app-specific-password",
        "calendar_name": "Calendar",
    }
)

# Authenticate
await icloud_cal.authenticate()

# Create a custom event
event_id = await icloud_cal.create_event(
    title="Post Video Clip",
    start_time=datetime.now() + timedelta(hours=2),
    description="Remember to post this clip!",
    metadata={"clip_id": "clip_uuid"},
)

print(f"Event created: {event_id}")
```

### cURL Examples

**Schedule a post:**

```bash
curl -X POST "http://localhost:8000/calendar/schedule" \
  -H "Content-Type: application/json" \
  -H "user_id: user_uuid" \
  --cookie "session=..." \
  -d '{
    "clip_id": "clip_uuid",
    "scheduled_time": "2025-11-15T10:00:00Z"
  }'
```

**List scheduled posts:**

```bash
curl "http://localhost:8000/calendar/events?status=scheduled&limit=10" \
  -H "user_id: user_uuid" \
  --cookie "session=..."
```

## Security Considerations

### Credential Storage

**Current Implementation:**
- OAuth tokens stored in database (access_token, refresh_token)
- CalDAV passwords stored in plain text in database
- Session-based authentication for API access

**Production Recommendations:**

1. **Encrypt Sensitive Data**
   ```python
   from cryptography.fernet import Fernet

   # Use environment variable for encryption key
   ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
   fernet = Fernet(ENCRYPTION_KEY)

   # Encrypt before storing
   encrypted_password = fernet.encrypt(password.encode())

   # Decrypt when retrieving
   decrypted_password = fernet.decrypt(encrypted_password).decode()
   ```

2. **Use Secure Token Storage**
   - Consider using a secret management service (AWS Secrets Manager, HashiCorp Vault)
   - Implement token rotation for OAuth tokens
   - Set short expiry times for access tokens

3. **Implement Rate Limiting**
   - Limit API requests per user/IP
   - Prevent brute force attacks on credentials

4. **Use HTTPS Only**
   - All calendar API requests must use HTTPS
   - Enable HSTS headers
   - Use secure cookies

### OAuth Security

- Always validate the `state` parameter to prevent CSRF attacks
- Use PKCE (Proof Key for Code Exchange) for mobile apps
- Implement proper token refresh logic
- Store tokens securely (encrypted at rest)

### CalDAV Security

- Require strong passwords
- Recommend app-specific passwords over main account passwords
- Validate CalDAV URLs to prevent SSRF attacks
- Implement connection timeouts

## Troubleshooting

### Google Calendar Issues

**Problem:** "OAuth URL generation fails"

**Solution:**
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Check that Google Calendar API is enabled in Google Cloud Console
- Ensure redirect URI is authorized in OAuth client settings

**Problem:** "Token refresh fails"

**Solution:**
- Check that refresh token is stored and valid
- Verify token hasn't been revoked in Google account settings
- Re-authenticate if necessary

### iCloud Calendar Issues

**Problem:** "Authentication fails with iCloud"

**Solution:**
- Ensure user is using an app-specific password, not their main iCloud password
- Verify Apple ID is correct
- Check that Calendar is enabled in iCloud settings

**Problem:** "Calendar not found"

**Solution:**
- Try leaving `calendar_name` empty to use default calendar
- List available calendars manually to verify name
- Check calendar sharing settings

### CalDAV Issues

**Problem:** "Connection timeout"

**Solution:**
- Verify CalDAV URL is correct and accessible
- Check firewall settings
- Test URL in a CalDAV client (Thunderbird, etc.)

**Problem:** "Invalid credentials"

**Solution:**
- Verify username and password are correct
- Check if server requires additional authentication
- Test credentials with curl:
  ```bash
  curl -u username:password https://caldav.example.com/
  ```

## Best Practices

### Event Creation

1. **Use Clear Titles**
   - Include clip filename in title
   - Add context (e.g., "Post Clip: viral_moment.mp4")

2. **Add Detailed Descriptions**
   - Include clip metadata (duration, relevance score)
   - Add transcript excerpt
   - Include clip ID for reference

3. **Set Appropriate Duration**
   - Default: 5 minutes
   - Adjust based on posting workflow
   - Add buffer time for review

### Scheduling Strategy

1. **Optimal Posting Times**
   - Schedule during peak engagement hours
   - Consider time zones of target audience
   - Space out posts evenly

2. **Batch Scheduling**
   - Schedule multiple clips at once
   - Use calendar view to avoid conflicts
   - Maintain consistent posting schedule

3. **Status Management**
   - Mark posts as "published" after posting
   - Set to "failed" if posting encounters errors
   - Use "cancelled" for posts you decide not to publish

## Testing

### Unit Tests

```python
# Test Google Calendar integration
async def test_google_calendar_schedule():
    calendar = GoogleCalendarIntegration(
        user_id="test_user",
        credentials=test_credentials
    )

    assert await calendar.authenticate()

    event_id = await calendar.create_event(
        title="Test Event",
        start_time=datetime.now() + timedelta(hours=1)
    )

    assert event_id is not None

    # Clean up
    await calendar.delete_event(event_id)
```

### Integration Tests

```bash
# Test API endpoints
pytest backend/tests/test_calendar_api.py -v

# Test with real credentials (requires setup)
pytest backend/tests/test_calendar_integration.py --real-credentials
```

## Limitations

### Current Limitations

1. **No Automatic Posting**
   - Calendar events are reminders, not automated posts
   - Actual posting must be done manually or via separate automation

2. **Single Calendar Per Provider**
   - Only one Google Calendar account per user
   - Only one iCloud Calendar account per user
   - Multiple CalDAV servers supported

3. **Event Metadata**
   - Google Calendar: Stored in extended properties
   - CalDAV: Stored in description (less structured)

4. **Timezone Handling**
   - All times stored and displayed in UTC
   - Frontend should handle local timezone conversion

### Future Enhancements

- [ ] Automatic posting at scheduled time (requires webhook/worker)
- [ ] Multiple calendar accounts per provider
- [ ] Calendar sync (two-way updates)
- [ ] Recurring post schedules
- [ ] Social media platform integration
- [ ] Team calendar sharing
- [ ] Calendar analytics and insights

## Support

For issues or questions:

1. Check the [GitHub Issues](https://github.com/yourusername/supoclip/issues)
2. Review the [API Documentation](http://localhost:8000/docs)
3. Join the [Discord Community](https://discord.gg/supoclip)

## License

This calendar integration is part of SupoClip and follows the same license as the main project.

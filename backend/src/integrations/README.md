# Calendar Integrations

This module provides calendar integration for scheduling posts in SupoClip.

## Supported Providers

- **Google Calendar** - OAuth 2.0 authentication
- **iCloud Calendar** - CalDAV with app-specific passwords
- **Generic CalDAV** - Any CalDAV-compatible service

## Architecture

### Base Classes

**`CalendarIntegration`** - Abstract base class that all calendar providers must implement.

Key methods:
- `authenticate()` - Authenticate with the calendar provider
- `create_event()` - Create a calendar event
- `update_event()` - Update an existing event
- `delete_event()` - Delete an event
- `get_event()` - Get a specific event
- `list_events()` - List events in a date range
- `schedule_post()` - High-level method to schedule a clip post

**`CalendarProvider`** - Enum of supported providers (`GOOGLE`, `ICLOUD`, `CALDAV`)

**`ScheduledPost`** - Pydantic model for scheduled posts

**`CalendarEvent`** - Generic calendar event model

### Provider Implementations

#### GoogleCalendarIntegration

Uses Google Calendar API v3 with OAuth 2.0.

```python
from integrations.google_calendar import GoogleCalendarIntegration

calendar = GoogleCalendarIntegration(
    user_id="user_uuid",
    credentials={
        "access_token": "token",
        "refresh_token": "refresh_token",
        "client_id": "client_id",
        "client_secret": "client_secret",
    }
)

await calendar.authenticate()

event_id = await calendar.create_event(
    title="Post Clip",
    start_time=datetime.now() + timedelta(hours=1),
    description="Remember to post this clip!",
)
```

**Features:**
- Automatic token refresh
- Extended properties for metadata
- 10-minute event reminders

#### CalDAVCalendarIntegration

Uses CalDAV protocol for iCloud and other CalDAV servers.

```python
from integrations.caldav_calendar import CalDAVCalendarIntegration

calendar = CalDAVCalendarIntegration(
    user_id="user_uuid",
    credentials={
        "url": "https://caldav.icloud.com",
        "username": "apple_id@icloud.com",
        "password": "app-specific-password",
        "calendar_name": "Calendar",
    }
)

await calendar.authenticate()

event_id = await calendar.create_event(
    title="Post Clip",
    start_time=datetime.now() + timedelta(hours=1),
)
```

**Features:**
- iCalendar format support
- Metadata stored in description
- Multiple calendar support

## Usage

### Factory Pattern

Use the factory method to get the appropriate integration:

```python
from integrations.calendar import CalendarIntegration, CalendarProvider

calendar = CalendarIntegration.get_calendar_integration(
    provider=CalendarProvider.GOOGLE,
    user_id="user_uuid",
    credentials=credentials_dict,
)

await calendar.authenticate()
```

### Scheduling Posts

The high-level `schedule_post()` method handles everything:

```python
scheduled_post = await calendar.schedule_post(
    clip_id="clip_uuid",
    task_id="task_uuid",
    scheduled_time=datetime.now() + timedelta(days=1),
    clip_metadata={
        "filename": "clip.mp4",
        "duration": 30.5,
        "relevance_score": 0.92,
    },
)

print(f"Scheduled: {scheduled_post.calendar_event_id}")
```

This will:
1. Create a 5-minute calendar event
2. Add clip metadata to the event
3. Return a `ScheduledPost` object

## Error Handling

All methods may raise exceptions:

```python
try:
    await calendar.authenticate()
except Exception as e:
    logger.error(f"Authentication failed: {e}")
    # Handle authentication error

try:
    event_id = await calendar.create_event(...)
except RuntimeError as e:
    logger.error(f"Failed to create event: {e}")
    # Handle creation error
```

## Testing

### Unit Tests

```python
import pytest
from integrations.calendar import CalendarIntegration, CalendarProvider

@pytest.mark.asyncio
async def test_google_calendar():
    calendar = CalendarIntegration.get_calendar_integration(
        provider=CalendarProvider.GOOGLE,
        user_id="test_user",
        credentials=test_credentials,
    )

    assert await calendar.authenticate()
    assert calendar.get_provider() == CalendarProvider.GOOGLE
```

### Integration Tests

```bash
# Run integration tests (requires real credentials)
pytest tests/test_calendar_integration.py --real-credentials

# Test with mock credentials
pytest tests/test_calendar_integration.py
```

## Dependencies

Required packages:
- `google-api-python-client` - Google Calendar API
- `google-auth-oauthlib` - Google OAuth 2.0
- `google-auth-httplib2` - Google Auth HTTP
- `caldav` - CalDAV protocol support
- `icalendar` - iCalendar format support
- `pytz` - Timezone support

Install with:
```bash
uv sync
```

## Security Notes

### Credential Storage

**Current implementation stores credentials in the database:**
- OAuth tokens (Google) - access_token, refresh_token
- CalDAV passwords (iCloud, CalDAV) - plain text

**Production recommendations:**

1. **Encrypt sensitive data at rest**
   ```python
   from cryptography.fernet import Fernet

   fernet = Fernet(ENCRYPTION_KEY)
   encrypted = fernet.encrypt(password.encode())
   decrypted = fernet.decrypt(encrypted).decode()
   ```

2. **Use a secrets manager**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault

3. **Implement token rotation**
   - Refresh OAuth tokens regularly
   - Rotate encryption keys

### OAuth Security

- Always validate `state` parameter (CSRF protection)
- Use PKCE for mobile apps
- Store tokens securely (encrypted)
- Implement proper token refresh logic

### CalDAV Security

- Require strong passwords
- Recommend app-specific passwords
- Validate URLs to prevent SSRF
- Implement connection timeouts

## Troubleshooting

### Google Calendar

**Issue:** Token refresh fails

**Solution:**
- Check refresh token is stored
- Verify token hasn't been revoked
- Re-authenticate if necessary

### iCloud Calendar

**Issue:** Authentication fails

**Solution:**
- Use app-specific password (not main password)
- Verify Apple ID is correct
- Check Calendar is enabled in iCloud settings

**Issue:** Calendar not found

**Solution:**
- Leave `calendar_name` empty for default
- List calendars to verify name
- Check calendar sharing settings

### CalDAV

**Issue:** Connection timeout

**Solution:**
- Verify URL is accessible
- Check firewall settings
- Test with curl: `curl -u user:pass https://caldav.example.com/`

## Future Enhancements

- [ ] Automatic posting at scheduled time (webhooks/workers)
- [ ] Multiple accounts per provider
- [ ] Two-way calendar sync
- [ ] Recurring schedules
- [ ] Team calendar sharing
- [ ] Calendar analytics

## API Reference

See [`/docs/CALENDAR_API.md`](../../../docs/CALENDAR_API.md) for complete API documentation.

## Integration Guide

See [`/docs/CALENDAR_INTEGRATION.md`](../../../docs/CALENDAR_INTEGRATION.md) for setup instructions and examples.

# Calendar Integration - Quick Start Guide

Get started with calendar scheduling in 5 minutes!

## Prerequisites

- SupoClip backend and frontend running
- PostgreSQL database
- (Optional) Google Cloud account for Google Calendar

## Step 1: Install Dependencies

```bash
cd backend
uv sync
```

This installs:
- `google-api-python-client` - Google Calendar API
- `google-auth-oauthlib` - OAuth 2.0
- `caldav` - CalDAV protocol
- `icalendar` - Calendar format
- `pytz` - Timezones

## Step 2: Run Database Migration

```bash
# Using psql
psql -U postgres -d supoclip < backend/migrations/001_add_calendar_tables.sql

# Or with Docker
docker exec -i supoclip-postgres psql -U postgres -d supoclip < backend/migrations/001_add_calendar_tables.sql
```

This creates two tables:
- `calendar_credentials` - Stores calendar credentials
- `scheduled_posts` - Stores scheduled posts

## Step 3: Choose Your Calendar Service

### Option A: iCloud Calendar (Easiest)

No backend configuration needed! Users just need:

1. Go to https://appleid.apple.com
2. Sign in
3. Security → App-Specific Passwords
4. Generate password for "SupoClip"
5. Enter Apple ID + password in frontend

**Skip to Step 5**

### Option B: Google Calendar (More Features)

Requires one-time OAuth setup:

1. **Go to Google Cloud Console**
   - https://console.cloud.google.com/

2. **Create/Select Project**
   - Click "Select a project" → "New Project"
   - Name it "SupoClip"

3. **Enable Calendar API**
   - APIs & Services → Library
   - Search "Google Calendar API"
   - Click "Enable"

4. **Create OAuth Credentials**
   - APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client ID
   - Application type: Web application
   - Name: SupoClip
   - Authorized redirect URIs:
     - `http://localhost:3000/auth/google/callback`
   - Save Client ID and Secret

5. **Add to backend/.env**
   ```bash
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
   ```

### Option C: Generic CalDAV

Works with Nextcloud, OwnCloud, etc. No backend setup needed!

Users enter:
- CalDAV URL (e.g., `https://nextcloud.example.com/remote.php/dav`)
- Username
- Password

## Step 4: Configure Frontend

Add to `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Step 5: Restart Services

```bash
# Terminal 1 - Backend
cd backend
uvicorn src.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Step 6: Connect Your Calendar

1. **Open calendar page**
   - http://localhost:3000/calendar

2. **Click "Add Calendar"**

3. **Choose your provider:**

   **For Google:**
   - Select "Google Calendar"
   - Click "Connect Google Calendar"
   - Sign in and authorize
   - Done!

   **For iCloud:**
   - Select "iCloud Calendar"
   - Enter Apple ID email
   - Enter app-specific password (from Step 3)
   - Click "Connect iCloud Calendar"
   - Done!

   **For CalDAV:**
   - Select "CalDAV (Generic)"
   - Enter CalDAV URL
   - Enter username and password
   - Click "Connect CalDAV Calendar"
   - Done!

## Step 7: Schedule Your First Post

### Option 1: Use the UI

1. Go to a task with clips: `http://localhost:3000/tasks/{task_id}`
2. Find the clip you want to schedule
3. Look for the calendar scheduling component
4. Select date and time
5. Click "Schedule Post"

### Option 2: Use the API

```bash
# Get your clip ID from a task
curl "http://localhost:8000/tasks/{task_id}/clips" \
  -H "user_id: your_user_id" \
  --cookie "session=your_session"

# Schedule the clip
curl -X POST "http://localhost:8000/calendar/schedule" \
  -H "Content-Type: application/json" \
  -H "user_id: your_user_id" \
  --cookie "session=your_session" \
  -d '{
    "clip_id": "clip_uuid",
    "scheduled_time": "2025-11-15T10:00:00Z"
  }'
```

## Step 8: View Scheduled Posts

1. Go to http://localhost:3000/calendar
2. Click "Scheduled Posts" tab
3. See all your scheduled posts grouped by date
4. Filter by status (scheduled, published, cancelled)

## Verify It Works

1. **Check your calendar**
   - Open Google Calendar or iCloud Calendar
   - You should see a 5-minute event at the scheduled time
   - Event title: "Post Clip: {filename}"
   - Description contains clip details

2. **Check the API**
   ```bash
   curl "http://localhost:8000/calendar/events?status=scheduled" \
     -H "user_id: your_user_id" \
     --cookie "session=your_session"
   ```

## Troubleshooting

### "Failed to load calendar providers"

**Check:**
- Backend is running (`http://localhost:8000/health/db`)
- User is authenticated (check session cookie)
- Database migration was applied

### "Invalid credentials" (iCloud)

**Fix:**
- Must use app-specific password, not main password
- Generate at https://appleid.apple.com
- Verify Apple ID email is correct

### "OAuth URL generation fails" (Google)

**Fix:**
- Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
- Verify Calendar API is enabled in Google Cloud Console
- Check redirect URI is authorized

### "Calendar not found" (CalDAV)

**Fix:**
- Leave `calendar_name` field empty to use default
- Try with different calendar name
- Check calendar exists in your CalDAV server

## Next Steps

### Integrate into Your Workflow

Add the scheduler component to your clip views:

```tsx
import { CalendarScheduler } from "@/components/calendar-scheduler";

function ClipCard({ clip }) {
  return (
    <div>
      <video src={clip.url} controls />

      <CalendarScheduler
        clipId={clip.id}
        clipTitle={clip.filename}
        onScheduled={() => {
          toast.success("Clip scheduled!");
        }}
      />
    </div>
  );
}
```

### Bulk Scheduling

Schedule multiple clips at once:

```typescript
const clipIds = ["clip1", "clip2", "clip3"];
const baseTime = new Date("2025-11-15T10:00:00Z");

for (let i = 0; i < clipIds.length; i++) {
  const scheduledTime = new Date(baseTime.getTime() + i * 3600000); // 1 hour apart

  await fetch('/calendar/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      clip_id: clipIds[i],
      scheduled_time: scheduledTime.toISOString(),
    }),
  });
}
```

## Resources

- **Full Documentation:** `/docs/CALENDAR_INTEGRATION.md`
- **API Reference:** `/docs/CALENDAR_API.md`
- **Interactive API Docs:** `http://localhost:8000/docs`
- **Frontend Example:** `http://localhost:3000/calendar`

## Common Use Cases

### 1. Schedule Week's Content

```bash
# Monday 9am
curl -X POST http://localhost:8000/calendar/schedule -d '{
  "clip_id": "clip1",
  "scheduled_time": "2025-11-18T09:00:00Z"
}'

# Wednesday 9am
curl -X POST http://localhost:8000/calendar/schedule -d '{
  "clip_id": "clip2",
  "scheduled_time": "2025-11-20T09:00:00Z"
}'

# Friday 9am
curl -X POST http://localhost:8000/calendar/schedule -d '{
  "clip_id": "clip3",
  "scheduled_time": "2025-11-22T09:00:00Z"
}'
```

### 2. Cancel Scheduled Post

```bash
curl -X PATCH http://localhost:8000/calendar/events/{post_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'
```

### 3. Reschedule Post

```bash
curl -X PATCH http://localhost:8000/calendar/events/{post_id} \
  -H "Content-Type: application/json" \
  -d '{"scheduled_time": "2025-11-16T15:00:00Z"}'
```

### 4. View This Week's Schedule

```bash
curl "http://localhost:8000/calendar/events?start_date=2025-11-11T00:00:00Z&end_date=2025-11-17T23:59:59Z"
```

## Tips

1. **Test with iCloud first** - Easiest to set up, no OAuth required
2. **Use UTC times** - All times are stored in UTC
3. **Check your calendar** - Events appear immediately in your calendar app
4. **Set reminders** - Default 10-minute reminder before each post
5. **Use status filters** - Keep track of published/cancelled posts

## Need Help?

1. Check `/docs/CALENDAR_INTEGRATION.md` for detailed docs
2. Review API docs at `http://localhost:8000/docs`
3. Check troubleshooting section above
4. Open GitHub issue for bugs

---

**You're all set!** 🎉

Your calendar integration is now ready to use. Schedule your first clip and watch it appear in your calendar!

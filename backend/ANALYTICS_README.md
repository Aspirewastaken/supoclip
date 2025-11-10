# Analytics System Documentation

## Overview

The SupoClip analytics system tracks performance metrics for generated video clips across multiple social media platforms. It provides comprehensive analytics including view counts, engagement metrics, and watch time statistics.

## Database Schema

### Tables

#### `clip_views`
Tracks view metrics for clips across different social media platforms.

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) | Primary key (UUID) |
| `clip_id` | VARCHAR(36) | Foreign key to `generated_clips.id` |
| `platform` | VARCHAR(50) | Platform name (tiktok, youtube_shorts, instagram_reels, etc.) |
| `views` | INTEGER | Number of views (≥ 0) |
| `likes` | INTEGER | Number of likes (≥ 0) |
| `comments` | INTEGER | Number of comments (≥ 0) |
| `shares` | INTEGER | Number of shares (≥ 0) |
| `date` | DATE | Date when metrics were recorded |
| `created_at` | TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | Record update timestamp |

**Indexes:**
- `idx_clip_views_clip_id` on `clip_id`
- `idx_clip_views_platform` on `platform`
- `idx_clip_views_date` on `date`
- `idx_clip_views_created_at` on `created_at`

#### `clip_performance`
Tracks engagement and watch metrics for clips. One record per clip.

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) | Primary key (UUID) |
| `clip_id` | VARCHAR(36) | Foreign key to `generated_clips.id` (UNIQUE) |
| `engagement_rate` | FLOAT | Engagement rate percentage (0-100) |
| `watch_time` | FLOAT | Average watch time in seconds (≥ 0) |
| `retention_rate` | FLOAT | Retention rate percentage (0-100) |
| `created_at` | TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | Record update timestamp |

**Indexes:**
- `idx_clip_performance_clip_id` on `clip_id`
- `idx_clip_performance_engagement_rate` on `engagement_rate`
- `idx_clip_performance_retention_rate` on `retention_rate`

**Unique Constraint:** Each clip can only have one performance record (enforced via `UNIQUE(clip_id)`)

### Supported Platforms

- `tiktok` - TikTok
- `youtube_shorts` - YouTube Shorts
- `instagram_reels` - Instagram Reels
- `facebook` - Facebook
- `twitter` - Twitter/X
- `linkedin` - LinkedIn

## Migration

### Running the Migration

To apply the analytics tables to your database:

```bash
# From the backend directory
cd backend

# Run the migration
python run_migration.py migrations/001_add_analytics_tables.sql
```

### Migration Script Details

The migration script (`001_add_analytics_tables.sql`):
- Creates `clip_views` and `clip_performance` tables
- Adds appropriate indexes for query performance
- Sets up foreign key constraints to `generated_clips`
- Adds check constraints for data validation
- Creates triggers for automatic `updated_at` timestamp updates
- Includes table and column comments for documentation

### Rollback

To remove the analytics tables:

```sql
DROP TABLE IF EXISTS clip_performance CASCADE;
DROP TABLE IF EXISTS clip_views CASCADE;
```

## API Endpoints

All analytics endpoints are prefixed with `/analytics`.

### 1. Record Metrics

**POST** `/analytics/record`

Record view metrics and/or performance metrics for a clip.

#### Request Body

```json
{
  "view_metrics": {
    "clip_id": "123e4567-e89b-12d3-a456-426614174000",
    "platform": "tiktok",
    "views": 1500,
    "likes": 120,
    "comments": 15,
    "shares": 45,
    "date": "2025-11-10"  // Optional, defaults to today
  },
  "performance_metrics": {
    "clip_id": "123e4567-e89b-12d3-a456-426614174000",
    "engagement_rate": 12.5,
    "watch_time": 8.3,
    "retention_rate": 75.2
  }
}
```

**Note:** Either `view_metrics` or `performance_metrics` (or both) must be provided.

#### Response

```json
{
  "message": "Metrics recorded successfully",
  "results": {
    "view_metrics": {
      "status": "created",  // or "updated"
      "id": "record-uuid"
    },
    "performance_metrics": {
      "status": "created",  // or "updated"
      "id": "record-uuid"
    }
  }
}
```

#### Behavior

- **View Metrics**: If a record already exists for the same `clip_id`, `platform`, and `date`, it will be updated. Otherwise, a new record is created.
- **Performance Metrics**: If a performance record already exists for the `clip_id`, it will be updated. Otherwise, a new record is created (one performance record per clip).

#### Example Usage

```bash
# Record TikTok metrics
curl -X POST http://localhost:8000/analytics/record \
  -H "Content-Type: application/json" \
  -d '{
    "view_metrics": {
      "clip_id": "abc-123",
      "platform": "tiktok",
      "views": 5000,
      "likes": 450,
      "comments": 32,
      "shares": 89
    }
  }'

# Record performance metrics
curl -X POST http://localhost:8000/analytics/record \
  -H "Content-Type: application/json" \
  -d '{
    "performance_metrics": {
      "clip_id": "abc-123",
      "engagement_rate": 15.2,
      "watch_time": 12.5,
      "retention_rate": 82.3
    }
  }'

# Record both at once
curl -X POST http://localhost:8000/analytics/record \
  -H "Content-Type: application/json" \
  -d '{
    "view_metrics": {
      "clip_id": "abc-123",
      "platform": "youtube_shorts",
      "views": 3200,
      "likes": 280,
      "comments": 18,
      "shares": 56
    },
    "performance_metrics": {
      "clip_id": "abc-123",
      "engagement_rate": 11.8,
      "watch_time": 9.7,
      "retention_rate": 71.5
    }
  }'
```

---

### 2. Get Clip Performance

**GET** `/analytics/clip/{clip_id}`

Get comprehensive performance metrics for a specific clip.

#### Path Parameters

- `clip_id` (string): UUID of the clip

#### Response

```json
{
  "clip_id": "123e4567-e89b-12d3-a456-426614174000",
  "clip_filename": "clip_1_transition.mp4",
  "clip_duration": 15.5,
  "total_views": 8700,
  "total_likes": 830,
  "total_comments": 65,
  "total_shares": 190,
  "avg_engagement_rate": 12.5,
  "avg_watch_time": 10.2,
  "avg_retention_rate": 78.4,
  "platforms": ["tiktok", "youtube_shorts", "instagram_reels"],
  "view_metrics_by_platform": {
    "tiktok": {
      "views": 5000,
      "likes": 450,
      "comments": 32,
      "shares": 89,
      "date": "2025-11-10",
      "last_updated": "2025-11-10T14:30:00Z"
    },
    "youtube_shorts": {
      "views": 3200,
      "likes": 280,
      "comments": 18,
      "shares": 56,
      "date": "2025-11-10",
      "last_updated": "2025-11-10T14:30:00Z"
    },
    "instagram_reels": {
      "views": 500,
      "likes": 100,
      "comments": 15,
      "shares": 45,
      "date": "2025-11-10",
      "last_updated": "2025-11-10T14:30:00Z"
    }
  },
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T14:30:00Z"
}
```

#### Example Usage

```bash
curl http://localhost:8000/analytics/clip/abc-123
```

---

### 3. Get Dashboard Statistics

**GET** `/analytics/dashboard`

Get aggregated analytics dashboard statistics.

#### Query Parameters

- `user_id` (optional): Filter by user ID
- `task_id` (optional): Filter by task ID
- `limit` (optional): Number of top performing clips to return (default: 10)

#### Response

```json
{
  "total_clips": 45,
  "total_clips_with_metrics": 38,
  "total_views": 125000,
  "total_likes": 12500,
  "total_comments": 850,
  "total_shares": 3200,
  "total_engagements": 16550,
  "avg_engagement_rate": 13.2,
  "avg_watch_time": 11.5,
  "avg_retention_rate": 76.8,
  "top_performing_clips": [
    {
      "clip_id": "clip-1-uuid",
      "filename": "clip_1_transition.mp4",
      "duration": 15.5,
      "relevance_score": 0.95,
      "total_views": 15000,
      "total_likes": 1800,
      "total_comments": 120,
      "total_shares": 450,
      "engagement_rate": 15.8,
      "retention_rate": 82.5,
      "video_url": "/clips/clip_1_transition.mp4"
    },
    // ... more clips
  ],
  "platform_breakdown": {
    "tiktok": {
      "clips_count": 25,
      "total_views": 75000,
      "total_likes": 7500,
      "total_comments": 520,
      "total_shares": 2100,
      "total_engagements": 10120
    },
    "youtube_shorts": {
      "clips_count": 20,
      "total_views": 35000,
      "total_likes": 3500,
      "total_comments": 230,
      "total_shares": 800,
      "total_engagements": 4530
    },
    "instagram_reels": {
      "clips_count": 18,
      "total_views": 15000,
      "total_likes": 1500,
      "total_comments": 100,
      "total_shares": 300,
      "total_engagements": 1900
    }
  }
}
```

#### Example Usage

```bash
# Get overall dashboard stats
curl http://localhost:8000/analytics/dashboard

# Filter by user
curl http://localhost:8000/analytics/dashboard?user_id=user-123

# Filter by task
curl http://localhost:8000/analytics/dashboard?task_id=task-456

# Get top 5 clips only
curl http://localhost:8000/analytics/dashboard?limit=5

# Combine filters
curl "http://localhost:8000/analytics/dashboard?user_id=user-123&limit=20"
```

## Usage Examples

### Python Client

```python
import httpx
from datetime import date

# Record metrics for a clip on TikTok
async def record_tiktok_metrics(clip_id: str, views: int, likes: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/analytics/record",
            json={
                "view_metrics": {
                    "clip_id": clip_id,
                    "platform": "tiktok",
                    "views": views,
                    "likes": likes,
                    "comments": 0,
                    "shares": 0,
                    "date": date.today().isoformat()
                }
            }
        )
        return response.json()

# Get clip performance
async def get_clip_analytics(clip_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/analytics/clip/{clip_id}"
        )
        return response.json()

# Get dashboard for a user
async def get_user_dashboard(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/analytics/dashboard?user_id={user_id}"
        )
        return response.json()
```

### JavaScript/TypeScript Client

```typescript
// Record metrics
async function recordMetrics(clipId: string, platform: string, metrics: any) {
  const response = await fetch('http://localhost:8000/analytics/record', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      view_metrics: {
        clip_id: clipId,
        platform: platform,
        ...metrics
      }
    })
  });
  return response.json();
}

// Get clip performance
async function getClipPerformance(clipId: string) {
  const response = await fetch(`http://localhost:8000/analytics/clip/${clipId}`);
  return response.json();
}

// Get dashboard
async function getDashboard(userId?: string, limit: number = 10) {
  const params = new URLSearchParams();
  if (userId) params.append('user_id', userId);
  params.append('limit', limit.toString());

  const response = await fetch(
    `http://localhost:8000/analytics/dashboard?${params}`
  );
  return response.json();
}
```

## Best Practices

### Recording Metrics

1. **Update Frequency**: Record metrics daily or whenever you fetch updated stats from social platforms
2. **Platform Names**: Always use lowercase platform names from the supported list
3. **Batch Updates**: You can record metrics for multiple platforms by making separate API calls
4. **Date Tracking**: If recording historical data, specify the `date` field explicitly

### Performance Considerations

1. **Indexes**: The migration includes appropriate indexes for common queries
2. **Unique Records**: View metrics are unique by `(clip_id, platform, date)` combination
3. **Performance Records**: Each clip has exactly one performance record (automatically enforced)
4. **Cascading Deletes**: Analytics data is automatically deleted when clips are removed

### Data Validation

All endpoints include validation:
- View counts, likes, comments, and shares must be ≥ 0
- Engagement rate and retention rate must be between 0-100
- Platform names must be from the supported list
- Clip IDs must reference existing clips

## Troubleshooting

### Common Issues

**Issue: "Clip not found" error**
- Verify the clip_id exists in the `generated_clips` table
- Check that you're using the correct UUID format

**Issue: Platform validation error**
- Ensure platform name is lowercase
- Use supported platform names only

**Issue: Migration fails**
- Check database connection in `.env`
- Verify PostgreSQL version (15+ recommended)
- Ensure `uuid-ossp` extension is enabled

### Debugging

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check database directly:

```sql
-- Check if tables exist
SELECT tablename FROM pg_tables WHERE tablename LIKE 'clip_%';

-- View recent metrics
SELECT * FROM clip_views ORDER BY created_at DESC LIMIT 10;

-- Check performance records
SELECT * FROM clip_performance ORDER BY engagement_rate DESC LIMIT 10;
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The analytics endpoints are grouped under the "analytics" tag for easy access.

# Analytics System - Quick Reference

## Database Schema

### Table: `clip_views`
Tracks view metrics across platforms (one record per clip/platform/date).

```sql
CREATE TABLE clip_views (
    id VARCHAR(36) PRIMARY KEY,
    clip_id VARCHAR(36) REFERENCES generated_clips(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    views INTEGER DEFAULT 0 CHECK (views >= 0),
    likes INTEGER DEFAULT 0 CHECK (likes >= 0),
    comments INTEGER DEFAULT 0 CHECK (comments >= 0),
    shares INTEGER DEFAULT 0 CHECK (shares >= 0),
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Supported Platforms**: `tiktok`, `youtube_shorts`, `instagram_reels`, `facebook`, `twitter`, `linkedin`

### Table: `clip_performance`
Tracks engagement and watch metrics (one record per clip).

```sql
CREATE TABLE clip_performance (
    id VARCHAR(36) PRIMARY KEY,
    clip_id VARCHAR(36) REFERENCES generated_clips(id) ON DELETE CASCADE UNIQUE,
    engagement_rate FLOAT DEFAULT 0.0 CHECK (engagement_rate >= 0 AND engagement_rate <= 100),
    watch_time FLOAT DEFAULT 0.0 CHECK (watch_time >= 0),
    retention_rate FLOAT DEFAULT 0.0 CHECK (retention_rate >= 0 AND retention_rate <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### 1. POST `/analytics/record`
Record view and/or performance metrics for a clip.

**Request:**
```json
{
  "view_metrics": {
    "clip_id": "uuid",
    "platform": "tiktok",
    "views": 1500,
    "likes": 120,
    "comments": 15,
    "shares": 45,
    "date": "2025-11-10"
  },
  "performance_metrics": {
    "clip_id": "uuid",
    "engagement_rate": 12.5,
    "watch_time": 8.3,
    "retention_rate": 75.2
  }
}
```

**Response:**
```json
{
  "message": "Metrics recorded successfully",
  "results": {
    "view_metrics": {"status": "created", "id": "uuid"},
    "performance_metrics": {"status": "updated", "id": "uuid"}
  }
}
```

### 2. GET `/analytics/clip/{clip_id}`
Get comprehensive performance metrics for a specific clip.

**Response:**
```json
{
  "clip_id": "uuid",
  "clip_filename": "clip_1.mp4",
  "clip_duration": 15.5,
  "total_views": 8700,
  "total_likes": 830,
  "total_comments": 65,
  "total_shares": 190,
  "avg_engagement_rate": 12.5,
  "avg_watch_time": 10.2,
  "avg_retention_rate": 78.4,
  "platforms": ["tiktok", "youtube_shorts"],
  "view_metrics_by_platform": {
    "tiktok": {
      "views": 5000,
      "likes": 450,
      "comments": 32,
      "shares": 89,
      "date": "2025-11-10",
      "last_updated": "2025-11-10T14:30:00Z"
    }
  }
}
```

### 3. GET `/analytics/dashboard`
Get aggregated analytics dashboard statistics.

**Query Parameters:**
- `user_id` (optional) - Filter by user
- `task_id` (optional) - Filter by task
- `limit` (optional) - Number of top clips (default: 10)

**Response:**
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
      "clip_id": "uuid",
      "filename": "clip_1.mp4",
      "duration": 15.5,
      "total_views": 15000,
      "engagement_rate": 15.8,
      "video_url": "/clips/clip_1.mp4"
    }
  ],
  "platform_breakdown": {
    "tiktok": {
      "clips_count": 25,
      "total_views": 75000,
      "total_engagements": 10120
    }
  }
}
```

## Migration

### Run Migration
```bash
cd backend
python run_migration.py migrations/001_add_analytics_tables.sql
```

### Verify Tables
```sql
SELECT tablename FROM pg_tables WHERE tablename LIKE 'clip_%';
```

## File Locations

- **Migration Script**: `/home/user/supoclip/backend/migrations/001_add_analytics_tables.sql`
- **Migration Runner**: `/home/user/supoclip/backend/run_migration.py`
- **API Routes**: `/home/user/supoclip/backend/src/api/routes/analytics.py`
- **Models**: `/home/user/supoclip/backend/src/models.py` (lines 178-225)
- **Main App**: `/home/user/supoclip/backend/src/main.py` (analytics router included)
- **Full Documentation**: `/home/user/supoclip/backend/ANALYTICS_README.md`

## Quick Start

1. **Apply Migration:**
   ```bash
   cd /home/user/supoclip/backend
   python run_migration.py migrations/001_add_analytics_tables.sql
   ```

2. **Start Backend:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **View API Docs:**
   Open http://localhost:8000/docs and look for "analytics" tag

4. **Record Metrics:**
   ```bash
   curl -X POST http://localhost:8000/analytics/record \
     -H "Content-Type: application/json" \
     -d '{
       "view_metrics": {
         "clip_id": "your-clip-id",
         "platform": "tiktok",
         "views": 1000,
         "likes": 100
       }
     }'
   ```

5. **View Dashboard:**
   ```bash
   curl http://localhost:8000/analytics/dashboard
   ```

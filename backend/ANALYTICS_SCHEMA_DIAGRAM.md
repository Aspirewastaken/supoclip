# Analytics Database Schema Diagram

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ANALYTICS SYSTEM SCHEMA                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────┐
│     generated_clips        │  (Existing Table)
├────────────────────────────┤
│ id (PK)                    │◄─────────┐
│ task_id (FK)               │          │
│ filename                   │          │
│ file_path                  │          │
│ start_time                 │          │
│ end_time                   │          │
│ duration                   │          │
│ text                       │          │
│ relevance_score            │          │
│ reasoning                  │          │
│ clip_order                 │          │
│ created_at                 │          │
│ updated_at                 │          │
└────────────────────────────┘          │
                                         │
                                         │
                                         │
                     ┌───────────────────┴────────────────────┐
                     │                                        │
                     │                                        │
                     │                                        │
┌────────────────────▼───────────────┐     ┌────────────────▼───────────────────┐
│        clip_views                  │     │      clip_performance              │
├────────────────────────────────────┤     ├────────────────────────────────────┤
│ id (PK)                            │     │ id (PK)                            │
│ clip_id (FK) → generated_clips.id  │     │ clip_id (FK,UQ) → generated_clips  │
│ platform                           │     │ engagement_rate                    │
│ views                              │     │ watch_time                         │
│ likes                              │     │ retention_rate                     │
│ comments                           │     │ created_at                         │
│ shares                             │     │ updated_at                         │
│ date                               │     └────────────────────────────────────┘
│ created_at                         │
│ updated_at                         │     Cardinality: 1 to 0..1
└────────────────────────────────────┘     (One clip has zero or one
                                            performance record)
Cardinality: 1 to Many
(One clip can have multiple view
 records across platforms/dates)


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RELATIONSHIPS EXPLAINED                                │
└─────────────────────────────────────────────────────────────────────────────────┘

1. generated_clips → clip_views (1:N)
   - One clip can have MULTIPLE view records
   - Each record represents metrics for a specific platform on a specific date
   - Unique constraint: (clip_id, platform, date)
   - Example: A clip posted on TikTok, YouTube Shorts, and Instagram will have
     3 view records (one per platform)

2. generated_clips → clip_performance (1:0..1)
   - One clip can have ZERO or ONE performance record
   - Aggregated engagement metrics across all platforms
   - Unique constraint: clip_id
   - Example: Stores overall engagement rate, avg watch time, retention rate


┌─────────────────────────────────────────────────────────────────────────────────┐
│                               INDEXES                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

clip_views:
  ├─ idx_clip_views_clip_id (clip_id)
  ├─ idx_clip_views_platform (platform)
  ├─ idx_clip_views_date (date)
  └─ idx_clip_views_created_at (created_at)

clip_performance:
  ├─ idx_clip_performance_clip_id (clip_id)
  ├─ idx_clip_performance_engagement_rate (engagement_rate)
  └─ idx_clip_performance_retention_rate (retention_rate)


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW EXAMPLE                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: Clip is generated
  generated_clips:
    ├─ id: "clip-abc-123"
    ├─ filename: "clip_1_transition.mp4"
    └─ duration: 15.5 seconds

Step 2: Post clip to TikTok (Day 1)
  clip_views:
    ├─ clip_id: "clip-abc-123"
    ├─ platform: "tiktok"
    ├─ views: 1000
    ├─ likes: 100
    └─ date: 2025-11-10

Step 3: Post clip to YouTube Shorts (Day 1)
  clip_views:
    ├─ clip_id: "clip-abc-123"
    ├─ platform: "youtube_shorts"
    ├─ views: 500
    ├─ likes: 50
    └─ date: 2025-11-10

Step 4: Update TikTok metrics (Day 2)
  clip_views:
    ├─ clip_id: "clip-abc-123"
    ├─ platform: "tiktok"
    ├─ views: 5000  ← Updated
    ├─ likes: 450   ← Updated
    └─ date: 2025-11-11  ← New date = new record

Step 5: Record overall performance metrics
  clip_performance:
    ├─ clip_id: "clip-abc-123"
    ├─ engagement_rate: 12.5%
    ├─ watch_time: 10.2 seconds
    └─ retention_rate: 78.4%

Result: Dashboard shows
  - Total views: 6500 (sum across all platforms and dates)
  - Total likes: 600
  - Platforms: ["tiktok", "youtube_shorts"]
  - Engagement: 12.5%


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QUERY PATTERNS                                         │
└─────────────────────────────────────────────────────────────────────────────────┘

# Get total views for a clip across all platforms
SELECT SUM(views) as total_views
FROM clip_views
WHERE clip_id = 'clip-abc-123';

# Get latest metrics for each platform
SELECT DISTINCT ON (platform) *
FROM clip_views
WHERE clip_id = 'clip-abc-123'
ORDER BY platform, date DESC;

# Get top performing clips
SELECT gc.id, gc.filename,
       SUM(cv.views) as total_views,
       cp.engagement_rate
FROM generated_clips gc
LEFT JOIN clip_views cv ON gc.id = cv.clip_id
LEFT JOIN clip_performance cp ON gc.id = cp.clip_id
GROUP BY gc.id, gc.filename, cp.engagement_rate
ORDER BY total_views DESC
LIMIT 10;

# Get platform breakdown
SELECT cv.platform,
       COUNT(DISTINCT cv.clip_id) as clips_count,
       SUM(cv.views) as total_views,
       SUM(cv.likes + cv.comments + cv.shares) as total_engagements
FROM clip_views cv
GROUP BY cv.platform
ORDER BY total_views DESC;

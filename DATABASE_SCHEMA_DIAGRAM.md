# SupoClip Database Schema Diagram

## Complete Entity Relationship Diagram

This diagram shows all tables, relationships, and key constraints in the SupoClip database.

```mermaid
erDiagram
    %% Core User Management
    users ||--o{ tasks : "creates"
    users ||--o{ webhooks : "configures"
    users ||--o{ experiments : "runs"
    users ||--o{ calendar_credentials : "connects"
    users ||--o{ social_media_accounts : "links"
    users ||--o{ usage_tracking : "tracks"
    users ||--o{ session : "authenticates"
    users ||--o{ account : "has_oauth"

    %% Video Processing Pipeline
    sources ||--o{ tasks : "processes"
    tasks ||--o{ generated_clips : "produces"
    tasks }o--|| users : "belongs_to"
    tasks }o--o| sources : "uses"

    %% Clip Analytics
    generated_clips ||--o{ clip_views : "tracked_on"
    generated_clips ||--o| clip_performance : "has_metrics"
    generated_clips ||--o{ experiment_results : "tested_in"

    %% A/B Testing
    experiments ||--o{ experiment_results : "measures"
    experiment_results }o--|| generated_clips : "tests"

    %% Webhook System
    webhooks ||--o{ webhook_deliveries : "sends"

    %% Calendar Integration
    calendar_credentials ||--o{ scheduled_posts : "schedules"
    scheduled_posts }o--|| generated_clips : "publishes"
    scheduled_posts }o--|| tasks : "for_task"

    %% Social Media Integration
    social_media_accounts ||--o{ post_attempts : "uses_for_posting"
    social_scheduled_posts ||--o{ post_attempts : "attempts"
    social_scheduled_posts }o--|| generated_clips : "publishes"

    users {
        varchar_36 id PK "UUID"
        varchar_255 email UK "Unique email"
        varchar_255 name "Display name"
        boolean emailVerified "Email verified"
        varchar_500 image "Profile image URL"
        varchar_20 role "free|pro|admin"
        varchar_255 stripe_customer_id "Stripe customer"
        varchar_255 stripe_subscription_id "Subscription ID"
        varchar_20 subscription_status "active|inactive"
        timestamp subscription_current_period_end "Renewal date"
        varchar_100 default_font_family "TikTokSans-Regular"
        int default_font_size "24"
        varchar_7 default_font_color "#FFFFFF"
        timestamptz createdAt "Created timestamp"
        timestamptz updatedAt "Updated timestamp"
    }

    tasks {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_36 source_id FK "→ sources.id"
        varchar_36_array generated_clips_ids "Clip UUIDs"
        varchar_20 status "pending|processing|completed|failed"
        int progress "0-100%"
        text progress_message "Status message"
        varchar_100 font_family "Custom font"
        int font_size "Font size"
        varchar_7 font_color "Hex color"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    sources {
        varchar_36 id PK "UUID"
        varchar_20 type "youtube|video_url"
        varchar_500 title "Video title"
        varchar_1000 url "Source URL"
        varchar_255 channel_name "Channel/uploader"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    generated_clips {
        varchar_36 id PK "UUID"
        varchar_36 task_id FK "→ tasks.id"
        varchar_255 filename "File name"
        varchar_500 file_path "Local path"
        varchar_1000 cdn_url "CDN URL"
        varchar_20 start_time "MM:SS"
        varchar_20 end_time "MM:SS"
        float duration "Seconds"
        text text "Transcript"
        float relevance_score "0.0-1.0"
        text reasoning "AI reasoning"
        int clip_order "Order in task"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    webhooks {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_1000 url "Webhook URL"
        text_array events "Event types"
        varchar_255 secret "HMAC secret"
        boolean active "Is active"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    webhook_deliveries {
        varchar_36 id PK "UUID"
        varchar_36 webhook_id FK "→ webhooks.id"
        varchar_50 event_type "Event name"
        jsonb payload "Event data"
        varchar_20 status "pending|success|failed"
        int response_code "HTTP code"
        text response_body "Response"
        int attempts "Attempt count"
        int max_attempts "Max retries (3)"
        timestamptz next_retry_at "Next retry"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
        timestamptz delivered_at "Delivered"
    }

    experiments {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_255 name "Experiment name"
        text description "Description"
        jsonb variations "Variation configs"
        varchar_20 status "running|paused|completed"
        varchar_36 winner_variation_id "Winner ID"
        float confidence_threshold "0.0-1.0 (0.95)"
        timestamptz started_at "Started"
        timestamptz completed_at "Completed"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    experiment_results {
        varchar_36 id PK "UUID"
        varchar_36 experiment_id FK "→ experiments.id"
        varchar_36 variation_id "Variation ID"
        varchar_36 clip_id FK "→ generated_clips.id"
        int views "View count"
        int clicks "Click count"
        int conversions "Conversions"
        int shares "Share count"
        int likes "Like count"
        int comments "Comment count"
        float click_through_rate "0.0-1.0"
        float conversion_rate "0.0-1.0"
        float engagement_rate "0.0-1.0"
        float avg_watch_time "Seconds"
        float watch_completion_rate "0.0-1.0"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    calendar_credentials {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_20 provider "google|icloud|caldav"
        text access_token "OAuth token"
        text refresh_token "Refresh token"
        timestamptz token_expiry "Token expires"
        varchar_500 caldav_url "CalDAV URL"
        varchar_255 caldav_username "CalDAV user"
        text caldav_password "CalDAV pass"
        varchar_255 calendar_name "Calendar name"
        jsonb metadata "Extra data"
        boolean is_active "Is active"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    scheduled_posts {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_36 clip_id FK "→ generated_clips.id"
        varchar_36 task_id FK "→ tasks.id"
        varchar_36 calendar_credential_id FK "→ calendar_credentials.id"
        varchar_500 calendar_event_id "Event ID"
        varchar_20 calendar_provider "Provider"
        timestamptz scheduled_time "Scheduled for"
        varchar_500 title "Post title"
        text description "Description"
        varchar_20 status "scheduled|published|failed|cancelled"
        jsonb clip_metadata "Metadata"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    social_media_accounts {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_20 platform "tiktok|instagram|youtube|twitter"
        varchar_255 platform_user_id "Platform user ID"
        varchar_255 platform_username "Username"
        text access_token "OAuth token"
        text refresh_token "Refresh token"
        timestamptz token_expires_at "Token expires"
        jsonb metadata "Platform data"
        boolean is_active "Is active"
        timestamptz last_used_at "Last used"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    social_scheduled_posts {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        varchar_36 clip_id FK "→ generated_clips.id"
        varchar_20_array platforms "Platforms"
        timestamptz scheduled_for "Scheduled for"
        text caption "Post caption"
        text_array hashtags "Hashtags"
        jsonb platform_config "Platform settings"
        varchar_20 status "scheduled|processing|completed|failed|cancelled"
        int max_retries "Max retries (3)"
        int retry_delay_seconds "Delay (300s)"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
        timestamptz processed_at "Processed"
    }

    post_attempts {
        varchar_36 id PK "UUID"
        varchar_36 scheduled_post_id FK "→ social_scheduled_posts.id"
        varchar_20 platform "Platform name"
        varchar_36 social_media_account_id FK "→ social_media_accounts.id"
        int attempt_number "Attempt #"
        varchar_20 status "pending|processing|success|failed"
        varchar_255 platform_post_id "Post ID"
        text platform_url "Post URL"
        jsonb response_data "API response"
        text error_message "Error message"
        varchar_100 error_code "Error code"
        timestamptz started_at "Started"
        timestamptz completed_at "Completed"
        timestamptz next_retry_at "Next retry"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    clip_views {
        varchar_36 id PK "UUID"
        varchar_36 clip_id FK "→ generated_clips.id"
        varchar_50 platform "tiktok|youtube_shorts|instagram_reels"
        int views "View count"
        int likes "Like count"
        int comments "Comment count"
        int shares "Share count"
        date date "Metrics date"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    clip_performance {
        varchar_36 id PK "UUID"
        varchar_36 clip_id FK_UK "→ generated_clips.id (UNIQUE)"
        float engagement_rate "0-100%"
        float watch_time "Avg watch seconds"
        float retention_rate "0-100%"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    usage_tracking {
        varchar_36 id PK "UUID"
        varchar_36 user_id FK "→ users.id"
        int month "1-12"
        int year "YYYY"
        int clips_generated "Clip count"
        timestamptz created_at "Created"
        timestamptz updated_at "Updated"
    }

    session {
        varchar_36 id PK "UUID"
        timestamptz expiresAt "Expires at"
        varchar_255 token UK "Session token"
        timestamptz createdAt "Created"
        timestamptz updatedAt "Updated"
        varchar_255 ipAddress "IP address"
        text userAgent "User agent"
        varchar_36 userId FK "→ users.id"
    }

    account {
        varchar_36 id PK "UUID"
        varchar_255 accountId "Account ID"
        varchar_255 providerId "Provider ID"
        varchar_36 userId FK "→ users.id"
        text accessToken "OAuth token"
        text refreshToken "Refresh token"
        text idToken "ID token"
        timestamptz accessTokenExpiresAt "Token expires"
        timestamptz refreshTokenExpiresAt "Refresh expires"
        text scope "OAuth scope"
        text password "Password hash"
        timestamptz createdAt "Created"
        timestamptz updatedAt "Updated"
    }
```

## Table Categories

### 🔐 Authentication & Users
- **users**: User accounts and profiles
- **session**: Active user sessions (Better Auth)
- **account**: OAuth provider accounts (Better Auth)
- **verification**: Email verification tokens (Better Auth)
- **usage_tracking**: Monthly quota tracking

### 🎬 Video Processing
- **sources**: Video source information (YouTube URLs, uploads)
- **tasks**: Processing jobs and their status
- **generated_clips**: Produced video clips with metadata

### 📊 Analytics & Performance
- **clip_views**: Per-platform view metrics (time-series)
- **clip_performance**: Aggregated engagement metrics
- **experiments**: A/B testing experiments
- **experiment_results**: Metrics for each variation

### 🔔 Notifications
- **webhooks**: User-configured webhook endpoints
- **webhook_deliveries**: Delivery attempts and status

### 📅 Scheduling
- **calendar_credentials**: Calendar OAuth credentials
- **scheduled_posts**: Calendar-based post scheduling
- **social_media_accounts**: Social platform OAuth
- **social_scheduled_posts**: Social media post scheduling
- **post_attempts**: Individual posting attempts

## Key Relationships

### One-to-Many (1:N)
```
users → tasks (one user has many tasks)
users → webhooks (one user has many webhooks)
tasks → generated_clips (one task produces many clips)
generated_clips → clip_views (one clip has many view records)
experiments → experiment_results (one experiment has many results)
webhooks → webhook_deliveries (one webhook has many deliveries)
social_media_accounts → post_attempts (one account has many attempts)
```

### One-to-One (1:1)
```
generated_clips ↔ clip_performance (one clip has one performance summary)
```

### Many-to-Many (N:M) via Junction Tables
```
generated_clips ⟷ experiments (via experiment_results)
  - One clip can be in multiple experiments
  - One experiment tests multiple clips
```

## Cascade Behaviors

### ON DELETE CASCADE
All child records are deleted when parent is deleted:
- Delete user → deletes all tasks, webhooks, experiments, etc.
- Delete task → deletes all generated_clips
- Delete webhook → deletes all webhook_deliveries
- Delete experiment → deletes all experiment_results

### ON DELETE SET NULL
Child record's foreign key is set to NULL:
- Delete source → sets tasks.source_id to NULL (task remains)

## Indexes Summary

### High-Cardinality Indexes (unique values)
- users.email (UNIQUE)
- session.token (UNIQUE)
- generated_clips.id (PRIMARY KEY on all tables)

### Query Optimization Indexes
- tasks(user_id, status) - Dashboard queries
- generated_clips(task_id, clip_order) - Clip listings
- clip_views(clip_id, date, platform) - Analytics queries
- webhook_deliveries(webhook_id, status, next_retry_at) - Retry queue
- experiment_results(experiment_id, conversion_rate) - Leaderboards
- usage_tracking(user_id, month, year) - Quota checks

### Timestamp Indexes
Almost all tables have `created_at` indexed for:
- Recent records queries
- Time-range analytics
- Pagination with LIMIT/OFFSET

## Triggers

All tables with timestamps have auto-update triggers:

### Snake_case Tables (Backend)
```sql
CREATE TRIGGER update_{table}_updated_at
    BEFORE UPDATE ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```
Applied to: tasks, sources, generated_clips, webhooks, webhook_deliveries,
experiments, experiment_results, usage_tracking, clip_views, clip_performance,
calendar_credentials, scheduled_posts, social_scheduled_posts,
social_media_accounts, post_attempts

### camelCase Tables (Better Auth)
```sql
CREATE TRIGGER update_{table}_updatedAt
    BEFORE UPDATE ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION update_updatedAt_column();
```
Applied to: users, session, account, verification

## Check Constraints

### Enum-like Constraints
```sql
-- User roles
CHECK (role IN ('free', 'pro', 'admin'))

-- Subscription status
CHECK (subscription_status IN ('active', 'inactive', 'canceled', 'past_due'))

-- Task status
CHECK (status IN ('pending', 'processing', 'completed', 'failed'))

-- Platform types
CHECK (platform IN ('tiktok', 'instagram', 'youtube', 'twitter'))

-- Calendar providers
CHECK (provider IN ('google', 'icloud', 'caldav'))
```

### Range Constraints
```sql
-- Task progress
CHECK (progress >= 0 AND progress <= 100)

-- Rates and percentages
CHECK (engagement_rate >= 0 AND engagement_rate <= 1)
CHECK (confidence_threshold >= 0 AND confidence_threshold <= 1)

-- Non-negative counts
CHECK (views >= 0)
CHECK (clips_generated >= 0)

-- Date ranges
CHECK (month >= 1 AND month <= 12)
CHECK (year >= 2020)
```

## Data Types

### UUIDs
All IDs use `VARCHAR(36)` for cross-platform compatibility:
```sql
id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text
```

### Timestamps
All timestamps use timezone-aware format:
```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
```

### Arrays
PostgreSQL native arrays for multi-value fields:
```sql
generated_clips_ids VARCHAR(36)[]  -- Array of UUIDs
platforms VARCHAR(20)[]            -- Array of platform names
hashtags TEXT[]                    -- Array of hashtags
```

### JSON
JSONB for flexible schema fields:
```sql
variations JSONB                   -- Experiment variations
metadata JSONB                     -- Platform-specific data
platform_config JSONB              -- Per-platform settings
```

## Query Patterns

### Dashboard - User's Recent Clips
```sql
SELECT gc.*, t.status, s.title as source_title
FROM generated_clips gc
JOIN tasks t ON gc.task_id = t.id
LEFT JOIN sources s ON t.source_id = s.id
WHERE t.user_id = $1
ORDER BY gc.created_at DESC
LIMIT 20;
```

### Analytics - Top Performing Clips
```sql
SELECT
    gc.id,
    gc.filename,
    SUM(cv.views) as total_views,
    SUM(cv.likes) as total_likes,
    cp.engagement_rate,
    cp.retention_rate
FROM generated_clips gc
LEFT JOIN clip_views cv ON gc.id = cv.clip_id
LEFT JOIN clip_performance cp ON gc.id = cp.clip_id
WHERE gc.task_id IN (SELECT id FROM tasks WHERE user_id = $1)
GROUP BY gc.id, gc.filename, cp.engagement_rate, cp.retention_rate
ORDER BY total_views DESC
LIMIT 10;
```

### Quota Check
```sql
SELECT
    u.role,
    ut.clips_generated,
    get_user_quota(u.role) as quota_limit,
    CASE
        WHEN get_user_quota(u.role) = -1 THEN -1  -- Unlimited
        ELSE get_user_quota(u.role) - COALESCE(ut.clips_generated, 0)
    END as remaining
FROM users u
LEFT JOIN usage_tracking ut ON u.id = ut.user_id
    AND ut.month = EXTRACT(MONTH FROM NOW())
    AND ut.year = EXTRACT(YEAR FROM NOW())
WHERE u.id = $1;
```

### Webhook Retry Queue
```sql
SELECT wd.*
FROM webhook_deliveries wd
JOIN webhooks w ON wd.webhook_id = w.id
WHERE w.active = true
    AND wd.status = 'failed'
    AND wd.attempts < wd.max_attempts
    AND wd.next_retry_at <= NOW()
ORDER BY wd.next_retry_at ASC
LIMIT 100;
```

## Migration Order

When setting up a fresh database:

1. **init.sql** - Base schema with core tables
2. **001_add_user_roles_and_quotas.sql** - Extend users table
3. **001_add_progress_fields.sql** - Extend tasks table
4. **001_add_webhooks_table.sql** - Add webhook system
5. **001_add_channel_name_to_sources.sql** - Extend sources
6. **001_add_analytics_tables.sql** - Add analytics
7. **001_add_calendar_tables.sql** - Add calendar integration
8. **add_cdn_url_to_clips.sql** - Extend generated_clips
9. **003_fix_scheduled_posts_conflict.sql** - Fix table conflict
10. **002_social_media_integrations.sql** - Add social media

## Performance Considerations

### Table Sizes (Estimated)

| Table | Growth Rate | Typical Size @ 1K Users |
|-------|-------------|-------------------------|
| users | Slow | 1K rows |
| tasks | Medium | 50K rows (50 per user) |
| generated_clips | High | 250K rows (5 clips per task) |
| clip_views | Very High | 2.5M rows (10 days × platform) |
| webhook_deliveries | High | 500K rows |
| experiment_results | Medium | 100K rows |
| usage_tracking | Slow | 12K rows (12 months per user) |

### Partitioning Recommendations

For tables growing beyond 10M rows:
```sql
-- Partition clip_views by month
CREATE TABLE clip_views_2025_11 PARTITION OF clip_views
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Partition webhook_deliveries by month
CREATE TABLE webhook_deliveries_2025_11 PARTITION OF webhook_deliveries
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

### Archival Strategy

Move old records to archive tables:
```sql
-- Archive clip_views older than 6 months
INSERT INTO clip_views_archive
SELECT * FROM clip_views WHERE date < NOW() - INTERVAL '6 months';

DELETE FROM clip_views WHERE date < NOW() - INTERVAL '6 months';
```

---

**Last Updated:** 2025-11-10
**Schema Version:** 1.0
**Total Tables:** 19
**Total Foreign Keys:** ~30
**Total Indexes:** ~60

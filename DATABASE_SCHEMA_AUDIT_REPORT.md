# Database Schema Audit Report
**Date:** 2025-11-10
**Auditor:** AGENT 5 - Database Schema Audit & Migration Verification
**Status:** ⚠️ CRITICAL ISSUES FOUND

---

## Executive Summary

The SupoClip database schema audit has identified **8 critical issues** and **12 recommendations** that require immediate attention. While the core schema is well-designed, there are significant conflicts between migrations, missing models, and inconsistencies that could cause production failures.

### Severity Breakdown
- 🔴 **CRITICAL (3)**: Schema conflicts that will cause failures
- 🟡 **HIGH (5)**: Missing models and indexes
- 🟢 **MEDIUM (12)**: Optimization opportunities

---

## 🔴 CRITICAL ISSUES

### 1. TABLE NAME CONFLICT: scheduled_posts (BLOCKING)
**Severity:** CRITICAL
**Impact:** Migration failure, data corruption risk

**Problem:**
Two different table definitions exist for `scheduled_posts`:

**Location 1:** `/backend/migrations/001_add_calendar_tables.sql`
```sql
CREATE TABLE scheduled_posts (
    id VARCHAR(36) PRIMARY KEY,
    calendar_event_id VARCHAR(500) NOT NULL,
    calendar_provider VARCHAR(20),
    scheduled_time TIMESTAMP WITH TIME ZONE,
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(20),
    -- Calendar-specific fields
)
```

**Location 2:** `/migrations/002_social_media_integrations.sql`
```sql
CREATE TABLE scheduled_posts (
    id VARCHAR(36) PRIMARY KEY,
    platforms VARCHAR(20)[] NOT NULL,  -- Array of platforms
    scheduled_for TIMESTAMP WITH TIME ZONE,
    caption TEXT,
    hashtags TEXT[],
    platform_config JSONB,
    -- Social media-specific fields
)
```

**Consequence:**
- Whichever migration runs last will DROP the first table
- Data loss will occur if not resolved
- Application code expects one schema but may receive another

**Resolution Required:**
Rename one table to avoid conflict:
- Option A: `calendar_scheduled_posts` and `social_scheduled_posts`
- Option B: `scheduled_calendar_events` and `scheduled_social_posts`
- Option C: Merge into single table with type discriminator

---

### 2. MISSING SQLAlchemy MODELS: Social Media Tables
**Severity:** CRITICAL
**Impact:** Backend cannot interact with social media tables

**Problem:**
The migration `/migrations/002_social_media_integrations.sql` creates these tables:
- `social_media_accounts`
- `post_attempts`

But **NO corresponding SQLAlchemy models exist** in `/backend/src/models.py`.

**Consequence:**
- Backend code cannot query or insert data into these tables
- ORM relationships are broken
- Any attempt to use these tables will fail with "table not found" errors

**Files Affected:**
- `/backend/src/models.py` - Missing `SocialMediaAccount` and `PostAttempts` classes

**Resolution Required:**
Add SQLAlchemy models for social media tables (see recommendations section).

---

### 3. MIGRATION ORDERING CONFLICT
**Severity:** CRITICAL
**Impact:** Non-deterministic migration order

**Problem:**
Multiple migrations have the same prefix `001_`:
```
backend/migrations/001_add_analytics_tables.sql
backend/migrations/001_add_calendar_tables.sql
backend/migrations/001_add_channel_name_to_sources.sql
backend/migrations/001_add_progress_fields.sql
backend/migrations/001_add_webhooks_table.sql
```

**Consequence:**
- Migrations run in alphabetical order, not semantic order
- No guarantee which runs first
- Dependency issues if migrations reference each other's tables

**Resolution Required:**
Rename migrations with proper sequence numbers:
- `001_add_progress_fields.sql`
- `002_add_webhooks_table.sql`
- `003_add_analytics_tables.sql`
- `004_add_calendar_tables.sql`
- `005_add_channel_name_to_sources.sql`
- `006_add_cdn_url_to_clips.sql`

---

## 🟡 HIGH PRIORITY ISSUES

### 4. MISSING FIELDS: tasks table progress tracking
**Severity:** HIGH
**Impact:** Progress tracking may fail

**Problem:**
The `init.sql` defines `tasks` table WITHOUT `progress` and `progress_message` fields:
```sql
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- NO progress fields here
)
```

But migration `001_add_progress_fields.sql` attempts to add them conditionally.

**Issue:**
If `init.sql` runs on a fresh database, progress fields won't exist until migration runs. This creates two-stage initialization.

**Resolution Required:**
Add progress fields directly to `init.sql`:
```sql
progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
progress_message TEXT,
```

---

### 5. MISSING INDEX: experiment_results unique constraint
**Severity:** HIGH
**Impact:** Duplicate experiment results possible

**Problem:**
The `init.sql` has a UNIQUE constraint in `experiment_results`:
```sql
UNIQUE(experiment_id, variation_id)
```

But the SQLAlchemy model in `models.py` does NOT define this constraint.

**Consequence:**
- ORM may attempt to insert duplicate records
- Database will reject with constraint violation
- Error handling may be inconsistent

**Resolution Required:**
Add to `/backend/src/models.py` in `ExperimentResult` class:
```python
__table_args__ = (
    # ... existing constraints ...
    UniqueConstraint('experiment_id', 'variation_id', name='uq_experiment_variation'),
)
```

---

### 6. MISSING INDEXES: Foreign key lookups
**Severity:** HIGH
**Impact:** Slow query performance

**Problem:**
Several foreign key columns lack indexes:

**Missing Indexes:**
```sql
-- calendar_credentials table
CREATE INDEX idx_calendar_credentials_user_id ON calendar_credentials(user_id);

-- scheduled_posts table (whichever version)
CREATE INDEX idx_scheduled_posts_user_id ON scheduled_posts(user_id);
CREATE INDEX idx_scheduled_posts_clip_id ON scheduled_posts(clip_id);

-- experiment_results table
CREATE INDEX idx_experiment_results_variation_id ON experiment_results(variation_id);
```

**Status:** Partially resolved in migration files, but NOT in `init.sql`.

**Consequence:**
Fresh database installations will have poor query performance until migrations run.

**Resolution Required:**
Add all indexes to `init.sql` for completeness.

---

### 7. INCONSISTENT DATA TYPES: VARCHAR vs TEXT
**Severity:** HIGH
**Impact:** Type mismatch errors

**Problem:**
The `webhooks.events` field has inconsistent definitions:

**init.sql:**
```sql
events TEXT[] NOT NULL DEFAULT '{}'
```

**models.py:**
```python
events: Mapped[List[str]] = mapped_column(ARRAY(Text), ...)
```

**migration (001_add_webhooks_table.sql):**
```sql
events TEXT[] NOT NULL DEFAULT '{}'
```

While TEXT[] works, better practice is VARCHAR(50)[] for event names.

**Resolution Required:**
Standardize on `VARCHAR(50)[]` for event types.

---

### 8. MISSING TRIGGERS: Social media tables
**Severity:** HIGH
**Impact:** Timestamps won't auto-update

**Problem:**
The social media migration creates tables but doesn't verify `update_updated_at_column()` function exists:

```sql
CREATE TRIGGER update_social_media_accounts_updated_at
    BEFORE UPDATE ON social_media_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

If this migration runs before `init.sql`, the function won't exist.

**Resolution Required:**
Add function check at start of migration:
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

---

## 📊 SCHEMA VALIDATION RESULTS

### Table Inventory

| Table Name | init.sql | models.py | Migrations | Prisma | Status |
|------------|----------|-----------|------------|--------|--------|
| users | ✅ | ✅ | ✅ (roles) | ✅ | ✅ Complete |
| tasks | ✅ | ✅ | ✅ (progress) | ✅ | ✅ Complete |
| sources | ✅ | ✅ | ✅ (channel) | ✅ | ✅ Complete |
| generated_clips | ✅ | ✅ | ✅ (cdn_url) | ❌ | ⚠️ Missing Prisma |
| webhooks | ✅ | ✅ | ✅ | ❌ | ⚠️ Missing Prisma |
| webhook_deliveries | ✅ | ✅ | ✅ | ❌ | ⚠️ Missing Prisma |
| session | ✅ | ❌ | ❌ | ✅ | ⚠️ Better Auth |
| account | ✅ | ❌ | ❌ | ✅ | ⚠️ Better Auth |
| verification | ✅ | ❌ | ❌ | ✅ | ⚠️ Better Auth |
| experiments | ✅ | ✅ | ❌ | ❌ | ⚠️ Missing Prisma |
| experiment_results | ✅ | ✅ | ❌ | ❌ | ⚠️ Missing Prisma |
| usage_tracking | ⚠️ (migration) | ✅ | ✅ | ✅ | ✅ Complete |
| clip_views | ⚠️ (migration) | ✅ | ✅ | ❌ | ⚠️ Missing Prisma |
| clip_performance | ⚠️ (migration) | ✅ | ✅ | ❌ | ⚠️ Missing Prisma |
| calendar_credentials | ⚠️ (migration) | ✅ | ✅ | ❌ | ⚠️ Missing Prisma |
| scheduled_posts | ⚠️ (CONFLICT) | ✅ (calendar) | ⚠️ (2 versions) | ❌ | 🔴 CONFLICT |
| social_media_accounts | ⚠️ (migration) | ❌ | ✅ | ❌ | 🔴 Missing Model |
| post_attempts | ⚠️ (migration) | ❌ | ✅ | ❌ | 🔴 Missing Model |

**Legend:**
- ✅ = Fully implemented and consistent
- ⚠️ = Partially implemented or inconsistency detected
- ❌ = Not implemented
- 🔴 = Critical issue

---

## 🔍 FOREIGN KEY ANALYSIS

### Verified Relationships

All foreign key relationships are correctly defined with appropriate CASCADE/SET NULL actions:

```sql
✅ tasks.user_id → users.id (ON DELETE CASCADE)
✅ tasks.source_id → sources.id (ON DELETE SET NULL)
✅ generated_clips.task_id → tasks.id (ON DELETE CASCADE)
✅ webhooks.user_id → users.id (ON DELETE CASCADE)
✅ webhook_deliveries.webhook_id → webhooks.id (ON DELETE CASCADE)
✅ experiments.user_id → users.id (ON DELETE CASCADE)
✅ experiment_results.experiment_id → experiments.id (ON DELETE CASCADE)
✅ experiment_results.clip_id → generated_clips.id (ON DELETE CASCADE)
✅ calendar_credentials.user_id → users.id (ON DELETE CASCADE)
✅ scheduled_posts.user_id → users.id (ON DELETE CASCADE)
✅ scheduled_posts.clip_id → generated_clips.id (ON DELETE CASCADE)
✅ clip_views.clip_id → generated_clips.id (ON DELETE CASCADE)
✅ clip_performance.clip_id → generated_clips.id (ON DELETE CASCADE)
✅ usage_tracking.user_id → users.id (ON DELETE CASCADE)
```

### Missing Relationships

The social media tables have proper foreign keys:
```sql
⚠️ social_media_accounts.user_id → users.id (ON DELETE CASCADE)
⚠️ post_attempts.scheduled_post_id → scheduled_posts.id (ON DELETE CASCADE)
⚠️ post_attempts.social_media_account_id → social_media_accounts.id (ON DELETE CASCADE)
```

But SQLAlchemy models don't exist to enforce them in the ORM.

---

## 📈 INDEX ANALYSIS

### Existing Indexes (from init.sql)

**✅ Well-indexed tables:**
- users: email, all timestamp columns
- tasks: user_id, source_id, status, created_at
- sources: created_at, channel_name
- generated_clips: task_id, clip_order, created_at
- webhooks: user_id, active, created_at
- webhook_deliveries: webhook_id, status, next_retry_at, created_at
- experiments: user_id, status, created_at
- experiment_results: experiment_id, clip_id, conversion_rate, engagement_rate
- session: token, userId
- account: userId
- verification: identifier

### Missing Indexes (Recommendations)

```sql
-- For calendar integration queries
CREATE INDEX idx_calendar_credentials_provider_active
    ON calendar_credentials(provider, is_active);

-- For scheduled post lookups
CREATE INDEX idx_scheduled_posts_scheduled_time_status
    ON scheduled_posts(scheduled_time, status);

-- For analytics dashboards
CREATE INDEX idx_clip_views_date_platform
    ON clip_views(date, platform);

CREATE INDEX idx_clip_performance_engagement_watch
    ON clip_performance(engagement_rate DESC, watch_time DESC);

-- For social media posting
CREATE INDEX idx_social_media_accounts_platform_active
    ON social_media_accounts(platform, is_active);

CREATE INDEX idx_post_attempts_status_next_retry
    ON post_attempts(status, next_retry_at)
    WHERE status = 'failed' AND next_retry_at IS NOT NULL;
```

---

## 🔄 TRIGGER VERIFICATION

### Verified Triggers

All `updated_at` triggers are correctly implemented:

```sql
✅ update_users_updatedAt (Better Auth convention)
✅ update_tasks_updated_at
✅ update_sources_updated_at
✅ update_generated_clips_updated_at
✅ update_webhooks_updated_at
✅ update_webhook_deliveries_updated_at
✅ update_session_updatedAt
✅ update_account_updatedAt
✅ update_verification_updatedAt
✅ update_experiments_updated_at
✅ update_experiment_results_updated_at
✅ update_calendar_credentials_updated_at
✅ update_scheduled_posts_updated_at (in calendar migration)
✅ update_clip_views_updated_at
✅ update_clip_performance_updated_at
✅ update_usage_tracking_updated_at
✅ update_social_media_accounts_updated_at
✅ update_scheduled_posts_updated_at (in social media migration - CONFLICT)
✅ update_post_attempts_updated_at
```

### Naming Convention Issues

**Problem:** Two functions with different purposes:
1. `update_updated_at_column()` - for snake_case tables
2. `update_updatedAt_column()` - for camelCase tables (Better Auth)

This is intentional and correct for the hybrid schema design.

---

## 🗂️ DATA TYPE CONSISTENCY

### UUID Storage
**Status:** ✅ CONSISTENT
All IDs use `VARCHAR(36)` with `uuid_generate_v4()::text` default.

### Timestamp Storage
**Status:** ✅ CONSISTENT
All timestamps use `TIMESTAMP WITH TIME ZONE`.

### Array Storage
**Status:** ⚠️ MIXED
- `tasks.generated_clips_ids`: `VARCHAR(36)[]` ✅
- `webhooks.events`: `TEXT[]` ⚠️ (should be VARCHAR)
- `scheduled_posts.platforms`: `VARCHAR(20)[]` ✅
- `scheduled_posts.hashtags`: `TEXT[]` ⚠️ (should be VARCHAR)

**Recommendation:** Use `VARCHAR(N)[]` instead of `TEXT[]` for bounded-length arrays.

---

## 🧪 MISSING CONSTRAINTS

### Check Constraints Audit

**✅ Well-constrained tables:**
- users: role, subscription_status
- sources: type (youtube, video_url)
- tasks: progress (0-100)
- webhooks: status (pending, success, failed)
- experiments: status, confidence_threshold
- experiment_results: all rates (0-1), counts (>= 0)
- clip_views: all counts (>= 0)
- clip_performance: rates (0-100), watch_time (>= 0)
- calendar_credentials: provider
- scheduled_posts: status, calendar_provider
- social_media_accounts: platform
- post_attempts: platform, status
- usage_tracking: month (1-12), year (>= 2020)

### Missing Constraints

**Recommendation:** Add check constraints for:

```sql
-- Ensure email format
ALTER TABLE users ADD CONSTRAINT check_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');

-- Ensure font_color is valid hex
ALTER TABLE users ADD CONSTRAINT check_font_color_hex
    CHECK (default_font_color ~* '^#[0-9A-Fa-f]{6}$');

ALTER TABLE tasks ADD CONSTRAINT check_font_color_hex
    CHECK (font_color ~* '^#[0-9A-Fa-f]{6}$');

-- Ensure duration is positive
ALTER TABLE generated_clips ADD CONSTRAINT check_duration_positive
    CHECK (duration > 0);

-- Ensure relevance_score is 0-1
ALTER TABLE generated_clips ADD CONSTRAINT check_relevance_score
    CHECK (relevance_score >= 0 AND relevance_score <= 1);
```

---

## 🔐 SECURITY CONSIDERATIONS

### Sensitive Data Fields

**⚠️ WARNING:** The following fields store sensitive data WITHOUT encryption:

1. `webhooks.secret` - HMAC secret (VARCHAR(255))
2. `calendar_credentials.access_token` - OAuth token (TEXT)
3. `calendar_credentials.refresh_token` - OAuth token (TEXT)
4. `calendar_credentials.caldav_password` - Password (TEXT)
5. `social_media_accounts.access_token` - OAuth token (TEXT)
6. `social_media_accounts.refresh_token` - OAuth token (TEXT)
7. `users.password_hash` - Password hash (safe if using bcrypt/argon2)

**Recommendation:**
Implement column-level encryption using:
- PostgreSQL `pgcrypto` extension
- Application-level encryption before insert
- Environment variable for encryption key (never commit to repo)

Example:
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Store encrypted
INSERT INTO calendar_credentials (access_token, ...)
VALUES (pgp_sym_encrypt('token', current_setting('app.encryption_key')), ...);

-- Retrieve decrypted
SELECT pgp_sym_decrypt(access_token::bytea, current_setting('app.encryption_key'))
FROM calendar_credentials;
```

---

## 📋 MIGRATION EXECUTION PLAN

### Recommended Migration Order

To safely apply all migrations to a production database:

```sql
-- 1. Base schema (if fresh install)
\i init.sql

-- 2. Backend migrations (in order)
\i migrations/001_add_user_roles_and_quotas.sql
\i backend/migrations/001_add_progress_fields.sql
\i backend/migrations/001_add_webhooks_table.sql
\i backend/migrations/001_add_channel_name_to_sources.sql
\i backend/migrations/001_add_analytics_tables.sql
\i backend/migrations/001_add_calendar_tables.sql
\i backend/migrations/add_cdn_url_to_clips.sql

-- 3. Social media (AFTER resolving scheduled_posts conflict)
-- \i migrations/002_social_media_integrations.sql  -- DO NOT RUN until conflict resolved
```

### Pre-Migration Checklist

Before running any migration:

- [ ] Backup database: `pg_dump supoclip > backup_$(date +%Y%m%d).sql`
- [ ] Test on staging environment first
- [ ] Verify no active user sessions
- [ ] Check disk space: `df -h`
- [ ] Review migration SQL for DDL locks
- [ ] Plan rollback strategy
- [ ] Monitor query locks: `SELECT * FROM pg_stat_activity;`

---

## 🎯 COMPLETE DATABASE SCHEMA DIAGRAM

```mermaid
erDiagram
    users ||--o{ tasks : "creates"
    users ||--o{ webhooks : "configures"
    users ||--o{ experiments : "runs"
    users ||--o{ calendar_credentials : "connects"
    users ||--o{ social_media_accounts : "connects"
    users ||--o{ usage_tracking : "tracks"
    users ||--o{ session : "has"
    users ||--o{ account : "has"

    sources ||--o{ tasks : "processes"

    tasks ||--o{ generated_clips : "produces"
    tasks }o--|| users : "belongs_to"
    tasks }o--o| sources : "uses"

    generated_clips }o--|| tasks : "belongs_to"
    generated_clips ||--o{ clip_views : "tracked_on"
    generated_clips ||--o| clip_performance : "has"
    generated_clips ||--o{ experiment_results : "tested_in"

    webhooks }o--|| users : "belongs_to"
    webhooks ||--o{ webhook_deliveries : "sends"

    experiments }o--|| users : "belongs_to"
    experiments ||--o{ experiment_results : "contains"

    experiment_results }o--|| experiments : "belongs_to"
    experiment_results }o--|| generated_clips : "tests"

    calendar_credentials }o--|| users : "belongs_to"
    calendar_credentials ||--o{ scheduled_posts_calendar : "schedules"

    scheduled_posts_calendar }o--|| calendar_credentials : "uses"
    scheduled_posts_calendar }o--|| users : "belongs_to"
    scheduled_posts_calendar }o--|| generated_clips : "posts"
    scheduled_posts_calendar }o--|| tasks : "for"

    social_media_accounts }o--|| users : "belongs_to"
    social_media_accounts ||--o{ post_attempts : "uses"

    scheduled_posts_social }o--|| users : "belongs_to"
    scheduled_posts_social }o--|| generated_clips : "posts"
    scheduled_posts_social ||--o{ post_attempts : "has"

    post_attempts }o--|| scheduled_posts_social : "belongs_to"
    post_attempts }o--|| social_media_accounts : "uses"

    clip_views }o--|| generated_clips : "tracks"
    clip_performance }o--|| generated_clips : "summarizes"

    usage_tracking }o--|| users : "tracks"

    users {
        varchar id PK
        varchar email UK
        varchar name
        boolean emailVerified
        varchar role
        varchar stripe_customer_id
        varchar stripe_subscription_id
        varchar subscription_status
        timestamp subscription_current_period_end
        varchar default_font_family
        int default_font_size
        varchar default_font_color
        timestamp createdAt
        timestamp updatedAt
    }

    tasks {
        varchar id PK
        varchar user_id FK
        varchar source_id FK
        varchar_array generated_clips_ids
        varchar status
        int progress
        text progress_message
        varchar font_family
        int font_size
        varchar font_color
        timestamp created_at
        timestamp updated_at
    }

    sources {
        varchar id PK
        varchar type
        varchar title
        varchar url
        varchar channel_name
        timestamp created_at
        timestamp updated_at
    }

    generated_clips {
        varchar id PK
        varchar task_id FK
        varchar filename
        varchar file_path
        varchar cdn_url
        varchar start_time
        varchar end_time
        float duration
        text text
        float relevance_score
        text reasoning
        int clip_order
        timestamp created_at
        timestamp updated_at
    }

    webhooks {
        varchar id PK
        varchar user_id FK
        varchar url
        text_array events
        varchar secret
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    webhook_deliveries {
        varchar id PK
        varchar webhook_id FK
        varchar event_type
        jsonb payload
        varchar status
        int response_code
        text response_body
        int attempts
        int max_attempts
        timestamp next_retry_at
        timestamp created_at
        timestamp updated_at
        timestamp delivered_at
    }

    experiments {
        varchar id PK
        varchar user_id FK
        varchar name
        text description
        jsonb variations
        varchar status
        varchar winner_variation_id
        float confidence_threshold
        timestamp started_at
        timestamp completed_at
        timestamp created_at
        timestamp updated_at
    }

    experiment_results {
        varchar id PK
        varchar experiment_id FK
        varchar variation_id
        varchar clip_id FK
        int views
        int clicks
        int conversions
        int shares
        int likes
        int comments
        float click_through_rate
        float conversion_rate
        float engagement_rate
        float avg_watch_time
        float watch_completion_rate
        timestamp created_at
        timestamp updated_at
    }

    calendar_credentials {
        varchar id PK
        varchar user_id FK
        varchar provider
        text access_token
        text refresh_token
        timestamp token_expiry
        varchar caldav_url
        varchar caldav_username
        text caldav_password
        varchar calendar_name
        jsonb metadata
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    scheduled_posts_calendar {
        varchar id PK
        varchar user_id FK
        varchar clip_id FK
        varchar task_id FK
        varchar calendar_credential_id FK
        varchar calendar_event_id
        varchar calendar_provider
        timestamp scheduled_time
        varchar title
        text description
        varchar status
        jsonb clip_metadata
        timestamp created_at
        timestamp updated_at
    }

    social_media_accounts {
        varchar id PK
        varchar user_id FK
        varchar platform
        varchar platform_user_id
        varchar platform_username
        text access_token
        text refresh_token
        timestamp token_expires_at
        jsonb metadata
        boolean is_active
        timestamp last_used_at
        timestamp created_at
        timestamp updated_at
    }

    scheduled_posts_social {
        varchar id PK
        varchar user_id FK
        varchar clip_id FK
        varchar_array platforms
        timestamp scheduled_for
        text caption
        text_array hashtags
        jsonb platform_config
        varchar status
        int max_retries
        int retry_delay_seconds
        timestamp created_at
        timestamp updated_at
        timestamp processed_at
    }

    post_attempts {
        varchar id PK
        varchar scheduled_post_id FK
        varchar platform
        varchar social_media_account_id FK
        int attempt_number
        varchar status
        varchar platform_post_id
        text platform_url
        jsonb response_data
        text error_message
        varchar error_code
        timestamp started_at
        timestamp completed_at
        timestamp next_retry_at
        timestamp created_at
        timestamp updated_at
    }

    clip_views {
        varchar id PK
        varchar clip_id FK
        varchar platform
        int views
        int likes
        int comments
        int shares
        date date
        timestamp created_at
        timestamp updated_at
    }

    clip_performance {
        varchar id PK
        varchar clip_id FK_UK
        float engagement_rate
        float watch_time
        float retention_rate
        timestamp created_at
        timestamp updated_at
    }

    usage_tracking {
        varchar id PK
        varchar user_id FK
        int month
        int year
        int clips_generated
        timestamp created_at
        timestamp updated_at
    }

    session {
        varchar id PK
        timestamp expiresAt
        varchar token UK
        timestamp createdAt
        timestamp updatedAt
        varchar ipAddress
        text userAgent
        varchar userId FK
    }

    account {
        varchar id PK
        varchar accountId
        varchar providerId
        varchar userId FK
        text accessToken
        text refreshToken
        text idToken
        timestamp accessTokenExpiresAt
        timestamp refreshTokenExpiresAt
        text scope
        text password
        timestamp createdAt
        timestamp updatedAt
    }
```

---

## 🛠️ ACTION ITEMS

### Immediate Actions (Before Production Deploy)

1. **RESOLVE scheduled_posts CONFLICT**
   - [ ] Decide on table naming strategy
   - [ ] Rename one or both tables
   - [ ] Update all references in code
   - [ ] Test both calendar and social features

2. **ADD MISSING SQLAlchemy MODELS**
   - [ ] Create `SocialMediaAccount` model
   - [ ] Create `PostAttempt` model
   - [ ] Add relationships to existing models
   - [ ] Test ORM queries

3. **FIX MIGRATION ORDERING**
   - [ ] Rename all migrations with proper sequence
   - [ ] Create migration execution script
   - [ ] Document dependencies
   - [ ] Test on fresh database

### Short-term Actions (Next Sprint)

4. **CONSOLIDATE init.sql**
   - [ ] Add progress fields to tasks table
   - [ ] Add all tables from migrations
   - [ ] Add all indexes
   - [ ] Single source of truth for schema

5. **ADD MISSING INDEXES**
   - [ ] Add composite indexes for common queries
   - [ ] Add partial indexes for status checks
   - [ ] Benchmark before/after performance

6. **IMPLEMENT ENCRYPTION**
   - [ ] Enable pgcrypto extension
   - [ ] Encrypt OAuth tokens
   - [ ] Encrypt API secrets
   - [ ] Document key management

7. **UPDATE PRISMA SCHEMA**
   - [ ] Add all missing tables
   - [ ] Sync with SQLAlchemy models
   - [ ] Generate TypeScript types
   - [ ] Test frontend integration

### Long-term Actions (Future Releases)

8. **ADD MONITORING**
   - [ ] Track table sizes: `pg_total_relation_size()`
   - [ ] Monitor slow queries: `pg_stat_statements`
   - [ ] Set up index usage stats
   - [ ] Alert on table bloat

9. **IMPLEMENT PARTITIONING**
   - [ ] Partition `clip_views` by date (monthly)
   - [ ] Partition `webhook_deliveries` by date
   - [ ] Partition `usage_tracking` by year
   - [ ] Improve query performance

10. **ADD MATERIALIZED VIEWS**
    - [ ] User dashboard stats (refresh daily)
    - [ ] Clip performance leaderboard
    - [ ] Platform analytics summary
    - [ ] Experiment A/B test results

---

## 📝 RECOMMENDATIONS

### Database Performance

1. **Connection Pooling** ✅ Already configured in `database.py`
   - pool_size=10, max_overflow=20
   - Good for current scale

2. **Enable Query Logging (Development)**
   ```python
   # In database.py, set:
   engine = create_async_engine(DATABASE_URL, echo=True)
   ```

3. **Add EXPLAIN ANALYZE to Slow Queries**
   ```sql
   EXPLAIN (ANALYZE, BUFFERS)
   SELECT * FROM generated_clips
   WHERE task_id = 'xxx';
   ```

### Schema Design

1. **Consider JSON Columns for Flexibility**
   - ✅ Already used in: `experiments.variations`, `calendar_credentials.metadata`
   - Good for platform-specific data

2. **Add Soft Deletes for Audit Trail**
   ```sql
   ALTER TABLE generated_clips ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
   CREATE INDEX idx_generated_clips_deleted_at ON generated_clips(deleted_at)
       WHERE deleted_at IS NULL;
   ```

3. **Implement Row-Level Security (RLS)**
   ```sql
   ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
   CREATE POLICY user_tasks ON tasks FOR ALL TO app_user
       USING (user_id = current_setting('app.user_id')::varchar);
   ```

### Testing

1. **Create Test Fixtures**
   ```python
   # tests/fixtures/database.py
   @pytest.fixture
   async def db_session():
       async with AsyncSessionLocal() as session:
           yield session
           await session.rollback()
   ```

2. **Add Migration Tests**
   ```bash
   # Test idempotency
   psql < init.sql
   psql < migrations/*.sql
   psql < migrations/*.sql  # Should not error
   ```

3. **Load Testing**
   ```bash
   # Simulate 1000 concurrent users
   pgbench -c 100 -j 10 -t 1000 supoclip
   ```

---

## 🎓 LESSONS LEARNED

### What Went Well

1. ✅ **Consistent Naming:** snake_case for backend, camelCase for Better Auth
2. ✅ **Good Indexing:** Most foreign keys and query patterns covered
3. ✅ **Check Constraints:** Excellent data validation at DB level
4. ✅ **Cascade Actions:** Proper cleanup on delete
5. ✅ **Timestamp Triggers:** Auto-updating updated_at fields

### Areas for Improvement

1. ⚠️ **Migration Strategy:** Need better versioning and ordering
2. ⚠️ **Model Sync:** SQLAlchemy, Prisma, and SQL drift apart
3. ⚠️ **Documentation:** Schema changes not always documented
4. ⚠️ **Testing:** No automated schema validation tests
5. ⚠️ **Security:** Sensitive data stored unencrypted

---

## 📚 REFERENCES

- PostgreSQL 15 Documentation: https://www.postgresql.org/docs/15/
- SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org/en/20/
- Prisma Schema: https://www.prisma.io/docs/concepts/components/prisma-schema
- Better Auth: https://better-auth.com/docs
- Database Indexing Strategies: https://use-the-index-luke.com/

---

## ✅ SIGN-OFF

**Audit Completed By:** AGENT 5
**Date:** 2025-11-10
**Status:** ⚠️ BLOCKED - Critical issues must be resolved before production deployment

**Next Steps:**
1. Address critical issues #1-#3 immediately
2. Schedule review meeting with team
3. Create tickets for all action items
4. Re-audit after fixes implemented

**Approvals Required:**
- [ ] Backend Lead - SQLAlchemy model fixes
- [ ] Database Admin - Migration strategy
- [ ] Security Team - Encryption implementation
- [ ] DevOps - Deployment plan review

---

*End of Report*

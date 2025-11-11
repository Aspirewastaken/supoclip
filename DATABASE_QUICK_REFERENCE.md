# Database Quick Reference Guide

## Quick Start

### Run Migrations
```bash
# Fresh install (destroys existing data)
DATABASE_URL="postgresql://user:pass@localhost:5432/supoclip" \
  ./scripts/run_migrations.sh --fresh

# Apply migrations to existing database
DATABASE_URL="postgresql://user:pass@localhost:5432/supoclip" \
  ./scripts/run_migrations.sh --skip-init --backup

# Test migrations
./scripts/test_migrations.sh
```

### Connect to Database
```bash
# PostgreSQL CLI
psql $DATABASE_URL

# List all tables
\dt

# Describe a table
\d+ users

# Show indexes
\di

# Show foreign keys
SELECT * FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY';
```

## Common Queries

### User Management
```sql
-- Get user with quota info
SELECT
    u.id, u.email, u.role,
    COALESCE(ut.clips_generated, 0) as clips_this_month,
    get_user_quota(u.role) as monthly_quota
FROM users u
LEFT JOIN usage_tracking ut ON u.id = ut.user_id
    AND ut.month = EXTRACT(MONTH FROM NOW())
    AND ut.year = EXTRACT(YEAR FROM NOW())
WHERE u.email = 'user@example.com';

-- Upgrade user to pro
UPDATE users
SET role = 'pro',
    subscription_status = 'active',
    stripe_customer_id = 'cus_xxx'
WHERE id = 'user-uuid';
```

### Task Management
```sql
-- Get user's recent tasks with clip count
SELECT
    t.id,
    t.status,
    t.progress,
    s.title as source_title,
    COUNT(gc.id) as clip_count,
    t.created_at
FROM tasks t
LEFT JOIN sources s ON t.source_id = s.id
LEFT JOIN generated_clips gc ON gc.task_id = t.id
WHERE t.user_id = 'user-uuid'
GROUP BY t.id, s.title
ORDER BY t.created_at DESC
LIMIT 10;

-- Find failed tasks
SELECT * FROM tasks WHERE status = 'failed' ORDER BY created_at DESC;
```

### Clip Analytics
```sql
-- Get clip with all metrics
SELECT
    gc.*,
    COALESCE(SUM(cv.views), 0) as total_views,
    COALESCE(SUM(cv.likes), 0) as total_likes,
    COALESCE(SUM(cv.shares), 0) as total_shares,
    cp.engagement_rate,
    cp.retention_rate
FROM generated_clips gc
LEFT JOIN clip_views cv ON gc.id = cv.clip_id
LEFT JOIN clip_performance cp ON gc.id = cp.clip_id
WHERE gc.id = 'clip-uuid'
GROUP BY gc.id, cp.engagement_rate, cp.retention_rate;

-- Top 10 clips by views
SELECT
    gc.filename,
    SUM(cv.views) as total_views,
    COUNT(DISTINCT cv.platform) as platform_count
FROM generated_clips gc
JOIN clip_views cv ON gc.id = cv.clip_id
GROUP BY gc.id, gc.filename
ORDER BY total_views DESC
LIMIT 10;
```

### Webhook Management
```sql
-- Get active webhooks for user
SELECT * FROM webhooks WHERE user_id = 'user-uuid' AND active = true;

-- Get recent deliveries for webhook
SELECT * FROM webhook_deliveries
WHERE webhook_id = 'webhook-uuid'
ORDER BY created_at DESC
LIMIT 20;

-- Retry failed deliveries
SELECT * FROM webhook_deliveries
WHERE status = 'failed'
    AND attempts < max_attempts
    AND next_retry_at <= NOW();
```

### A/B Testing
```sql
-- Get experiment with results
SELECT
    e.name,
    e.status,
    er.variation_id,
    er.views,
    er.conversions,
    er.conversion_rate,
    gc.filename
FROM experiments e
JOIN experiment_results er ON e.id = er.experiment_id
JOIN generated_clips gc ON er.clip_id = gc.id
WHERE e.id = 'experiment-uuid';

-- Find winning variation (highest conversion rate)
SELECT
    variation_id,
    conversion_rate,
    views
FROM experiment_results
WHERE experiment_id = 'experiment-uuid'
ORDER BY conversion_rate DESC
LIMIT 1;
```

### Usage Tracking
```sql
-- Check current month usage
SELECT
    u.email,
    u.role,
    ut.clips_generated,
    get_user_quota(u.role) as quota
FROM users u
LEFT JOIN usage_tracking ut ON u.id = ut.user_id
WHERE ut.month = EXTRACT(MONTH FROM NOW())
    AND ut.year = EXTRACT(YEAR FROM NOW());

-- Increment usage (use function for atomicity)
SELECT increment_usage('user-uuid',
    EXTRACT(MONTH FROM NOW())::int,
    EXTRACT(YEAR FROM NOW())::int,
    5  -- increment by 5 clips
);
```

### Calendar & Social Media
```sql
-- Get scheduled posts for today
SELECT
    sp.title,
    sp.scheduled_time,
    gc.filename,
    cc.provider
FROM scheduled_posts sp
JOIN generated_clips gc ON sp.clip_id = gc.id
JOIN calendar_credentials cc ON sp.calendar_credential_id = cc.id
WHERE sp.scheduled_time::date = CURRENT_DATE
    AND sp.status = 'scheduled';

-- Get social media accounts
SELECT
    sma.platform,
    sma.platform_username,
    sma.is_active,
    sma.last_used_at
FROM social_media_accounts sma
WHERE sma.user_id = 'user-uuid';
```

## Database Functions

### Quota Management
```sql
-- Get user's monthly quota
SELECT get_user_quota('pro');  -- Returns: 500

-- Check if user has quota available
SELECT * FROM check_user_quota(
    'user-uuid',
    11,    -- month
    2025   -- year
);

-- Returns:
-- has_quota | current_usage | quota_limit | remaining
-- true      | 45            | 500         | 455

-- Increment usage atomically
SELECT increment_usage('user-uuid', 11, 2025, 1);
```

## Maintenance

### Vacuum & Analyze
```sql
-- Vacuum and analyze all tables
VACUUM ANALYZE;

-- Specific table
VACUUM ANALYZE generated_clips;

-- Check table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Index Maintenance
```sql
-- Find unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey';

-- Rebuild bloated index
REINDEX INDEX CONCURRENTLY idx_generated_clips_task_id;

-- Analyze index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Backup & Restore
```bash
# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Create compressed backup
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from backup
psql $DATABASE_URL < backup_20251110.sql

# Restore compressed backup
gunzip < backup_20251110.sql.gz | psql $DATABASE_URL
```

### Table Statistics
```sql
-- Table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Row counts (approximate, fast)
SELECT
    schemaname,
    relname,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Row counts (exact, slow)
SELECT
    'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks
UNION ALL
SELECT 'generated_clips', COUNT(*) FROM generated_clips
UNION ALL
SELECT 'clip_views', COUNT(*) FROM clip_views;
```

## Performance Tuning

### Slow Query Analysis
```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT
    substring(query, 1, 100) AS short_query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### Connection Monitoring
```sql
-- Active connections
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    substring(query, 1, 50) as query
FROM pg_stat_activity
WHERE datname = 'supoclip';

-- Kill a connection
SELECT pg_terminate_backend(12345);  -- Replace with PID
```

### Lock Monitoring
```sql
-- Check for locks
SELECT
    pid,
    locktype,
    relation::regclass,
    mode,
    granted
FROM pg_locks
WHERE NOT granted;

-- Check for blocking queries
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

## Development Helpers

### Generate Test Data
```sql
-- Insert test user
INSERT INTO users (id, name, email, "emailVerified", "createdAt", "updatedAt")
VALUES (
    'test-user-' || gen_random_uuid()::text,
    'Test User',
    'test+' || floor(random() * 10000)::text || '@example.com',
    false,
    NOW(),
    NOW()
);

-- Insert test task
INSERT INTO tasks (id, user_id, status, created_at, updated_at)
SELECT
    'test-task-' || gen_random_uuid()::text,
    id,
    'completed',
    NOW() - (random() * INTERVAL '30 days'),
    NOW()
FROM users
WHERE email LIKE 'test%'
LIMIT 1;

-- Bulk insert test clips
INSERT INTO generated_clips (id, task_id, filename, file_path, start_time, end_time, duration, relevance_score, clip_order, created_at, updated_at)
SELECT
    gen_random_uuid()::text,
    t.id,
    'clip_' || i || '.mp4',
    '/tmp/clips/clip_' || i || '.mp4',
    '00:00',
    '00:30',
    30.0,
    random(),
    i,
    NOW(),
    NOW()
FROM tasks t
CROSS JOIN generate_series(1, 5) i
WHERE t.user_id IN (SELECT id FROM users WHERE email LIKE 'test%')
LIMIT 50;
```

### Clean Test Data
```sql
-- Delete all test users and cascade
DELETE FROM users WHERE email LIKE 'test%';

-- Delete old tasks
DELETE FROM tasks WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete old webhook deliveries
DELETE FROM webhook_deliveries WHERE created_at < NOW() - INTERVAL '30 days' AND status != 'pending';
```

## Troubleshooting

### Common Errors

**Error: `duplicate key value violates unique constraint`**
```sql
-- Find duplicate values
SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;

-- Fix: Delete duplicates keeping the oldest
DELETE FROM users a USING users b
WHERE a.id > b.id AND a.email = b.email;
```

**Error: `relation "scheduled_posts" already exists`**
```sql
-- Check if it's the calendar or social version
SELECT column_name FROM information_schema.columns WHERE table_name = 'scheduled_posts';

-- If it has 'calendar_event_id', it's the calendar version
-- If it has 'platforms', it's the social version (needs renaming)
-- Run: migrations/003_fix_scheduled_posts_conflict.sql
```

**Error: `function update_updated_at_column() does not exist`**
```sql
-- Create the function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

### Performance Issues

**Slow queries on clip_views**
```sql
-- Add missing index
CREATE INDEX CONCURRENTLY idx_clip_views_clip_date ON clip_views(clip_id, date DESC);

-- Partition by month
-- See DATABASE_SCHEMA_DIAGRAM.md for partitioning examples
```

**Slow user dashboard**
```sql
-- Add composite index
CREATE INDEX CONCURRENTLY idx_tasks_user_created ON tasks(user_id, created_at DESC);

-- Add covering index
CREATE INDEX CONCURRENTLY idx_tasks_user_status_created
    ON tasks(user_id, status, created_at DESC)
    INCLUDE (progress, progress_message);
```

## Security Checklist

- [ ] Enable SSL for database connections
- [ ] Rotate webhook secrets regularly
- [ ] Encrypt OAuth tokens in social_media_accounts
- [ ] Implement row-level security (RLS) for multi-tenant isolation
- [ ] Regular security audits with `pg_audit` extension
- [ ] Backup encryption with `pgcrypto`
- [ ] Limit database user permissions (no SUPERUSER for app)
- [ ] Enable connection pooling (PgBouncer)
- [ ] Set up monitoring (pg_stat_statements, pg_stat_monitor)
- [ ] Regular password rotation for database users

## Resources

- **Full Audit Report**: `DATABASE_SCHEMA_AUDIT_REPORT.md`
- **Schema Diagram**: `DATABASE_SCHEMA_DIAGRAM.md`
- **Migration Scripts**: `scripts/run_migrations.sh`, `scripts/test_migrations.sh`
- **Missing Models**: `backend/migrations/MISSING_MODELS.py`
- **PostgreSQL Docs**: https://www.postgresql.org/docs/15/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/en/20/

---

**Need Help?**
1. Check the audit report for detailed analysis
2. Review schema diagram for relationships
3. Test migrations on a separate database first
4. Ask in #database channel on Discord

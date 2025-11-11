-- Migration: Fix scheduled_posts table name conflict
-- Date: 2025-11-10
-- Description: Rename social media scheduled_posts to social_scheduled_posts to avoid conflict with calendar table
-- Priority: CRITICAL - Must run before 002_social_media_integrations.sql
--
-- CONFLICT EXPLANATION:
-- Two migrations created tables with the same name 'scheduled_posts':
--   1. backend/migrations/001_add_calendar_tables.sql (calendar integration)
--   2. migrations/002_social_media_integrations.sql (social media posting)
--
-- RESOLUTION:
-- This migration renames the social media table to 'social_scheduled_posts'
-- The calendar table remains 'scheduled_posts' (no prefix needed as it was created first)

-- Step 1: Check if old scheduled_posts table exists (from social media migration)
-- If it exists and has the social media schema, rename it

DO $$
BEGIN
    -- Check if scheduled_posts exists with platforms column (social media version)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'scheduled_posts' AND column_name = 'platforms'
    ) THEN
        -- This is the social media version, rename it
        RAISE NOTICE 'Found social media scheduled_posts table, renaming to social_scheduled_posts';

        -- Drop existing triggers
        DROP TRIGGER IF EXISTS update_scheduled_posts_updated_at ON scheduled_posts;

        -- Rename the table
        ALTER TABLE scheduled_posts RENAME TO social_scheduled_posts;

        -- Recreate trigger with new table name
        CREATE TRIGGER update_social_scheduled_posts_updated_at
            BEFORE UPDATE ON social_scheduled_posts
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        RAISE NOTICE 'Successfully renamed scheduled_posts to social_scheduled_posts';
    ELSE
        RAISE NOTICE 'Social media scheduled_posts table not found, skipping rename';
    END IF;
END $$;

-- Step 2: Create the social_scheduled_posts table if it doesn't exist
-- (in case migration is run on fresh database)

CREATE TABLE IF NOT EXISTS social_scheduled_posts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    clip_id VARCHAR(36) NOT NULL REFERENCES generated_clips(id) ON DELETE CASCADE,

    -- Publishing details
    platforms VARCHAR(20)[] NOT NULL, -- Array of platforms to post to
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Post content
    caption TEXT,
    hashtags TEXT[], -- Array of hashtags without # symbol

    -- Post configuration per platform
    platform_config JSONB DEFAULT '{}', -- Platform-specific settings (privacy, comments, duet, etc.)

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'processing', 'completed', 'failed', 'cancelled')),

    -- Retry configuration
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_delay_seconds INTEGER NOT NULL DEFAULT 300, -- 5 minutes

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Step 3: Create indexes for social_scheduled_posts
CREATE INDEX IF NOT EXISTS idx_social_scheduled_posts_user_id ON social_scheduled_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_scheduled_posts_clip_id ON social_scheduled_posts(clip_id);
CREATE INDEX IF NOT EXISTS idx_social_scheduled_posts_status ON social_scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_social_scheduled_posts_scheduled_for ON social_scheduled_posts(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_social_scheduled_posts_created_at ON social_scheduled_posts(created_at);

-- Step 4: Create trigger for social_scheduled_posts
DROP TRIGGER IF EXISTS update_social_scheduled_posts_updated_at ON social_scheduled_posts;
CREATE TRIGGER update_social_scheduled_posts_updated_at
    BEFORE UPDATE ON social_scheduled_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 5: Update post_attempts foreign key reference
-- First, check if post_attempts exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'post_attempts') THEN
        -- Drop old foreign key constraint if it exists
        ALTER TABLE post_attempts DROP CONSTRAINT IF EXISTS post_attempts_scheduled_post_id_fkey;

        -- Update foreign key to reference new table name
        -- Note: This will only work if scheduled_post_id column exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'post_attempts' AND column_name = 'scheduled_post_id'
        ) THEN
            ALTER TABLE post_attempts
                ADD CONSTRAINT post_attempts_scheduled_post_id_fkey
                FOREIGN KEY (scheduled_post_id)
                REFERENCES social_scheduled_posts(id)
                ON DELETE CASCADE;

            RAISE NOTICE 'Updated post_attempts foreign key to reference social_scheduled_posts';
        END IF;
    END IF;
END $$;

-- Step 6: Add comments for documentation
COMMENT ON TABLE social_scheduled_posts IS 'Scheduled posts for social media platforms (TikTok, Instagram, YouTube, Twitter)';
COMMENT ON COLUMN social_scheduled_posts.platforms IS 'Array of platforms to post to: tiktok, instagram, youtube, twitter';
COMMENT ON COLUMN social_scheduled_posts.platform_config IS 'Platform-specific settings as JSON (privacy, comments, duet settings, etc.)';
COMMENT ON COLUMN social_scheduled_posts.status IS 'Post status: scheduled, processing, completed, failed, cancelled';

-- Verification query
SELECT
    table_name,
    COUNT(*) as column_count
FROM information_schema.columns
WHERE table_name IN ('scheduled_posts', 'social_scheduled_posts')
GROUP BY table_name
ORDER BY table_name;

-- Expected output after migration:
-- table_name                | column_count
-- --------------------------|-------------
-- scheduled_posts           | 12-15 (calendar version with calendar_event_id)
-- social_scheduled_posts    | 13-15 (social media version with platforms[])

-- SUCCESS CRITERIA:
-- 1. social_scheduled_posts table exists
-- 2. scheduled_posts table exists with calendar_event_id column (calendar version)
-- 3. No duplicate table names
-- 4. All foreign keys valid
-- 5. All triggers working

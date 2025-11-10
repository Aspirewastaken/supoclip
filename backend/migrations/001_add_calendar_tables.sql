-- Migration: Add calendar integration tables
-- Date: 2025-11-10
-- Description: Add calendar_credentials and scheduled_posts tables for calendar integration

-- Calendar credentials table
CREATE TABLE IF NOT EXISTS calendar_credentials (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) CHECK (provider IN ('google', 'icloud', 'caldav')) NOT NULL,

    -- OAuth credentials (for Google Calendar)
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMP WITH TIME ZONE,

    -- CalDAV credentials (for iCloud and other CalDAV servers)
    caldav_url VARCHAR(500),
    caldav_username VARCHAR(255),
    caldav_password TEXT,  -- Should be encrypted in production
    calendar_name VARCHAR(255),

    -- Additional metadata
    metadata JSONB,

    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled posts table
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    clip_id VARCHAR(36) NOT NULL REFERENCES generated_clips(id) ON DELETE CASCADE,
    task_id VARCHAR(36) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    calendar_credential_id VARCHAR(36) NOT NULL REFERENCES calendar_credentials(id) ON DELETE CASCADE,

    -- Calendar event details
    calendar_event_id VARCHAR(500) NOT NULL,  -- Event ID from calendar provider
    calendar_provider VARCHAR(20) CHECK (calendar_provider IN ('google', 'icloud', 'caldav')) NOT NULL,

    -- Scheduling details
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Status tracking
    status VARCHAR(20) CHECK (status IN ('scheduled', 'published', 'failed', 'cancelled')) NOT NULL DEFAULT 'scheduled',

    -- Post metadata
    clip_metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_calendar_credentials_user_id ON calendar_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_credentials_provider ON calendar_credentials(provider);
CREATE INDEX IF NOT EXISTS idx_calendar_credentials_is_active ON calendar_credentials(is_active);

CREATE INDEX IF NOT EXISTS idx_scheduled_posts_user_id ON scheduled_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_clip_id ON scheduled_posts(clip_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_task_id ON scheduled_posts(task_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_calendar_credential_id ON scheduled_posts(calendar_credential_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_scheduled_time ON scheduled_posts(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_calendar_provider ON scheduled_posts(calendar_provider);

-- Create triggers for updated_at columns
CREATE TRIGGER update_calendar_credentials_updated_at
    BEFORE UPDATE ON calendar_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_posts_updated_at
    BEFORE UPDATE ON scheduled_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE calendar_credentials IS 'Stores calendar provider credentials for users (Google, iCloud, CalDAV)';
COMMENT ON TABLE scheduled_posts IS 'Stores scheduled posts linked to calendar events';

COMMENT ON COLUMN calendar_credentials.provider IS 'Calendar provider type: google, icloud, or caldav';
COMMENT ON COLUMN calendar_credentials.caldav_password IS 'CalDAV password - should be encrypted in production';
COMMENT ON COLUMN scheduled_posts.status IS 'Post status: scheduled, published, failed, or cancelled';

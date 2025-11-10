-- Social Media Integrations Migration
-- Adds tables for social media account connections, scheduled posts, and post tracking

-- Social media accounts table - stores OAuth tokens and platform connections
CREATE TABLE social_media_accounts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('tiktok', 'instagram', 'youtube', 'twitter')),
    platform_user_id VARCHAR(255) NOT NULL, -- User ID on the platform
    platform_username VARCHAR(255), -- Username/handle on the platform

    -- OAuth credentials (encrypted in production)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Platform-specific metadata
    metadata JSONB DEFAULT '{}', -- Store platform-specific data (scopes, permissions, etc.)

    -- Account status
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one account per platform per user
    UNIQUE(user_id, platform, platform_user_id)
);

-- Scheduled posts table - stores posts to be published
CREATE TABLE scheduled_posts (
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

-- Post attempts table - tracks individual posting attempts to platforms
CREATE TABLE post_attempts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    scheduled_post_id VARCHAR(36) NOT NULL REFERENCES scheduled_posts(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('tiktok', 'instagram', 'youtube', 'twitter')),
    social_media_account_id VARCHAR(36) NOT NULL REFERENCES social_media_accounts(id) ON DELETE CASCADE,

    -- Attempt details
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'success', 'failed')),

    -- Response from platform
    platform_post_id VARCHAR(255), -- ID of the post on the platform (if successful)
    platform_url TEXT, -- Direct URL to the post
    response_data JSONB, -- Full response from platform API

    -- Error tracking
    error_message TEXT,
    error_code VARCHAR(100),

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_social_media_accounts_user_id ON social_media_accounts(user_id);
CREATE INDEX idx_social_media_accounts_platform ON social_media_accounts(platform);
CREATE INDEX idx_social_media_accounts_is_active ON social_media_accounts(is_active);
CREATE INDEX idx_social_media_accounts_created_at ON social_media_accounts(created_at);

CREATE INDEX idx_scheduled_posts_user_id ON scheduled_posts(user_id);
CREATE INDEX idx_scheduled_posts_clip_id ON scheduled_posts(clip_id);
CREATE INDEX idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX idx_scheduled_posts_scheduled_for ON scheduled_posts(scheduled_for);
CREATE INDEX idx_scheduled_posts_created_at ON scheduled_posts(created_at);

CREATE INDEX idx_post_attempts_scheduled_post_id ON post_attempts(scheduled_post_id);
CREATE INDEX idx_post_attempts_platform ON post_attempts(platform);
CREATE INDEX idx_post_attempts_status ON post_attempts(status);
CREATE INDEX idx_post_attempts_next_retry_at ON post_attempts(next_retry_at);
CREATE INDEX idx_post_attempts_created_at ON post_attempts(created_at);

-- Create triggers for updated_at
CREATE TRIGGER update_social_media_accounts_updated_at
    BEFORE UPDATE ON social_media_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_posts_updated_at
    BEFORE UPDATE ON scheduled_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_post_attempts_updated_at
    BEFORE UPDATE ON post_attempts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

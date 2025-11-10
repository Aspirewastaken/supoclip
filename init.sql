-- Database initialization script for SupoClip
-- Create database schema with required tables

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (compatible with Prisma schema)
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    "emailVerified" BOOLEAN NOT NULL DEFAULT false,
    image VARCHAR(500),
    "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash VARCHAR(255),
    -- Default font preferences
    default_font_family VARCHAR(100) DEFAULT 'TikTokSans-Regular',
    default_font_size INTEGER DEFAULT 24,
    default_font_color VARCHAR(7) DEFAULT '#FFFFFF'
);

-- Source table (created before tasks since tasks reference sources)
CREATE TABLE sources (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    type VARCHAR(20) CHECK (type IN ('youtube', 'video_url')) NOT NULL,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000),  -- Source URL
    channel_name VARCHAR(255),  -- Channel/uploader name for folder organization
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_id VARCHAR(36) REFERENCES sources(id) ON DELETE SET NULL,
    generated_clips_ids VARCHAR(36)[], -- Array of clip IDs
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Progress tracking fields
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    progress_message TEXT,

    -- Font customization fields
    font_family VARCHAR(100) DEFAULT 'TikTokSans-Regular',
    font_size INTEGER DEFAULT 24,
    font_color VARCHAR(7) DEFAULT '#FFFFFF', -- Hex color code

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Generated clips table
CREATE TABLE generated_clips (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    task_id VARCHAR(36) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    start_time VARCHAR(20) NOT NULL, -- MM:SS format
    end_time VARCHAR(20) NOT NULL,   -- MM:SS format
    duration FLOAT NOT NULL,         -- Duration in seconds
    text TEXT,                       -- Transcript text for this clip
    relevance_score FLOAT NOT NULL,
    reasoning TEXT,                  -- AI reasoning for selection
    clip_order INTEGER NOT NULL,     -- Order within the task
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Webhooks table for storing webhook configurations
CREATE TABLE webhooks (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(1000) NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}', -- Array of event types: task.completed, task.failed, clips.ready
    secret VARCHAR(255) NOT NULL, -- HMAC secret for signature validation
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Webhook delivery logs table for tracking webhook delivery attempts
CREATE TABLE webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    webhook_id VARCHAR(36) NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
    response_code INTEGER,
    response_body TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- Better Auth tables
CREATE TABLE session (
    id VARCHAR(36) PRIMARY KEY,
    "expiresAt" TIMESTAMP WITH TIME ZONE NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL,
    "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL,
    "ipAddress" VARCHAR(255),
    "userAgent" TEXT,
    "userId" VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE account (
    id VARCHAR(36) PRIMARY KEY,
    "accountId" VARCHAR(255) NOT NULL,
    "providerId" VARCHAR(255) NOT NULL,
    "userId" VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    "accessToken" TEXT,
    "refreshToken" TEXT,
    "idToken" TEXT,
    "accessTokenExpiresAt" TIMESTAMP WITH TIME ZONE,
    "refreshTokenExpiresAt" TIMESTAMP WITH TIME ZONE,
    scope TEXT,
    password TEXT,
    "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL,
    "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE verification (
    id VARCHAR(36) PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    "expiresAt" TIMESTAMP WITH TIME ZONE NOT NULL,
    "createdAt" TIMESTAMP WITH TIME ZONE,
    "updatedAt" TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_source_id ON tasks(source_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_sources_created_at ON sources(created_at);
CREATE INDEX idx_sources_channel_name ON sources(channel_name);
CREATE INDEX idx_generated_clips_task_id ON generated_clips(task_id);
CREATE INDEX idx_generated_clips_clip_order ON generated_clips(clip_order);
CREATE INDEX idx_generated_clips_created_at ON generated_clips(created_at);
CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_active ON webhooks(active);
CREATE INDEX idx_webhooks_created_at ON webhooks(created_at);
CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_next_retry_at ON webhook_deliveries(next_retry_at);
CREATE INDEX idx_webhook_deliveries_created_at ON webhook_deliveries(created_at);
CREATE INDEX idx_session_token ON session(token);
CREATE INDEX idx_session_userId ON session("userId");
CREATE INDEX idx_account_userId ON account("userId");
CREATE INDEX idx_verification_identifier ON verification(identifier);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create function for updatedAt column (Prisma format)
CREATE OR REPLACE FUNCTION update_updatedAt_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW."updatedAt" = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at and updatedAt
-- Users table only has "updatedAt" (Better Auth convention)
CREATE TRIGGER update_users_updatedAt BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updatedAt_column();

-- Tasks, sources, and generated_clips use snake_case updated_at
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_generated_clips_updated_at BEFORE UPDATE ON generated_clips FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_webhook_deliveries_updated_at BEFORE UPDATE ON webhook_deliveries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Better Auth tables use camelCase "updatedAt"
CREATE TRIGGER update_session_updatedAt BEFORE UPDATE ON session FOR EACH ROW EXECUTE FUNCTION update_updatedAt_column();
CREATE TRIGGER update_account_updatedAt BEFORE UPDATE ON account FOR EACH ROW EXECUTE FUNCTION update_updatedAt_column();
CREATE TRIGGER update_verification_updatedAt BEFORE UPDATE ON verification FOR EACH ROW EXECUTE FUNCTION update_updatedAt_column();

-- Experiments table for A/B testing clip variations
CREATE TABLE experiments (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    variations JSONB NOT NULL DEFAULT '[]', -- Array of variation objects with clip_id, variation_name
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'paused', 'completed')),
    winner_variation_id VARCHAR(36),
    confidence_threshold FLOAT DEFAULT 0.95 CHECK (confidence_threshold >= 0 AND confidence_threshold <= 1),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Experiment results table for tracking metrics per variation
CREATE TABLE experiment_results (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    experiment_id VARCHAR(36) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    variation_id VARCHAR(36) NOT NULL, -- References the clip ID in the variation
    clip_id VARCHAR(36) NOT NULL REFERENCES generated_clips(id) ON DELETE CASCADE,

    -- Engagement metrics
    views INTEGER DEFAULT 0 CHECK (views >= 0),
    clicks INTEGER DEFAULT 0 CHECK (clicks >= 0),
    conversions INTEGER DEFAULT 0 CHECK (conversions >= 0),
    shares INTEGER DEFAULT 0 CHECK (shares >= 0),
    likes INTEGER DEFAULT 0 CHECK (likes >= 0),
    comments INTEGER DEFAULT 0 CHECK (comments >= 0),

    -- Calculated rates
    click_through_rate FLOAT DEFAULT 0.0 CHECK (click_through_rate >= 0 AND click_through_rate <= 1),
    conversion_rate FLOAT DEFAULT 0.0 CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    engagement_rate FLOAT DEFAULT 0.0 CHECK (engagement_rate >= 0 AND engagement_rate <= 1),

    -- Watch metrics
    avg_watch_time FLOAT DEFAULT 0.0 CHECK (avg_watch_time >= 0),
    watch_completion_rate FLOAT DEFAULT 0.0 CHECK (watch_completion_rate >= 0 AND watch_completion_rate <= 1),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(experiment_id, variation_id)
);

-- Create indexes for experiments
CREATE INDEX idx_experiments_user_id ON experiments(user_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created_at ON experiments(created_at);
CREATE INDEX idx_experiment_results_experiment_id ON experiment_results(experiment_id);
CREATE INDEX idx_experiment_results_clip_id ON experiment_results(clip_id);
CREATE INDEX idx_experiment_results_conversion_rate ON experiment_results(conversion_rate);
CREATE INDEX idx_experiment_results_engagement_rate ON experiment_results(engagement_rate);

-- Create triggers for updated_at
CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_experiment_results_updated_at BEFORE UPDATE ON experiment_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

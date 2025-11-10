-- Migration: Add analytics tables for clip performance tracking
-- Created: 2025-11-10
-- Description: Adds clip_views and clip_performance tables for tracking clip analytics

-- Drop tables if they exist (for clean re-runs)
DROP TABLE IF EXISTS clip_performance CASCADE;
DROP TABLE IF EXISTS clip_views CASCADE;

-- Clip views table - tracks view metrics across platforms
CREATE TABLE clip_views (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    clip_id VARCHAR(36) NOT NULL REFERENCES generated_clips(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- e.g., 'tiktok', 'youtube_shorts', 'instagram_reels', 'facebook', 'twitter', 'linkedin'
    views INTEGER DEFAULT 0 CHECK (views >= 0),
    likes INTEGER DEFAULT 0 CHECK (likes >= 0),
    comments INTEGER DEFAULT 0 CHECK (comments >= 0),
    shares INTEGER DEFAULT 0 CHECK (shares >= 0),
    date DATE NOT NULL DEFAULT CURRENT_DATE, -- Date when metrics were recorded
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Clip performance table - tracks engagement and watch metrics
CREATE TABLE clip_performance (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    clip_id VARCHAR(36) NOT NULL REFERENCES generated_clips(id) ON DELETE CASCADE,
    engagement_rate FLOAT DEFAULT 0.0 CHECK (engagement_rate >= 0 AND engagement_rate <= 100), -- Percentage (0-100)
    watch_time FLOAT DEFAULT 0.0 CHECK (watch_time >= 0), -- Average watch time in seconds
    retention_rate FLOAT DEFAULT 0.0 CHECK (retention_rate >= 0 AND retention_rate <= 100), -- Percentage (0-100)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(clip_id) -- Each clip has one performance record
);

-- Create indexes for better query performance
CREATE INDEX idx_clip_views_clip_id ON clip_views(clip_id);
CREATE INDEX idx_clip_views_platform ON clip_views(platform);
CREATE INDEX idx_clip_views_date ON clip_views(date);
CREATE INDEX idx_clip_views_created_at ON clip_views(created_at);
CREATE INDEX idx_clip_performance_clip_id ON clip_performance(clip_id);
CREATE INDEX idx_clip_performance_engagement_rate ON clip_performance(engagement_rate);
CREATE INDEX idx_clip_performance_retention_rate ON clip_performance(retention_rate);

-- Add triggers for updated_at columns
CREATE TRIGGER update_clip_views_updated_at
    BEFORE UPDATE ON clip_views
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clip_performance_updated_at
    BEFORE UPDATE ON clip_performance
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE clip_views IS 'Tracks view metrics for clips across different social media platforms';
COMMENT ON TABLE clip_performance IS 'Tracks engagement and watch metrics for clips';
COMMENT ON COLUMN clip_views.platform IS 'Social media platform where the clip was posted (tiktok, youtube_shorts, instagram_reels, etc.)';
COMMENT ON COLUMN clip_views.date IS 'Date when these metrics were recorded (allows tracking metrics over time)';
COMMENT ON COLUMN clip_performance.engagement_rate IS 'Overall engagement rate as percentage (likes + comments + shares) / views * 100';
COMMENT ON COLUMN clip_performance.watch_time IS 'Average watch time in seconds';
COMMENT ON COLUMN clip_performance.retention_rate IS 'Percentage of viewers who watched the entire clip';

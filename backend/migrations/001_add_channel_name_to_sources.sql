-- Migration: Add channel_name and url to sources table
-- Description: Adds channel/uploader tracking for better folder organization
-- Date: 2025-11-10

-- Add url column to store source URL
ALTER TABLE sources ADD COLUMN IF NOT EXISTS url VARCHAR(1000);

-- Add channel_name column to store channel/uploader name
ALTER TABLE sources ADD COLUMN IF NOT EXISTS channel_name VARCHAR(255);

-- Create index for faster channel lookups
CREATE INDEX IF NOT EXISTS idx_sources_channel_name ON sources(channel_name);

-- Add comment to table
COMMENT ON COLUMN sources.url IS 'Source URL (YouTube, video_url, etc.)';
COMMENT ON COLUMN sources.channel_name IS 'Channel or uploader name for folder organization';

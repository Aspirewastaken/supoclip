-- Migration: Add CDN URL support to generated_clips table
-- Version: 1.0.0
-- Date: 2025-11-10
-- Description: Adds cdn_url column to store CDN delivery URLs for clips

-- Add cdn_url column to generated_clips table
ALTER TABLE generated_clips
ADD COLUMN IF NOT EXISTS cdn_url VARCHAR(1000);

-- Add comment to document the column
COMMENT ON COLUMN generated_clips.cdn_url IS 'CDN URL for the clip if uploaded to CDN (CloudFront, R2, Bunny, etc.)';

-- Create index for faster lookups by CDN URL (optional, useful for debugging)
CREATE INDEX IF NOT EXISTS idx_generated_clips_cdn_url ON generated_clips(cdn_url);

-- Update any existing clips to have NULL cdn_url (no action needed, already default)
-- This ensures backward compatibility

-- Verify the migration
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'generated_clips'
    AND column_name = 'cdn_url';

-- Expected output:
-- column_name | data_type | character_maximum_length | is_nullable
-- cdn_url     | varchar   | 1000                     | YES

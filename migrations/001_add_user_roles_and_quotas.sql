-- Migration: Add user roles and quota tracking
-- Date: 2025-11-10

-- Add role and billing fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'free' CHECK (role IN ('free', 'pro', 'admin'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20) DEFAULT 'inactive' CHECK (subscription_status IN ('active', 'inactive', 'canceled', 'past_due'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMP WITH TIME ZONE;

-- Create usage tracking table for monthly quotas
CREATE TABLE IF NOT EXISTS usage_tracking (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    year INTEGER NOT NULL CHECK (year >= 2020),
    clips_generated INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one record per user per month/year
    CONSTRAINT unique_user_month_year UNIQUE (user_id, month, year)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_month_year ON usage_tracking(month, year);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_created_at ON usage_tracking(created_at);

-- Add trigger for usage_tracking updated_at
CREATE TRIGGER update_usage_tracking_updated_at
    BEFORE UPDATE ON usage_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to get user's monthly quota based on role
CREATE OR REPLACE FUNCTION get_user_quota(user_role VARCHAR)
RETURNS INTEGER AS $$
BEGIN
    CASE user_role
        WHEN 'free' THEN RETURN 10;
        WHEN 'pro' THEN RETURN 500;
        WHEN 'admin' THEN RETURN -1;  -- -1 means unlimited
        ELSE RETURN 0;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to check if user has quota available
CREATE OR REPLACE FUNCTION check_user_quota(p_user_id VARCHAR, p_month INTEGER, p_year INTEGER)
RETURNS TABLE(
    has_quota BOOLEAN,
    current_usage INTEGER,
    quota_limit INTEGER,
    remaining INTEGER
) AS $$
DECLARE
    v_role VARCHAR;
    v_usage INTEGER;
    v_quota INTEGER;
BEGIN
    -- Get user role
    SELECT role INTO v_role FROM users WHERE id = p_user_id;

    -- Get quota for role
    v_quota := get_user_quota(v_role);

    -- Get current usage
    SELECT COALESCE(clips_generated, 0) INTO v_usage
    FROM usage_tracking
    WHERE user_id = p_user_id AND month = p_month AND year = p_year;

    -- If no record exists, usage is 0
    IF v_usage IS NULL THEN
        v_usage := 0;
    END IF;

    -- Check if user has quota (admin has unlimited)
    RETURN QUERY SELECT
        (v_quota = -1 OR v_usage < v_quota) as has_quota,
        v_usage as current_usage,
        v_quota as quota_limit,
        CASE
            WHEN v_quota = -1 THEN -1  -- Unlimited
            ELSE GREATEST(0, v_quota - v_usage)
        END as remaining;
END;
$$ LANGUAGE plpgsql;

-- Function to increment usage
CREATE OR REPLACE FUNCTION increment_usage(p_user_id VARCHAR, p_month INTEGER, p_year INTEGER, p_increment INTEGER DEFAULT 1)
RETURNS INTEGER AS $$
DECLARE
    v_new_usage INTEGER;
BEGIN
    -- Insert or update usage record
    INSERT INTO usage_tracking (user_id, month, year, clips_generated)
    VALUES (p_user_id, p_month, p_year, p_increment)
    ON CONFLICT (user_id, month, year)
    DO UPDATE SET
        clips_generated = usage_tracking.clips_generated + p_increment,
        updated_at = CURRENT_TIMESTAMP
    RETURNING clips_generated INTO v_new_usage;

    RETURN v_new_usage;
END;
$$ LANGUAGE plpgsql;

-- Seed admin user if needed (optional - uncomment if you want a default admin)
-- UPDATE users SET role = 'admin' WHERE email = 'admin@supoclip.com';

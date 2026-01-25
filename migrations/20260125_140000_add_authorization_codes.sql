-- Migration: Add Authorization Codes
-- Created: 2026-01-25 14:00:00
-- Description: Adds tables for authorization code system to control user registration

-- UP

-- Create auth_codes table
CREATE TABLE IF NOT EXISTS auth_codes (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    created_by INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Create indexes for auth_codes
CREATE INDEX IF NOT EXISTS idx_auth_codes_code ON auth_codes(code);
CREATE INDEX IF NOT EXISTS idx_auth_codes_is_active ON auth_codes(is_active);
CREATE INDEX IF NOT EXISTS idx_auth_codes_expires_at ON auth_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_codes_created_by ON auth_codes(created_by);

-- Create code_usage table (tracks which user used which code)
CREATE TABLE IF NOT EXISTS code_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    used_at INTEGER NOT NULL,
    FOREIGN KEY (code_id) REFERENCES auth_codes(code_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for code_usage
CREATE INDEX IF NOT EXISTS idx_code_usage_code_id ON code_usage(code_id);
CREATE INDEX IF NOT EXISTS idx_code_usage_user_id ON code_usage(user_id);

-- DOWN (Rollback instructions)
-- To roll back this migration, run:
-- DROP INDEX IF EXISTS idx_code_usage_user_id;
-- DROP INDEX IF EXISTS idx_code_usage_code_id;
-- DROP TABLE IF EXISTS code_usage;
-- DROP INDEX IF EXISTS idx_auth_codes_created_by;
-- DROP INDEX IF EXISTS idx_auth_codes_expires_at;
-- DROP INDEX IF EXISTS idx_auth_codes_is_active;
-- DROP INDEX IF EXISTS idx_auth_codes_code;
-- DROP TABLE IF EXISTS auth_codes;

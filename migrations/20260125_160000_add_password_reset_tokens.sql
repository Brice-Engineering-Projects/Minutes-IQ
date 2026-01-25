-- Migration: Add password reset tokens table
-- Created: 2026-01-25
-- Purpose: Enable self-service password reset functionality
--
-- This table stores password reset tokens for users who have forgotten
-- their passwords. Tokens are:
--   - Single-use (invalidated after use)
--   - Time-limited (expire after 30 minutes)
--   - Cryptographically secure
--   - Hashed before storage (not stored in plain text)

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,  -- SHA-256 hash of the actual token
    created_at INTEGER NOT NULL,      -- Unix timestamp when token was created
    expires_at INTEGER NOT NULL,      -- Unix timestamp when token expires
    used_at INTEGER,                  -- Unix timestamp when token was used (NULL if not used)
    is_valid INTEGER NOT NULL DEFAULT 1,  -- 1 = valid, 0 = invalidated

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Index for efficient lookups by token hash
CREATE INDEX IF NOT EXISTS idx_password_reset_token_hash ON password_reset_tokens(token_hash);

-- Index for efficient lookups by user
CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id);

-- Index for efficient cleanup of expired tokens
CREATE INDEX IF NOT EXISTS idx_password_reset_expires_at ON password_reset_tokens(expires_at);

-- ============================================================================
-- ROLLBACK MIGRATION
-- ============================================================================

-- To rollback this migration, run:
-- DROP TABLE IF EXISTS password_reset_tokens;

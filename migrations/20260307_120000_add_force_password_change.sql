-- Migration: Add force_password_change flag to users
-- Created: 2026-03-07
-- Purpose: Support admin fallback password reset requiring mandatory password change

-- UP
ALTER TABLE users
ADD COLUMN force_password_change INTEGER NOT NULL DEFAULT 0;

-- DOWN (SQLite/libSQL note: dropping a column requires table rebuild)
-- No automatic rollback provided.
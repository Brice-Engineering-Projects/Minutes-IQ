-- =====================================================
-- 002_add_indexes.sql
-- Additional indexes for Minutes IQ (v1)
-- SQLite / Turso Compatible
-- =====================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Deferred performance indexes
-- (Added intentionally, not automatically)
-- -----------------------------------------------------

-- Speed up user-scoped saved search lookups
CREATE INDEX IF NOT EXISTS idx_saved_searches_user_id
    ON saved_searches(user_id);

-- Speed up client-scoped saved search lookups
CREATE INDEX IF NOT EXISTS idx_saved_searches_client_id
    ON saved_searches(client_id);

-- Speed up active source filtering per client
CREATE INDEX IF NOT EXISTS idx_client_sources_client_active
    ON client_sources(client_id, is_active);

-- Speed up auth credential lookups by user
CREATE INDEX IF NOT EXISTS idx_auth_credentials_user_id
    ON auth_credentials(user_id);

-- =====================================================
-- End of 002_add_indexes.sql
-- =====================================================

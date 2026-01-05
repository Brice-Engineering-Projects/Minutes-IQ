-- =====================================================
-- 003_seed_auth_providers.sql
-- Seed authentication providers for JEA Web Scraper (v1)
-- SQLite / Turso Compatible
-- =====================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Seed auth provider types
-- -----------------------------------------------------
-- NOTE:
-- This assumes auth_provider is currently user-scoped.
-- Providers should be inserted after at least one
-- system/admin user exists.
-- -----------------------------------------------------

-- Example seed (replace user_id with real admin user)
-- INSERT INTO auth_provider (user_id, provider_type)
-- VALUES (1, 'local');

-- =====================================================
-- End of 003_seed_auth_providers.sql
-- =====================================================

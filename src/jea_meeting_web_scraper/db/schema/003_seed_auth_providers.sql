-- =====================================================
-- 003_seed_auth_providers.sql
-- Seed authentication providers for JEA Web Scraper (v1)
-- SQLite / Turso Compatible
-- =====================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Attach LOCAL auth provider to admin user
-- -----------------------------------------------------
-- Assumptions:
-- 1. users table already exists
-- 2. admin user has already been seeded
-- 3. auth_provider is user-scoped
--
-- This script is idempotent and safe to re-run.
-- -----------------------------------------------------

INSERT INTO auth_providers (user_id, provider_type)
SELECT u.user_id, 'local'
FROM users u
WHERE u.username = 'admin'
  AND NOT EXISTS (
    SELECT 1
    FROM auth_provider ap
    WHERE ap.user_id = u.user_id
      AND ap.provider_type = 'local'
  );

-- =====================================================
-- End of 003_seed_auth_providers.sql
-- =====================================================

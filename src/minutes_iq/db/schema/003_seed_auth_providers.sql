-- =====================================================
-- 003_seed_auth_providers.sql
-- Seed baseline reference data required by the app
-- =====================================================

PRAGMA foreign_keys = ON;

-- Required role IDs used by repositories/services.
INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (1, 'admin');
INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (2, 'user');

-- Provider ID 1 is expected to be password auth.
INSERT OR IGNORE INTO auth_providers (provider_id, provider_name)
VALUES (1, 'password');

-- Migration: Initial Schema
-- Created: 2026-01-25 12:00:00
-- Description: Creates the initial database schema for authentication and user management

-- UP

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

-- Seed roles
INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (1, 'admin');
INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (2, 'user');

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- Create auth_providers table
CREATE TABLE IF NOT EXISTS auth_providers (
    provider_id INTEGER PRIMARY KEY,
    provider_name TEXT NOT NULL UNIQUE
);

-- Seed auth providers
INSERT OR IGNORE INTO auth_providers (provider_id, provider_name) VALUES (1, 'password');

-- Create auth_credentials table
CREATE TABLE IF NOT EXISTS auth_credentials (
    credential_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (provider_id) REFERENCES auth_providers(provider_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_auth_credentials_user_id ON auth_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_credentials_provider_id ON auth_credentials(provider_id);
CREATE INDEX IF NOT EXISTS idx_auth_credentials_is_active ON auth_credentials(is_active);

-- DOWN (Rollback instructions)
-- To roll back this migration, run:
-- DROP INDEX IF EXISTS idx_auth_credentials_is_active;
-- DROP INDEX IF EXISTS idx_auth_credentials_provider_id;
-- DROP INDEX IF EXISTS idx_auth_credentials_user_id;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP INDEX IF EXISTS idx_users_username;
-- DROP TABLE IF EXISTS auth_credentials;
-- DROP TABLE IF EXISTS auth_providers;
-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS roles;

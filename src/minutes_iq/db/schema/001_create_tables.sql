-- =====================================================
-- Minutes IQ Database Schema (v1)
-- SQLite / Turso Compatible
-- =====================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Roles
-- -----------------------------------------------------
CREATE TABLE role (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- -----------------------------------------------------
-- Permissions
-- -----------------------------------------------------
CREATE TABLE permission (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- -----------------------------------------------------
-- Role-Permission Mapping
-- -----------------------------------------------------
CREATE TABLE role_permission (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES role(role_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (permission_id) REFERENCES permission(permission_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Users
-- -----------------------------------------------------
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    role_id INTEGER,
    provider_id INTEGER
);

-- -----------------------------------------------------
-- Auth Providers
-- -----------------------------------------------------
CREATE TABLE auth_providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_type TEXT NOT NULL,
    UNIQUE (user_id, provider_type),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Profiles
-- -----------------------------------------------------
DROP TABLE IF EXISTS profile;
CREATE TABLE profile (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Auth Credentials
-- -----------------------------------------------------
DROP TABLE IF EXISTS auth_credentials;
CREATE TABLE auth_credentials (
    auth_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provider_id, user_id),
    FOREIGN KEY (provider_id) REFERENCES auth_provider(provider_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Clients
-- -----------------------------------------------------
CREATE TABLE client (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Client Sources
-- -----------------------------------------------------
CREATE TABLE client_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    source_key TEXT NOT NULL,
    source_name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    index_url TEXT NOT NULL,
    archive_url TEXT,
    source_type TEXT NOT NULL,
    parser_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (client_id, source_key),
    FOREIGN KEY (client_id) REFERENCES client(client_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- User Client Favorites
-- -----------------------------------------------------
DROP TABLE IF EXISTS user_client_favorites;
CREATE TABLE user_client_favorites (
    user_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, client_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES client(client_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Saved Searches
-- -----------------------------------------------------
DROP TABLE IF EXISTS saved_searches;
CREATE TABLE saved_searches (
    saved_search_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, client_id, name),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES client(client_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Saved Search Sources
-- -----------------------------------------------------
CREATE TABLE saved_search_sources (
    saved_search_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    PRIMARY KEY (saved_search_id, source_id),
    FOREIGN KEY (saved_search_id) REFERENCES saved_searches(saved_search_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (source_id) REFERENCES client_sources(source_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Keywords
-- -----------------------------------------------------
CREATE TABLE keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Saved Search Keywords
-- -----------------------------------------------------
CREATE TABLE saved_search_keywords (
    saved_search_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    PRIMARY KEY (saved_search_id, keyword_id),
    FOREIGN KEY (saved_search_id) REFERENCES saved_searches(saved_search_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- =====================================================
-- End of Schema v1
-- =====================================================

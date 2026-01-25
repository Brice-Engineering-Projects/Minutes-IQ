-- Migration: Add Client and Keyword Management
-- Created: 2026-01-25
-- Purpose: Enable management of clients (government agencies), keywords, and user favorites
--
-- This migration creates tables for:
--   - clients: Government agencies/organizations being tracked
--   - keywords: Search terms used to filter meeting minutes
--   - client_keywords: Many-to-many relationship between clients and keywords
--   - user_client_favorites: User preferences for clients
--   - client_sources: URLs and data sources for each client

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

-- Table: clients
-- Represents government agencies or organizations being tracked
CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                -- Organization name (e.g., "JEA", "City of Jacksonville")
    description TEXT,                          -- Brief description of the organization
    website_url TEXT,                          -- Official website
    is_active INTEGER NOT NULL DEFAULT 1,     -- 1 = active, 0 = inactive
    created_at INTEGER NOT NULL,              -- Unix timestamp when client was added
    created_by INTEGER NOT NULL,              -- Admin user who added the client
    updated_at INTEGER,                        -- Unix timestamp of last update
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Table: keywords
-- Taxonomy of search terms for filtering meeting minutes
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,             -- The actual keyword/phrase
    category TEXT,                             -- Optional category (e.g., "Infrastructure", "Budget")
    description TEXT,                          -- What this keyword is used for
    is_active INTEGER NOT NULL DEFAULT 1,     -- 1 = active, 0 = deprecated
    created_at INTEGER NOT NULL,              -- Unix timestamp when keyword was added
    created_by INTEGER NOT NULL,              -- Admin user who added the keyword
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Table: client_keywords
-- Associates keywords with clients (many-to-many)
-- Defines which keywords are relevant for which clients
CREATE TABLE IF NOT EXISTS client_keywords (
    client_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    added_at INTEGER NOT NULL,                -- Unix timestamp when association was created
    added_by INTEGER NOT NULL,                -- Admin user who created the association
    PRIMARY KEY (client_id, keyword_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(user_id)
);

-- Table: user_client_favorites
-- User preferences for clients (many-to-many)
-- Allows users to mark clients as favorites for quick access
CREATE TABLE IF NOT EXISTS user_client_favorites (
    user_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    favorited_at INTEGER NOT NULL,           -- Unix timestamp when favorited
    PRIMARY KEY (user_id, client_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Table: client_sources
-- Data sources (URLs) for each client
-- Each client can have multiple sources (e.g., different meeting types)
CREATE TABLE IF NOT EXISTS client_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    source_name TEXT NOT NULL,                -- Descriptive name (e.g., "Board Meetings", "Public Hearings")
    source_url TEXT NOT NULL,                 -- URL to scrape
    source_type TEXT,                         -- Type of source (e.g., "agenda", "minutes", "video")
    is_active INTEGER NOT NULL DEFAULT 1,     -- 1 = active, 0 = inactive
    scrape_frequency TEXT,                    -- How often to scrape (e.g., "weekly", "monthly")
    last_scraped_at INTEGER,                  -- Unix timestamp of last successful scrape
    created_at INTEGER NOT NULL,              -- Unix timestamp when source was added
    created_by INTEGER NOT NULL,              -- Admin user who added the source
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Clients indexes
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);
CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_clients_created_by ON clients(created_by);

-- Keywords indexes
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
CREATE INDEX IF NOT EXISTS idx_keywords_is_active ON keywords(is_active);

-- Client-Keyword relationship indexes
CREATE INDEX IF NOT EXISTS idx_client_keywords_client_id ON client_keywords(client_id);
CREATE INDEX IF NOT EXISTS idx_client_keywords_keyword_id ON client_keywords(keyword_id);

-- User favorites indexes
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_client_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_client_id ON user_client_favorites(client_id);

-- Client sources indexes
CREATE INDEX IF NOT EXISTS idx_client_sources_client_id ON client_sources(client_id);
CREATE INDEX IF NOT EXISTS idx_client_sources_is_active ON client_sources(is_active);

-- ============================================================================
-- ROLLBACK MIGRATION
-- ============================================================================

-- To rollback this migration, run:
-- DROP INDEX IF EXISTS idx_client_sources_is_active;
-- DROP INDEX IF EXISTS idx_client_sources_client_id;
-- DROP INDEX IF EXISTS idx_user_favorites_client_id;
-- DROP INDEX IF EXISTS idx_user_favorites_user_id;
-- DROP INDEX IF EXISTS idx_client_keywords_keyword_id;
-- DROP INDEX IF EXISTS idx_client_keywords_client_id;
-- DROP INDEX IF EXISTS idx_keywords_is_active;
-- DROP INDEX IF EXISTS idx_keywords_category;
-- DROP INDEX IF EXISTS idx_keywords_keyword;
-- DROP INDEX IF EXISTS idx_clients_created_by;
-- DROP INDEX IF EXISTS idx_clients_is_active;
-- DROP INDEX IF EXISTS idx_clients_name;
-- DROP TABLE IF EXISTS client_sources;
-- DROP TABLE IF EXISTS user_client_favorites;
-- DROP TABLE IF EXISTS client_keywords;
-- DROP TABLE IF EXISTS keywords;
-- DROP TABLE IF EXISTS clients;

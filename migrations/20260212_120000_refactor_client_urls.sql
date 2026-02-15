-- Migration: Refactor Client URLs Architecture
-- Created: 2026-02-12
-- Purpose: Simplify client_sources table and migrate website_url from client table
--
-- Changes:
--   1. Rename client_sources to client_urls
--   2. Simplify schema: alias + url (remove base_url, index_url, archive_url, source_key, parser_type)
--   3. Migrate existing website_url from client table to client_urls
--   4. Remove website_url column from client table
--   5. Update scrape_jobs to reference client_url_id

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

-- Step 1: Create new client_urls table with simplified schema
CREATE TABLE IF NOT EXISTS client_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    alias TEXT NOT NULL,                      -- Descriptive name (e.g., "current", "archive", "board meetings")
    url TEXT NOT NULL,                        -- The actual URL to scrape
    is_active INTEGER NOT NULL DEFAULT 1,     -- 1 = active, 0 = inactive
    last_scraped_at INTEGER,                  -- Unix timestamp of last successful scrape
    created_at INTEGER NOT NULL,              -- Unix timestamp when URL was added
    updated_at INTEGER,                        -- Unix timestamp of last update
    FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE
);

-- Step 2: Migrate data from existing client_sources to client_urls
-- For each row in client_sources, create entries in client_urls
-- If index_url exists, create "current" entry
-- If archive_url exists, create "archive" entry
-- If base_url exists and is different from index/archive, create "base" entry

-- Step 3: Migrate website_url from client table to client_urls
-- For each client with a website_url, create a "default" entry
INSERT INTO client_urls (client_id, alias, url, is_active, created_at)
SELECT
    client_id,
    'default' as alias,
    website_url as url,
    1 as is_active,
    CAST(strftime('%s', 'now') AS INTEGER) as created_at
FROM client
WHERE website_url IS NOT NULL AND website_url != '';

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_client_urls_client_id ON client_urls(client_id);
CREATE INDEX IF NOT EXISTS idx_client_urls_is_active ON client_urls(is_active);
CREATE INDEX IF NOT EXISTS idx_client_urls_alias ON client_urls(alias);

-- Step 5: Drop old client_sources table
DROP TABLE IF EXISTS client_sources;

-- Step 6: Create temporary table to drop website_url column from client
CREATE TABLE client_new (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    updated_at INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Step 7: Copy data from old client table to new (without website_url)
INSERT INTO client_new (client_id, name, description, is_active, created_at, created_by, updated_at)
SELECT client_id, name, description, is_active, created_at, created_by, updated_at
FROM client;

-- Step 8: Drop old client table and rename new one
DROP TABLE client;
ALTER TABLE client_new RENAME TO client;

-- Step 9: Recreate client indexes
CREATE INDEX IF NOT EXISTS idx_client_name ON client(name);
CREATE INDEX IF NOT EXISTS idx_client_is_active ON client(is_active);
CREATE INDEX IF NOT EXISTS idx_client_created_by ON client(created_by);

-- ============================================================================
-- UPDATE SCRAPE_JOBS (if exists)
-- ============================================================================

-- Note: This will be handled in a separate step after verifying scrape_jobs schema
-- The scrape_jobs table should reference client_url_id instead of client_id

-- ============================================================================
-- ROLLBACK MIGRATION
-- ============================================================================

-- To rollback this migration:
-- 1. Recreate client table with website_url column
-- 2. Migrate "default" entries from client_urls back to client.website_url
-- 3. Drop client_urls table
-- 4. Recreate client_sources table with original schema

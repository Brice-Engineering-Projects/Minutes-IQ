-- =====================================================
-- 001_create_tables.sql
-- Canonical Minutes IQ schema (SQLite / Turso)
-- =====================================================

PRAGMA foreign_keys = ON;

-- Core identity tables
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    role_id INTEGER NOT NULL,
    force_password_change INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE IF NOT EXISTS auth_providers (
    provider_id INTEGER PRIMARY KEY,
    provider_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS auth_credentials (
    credential_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (provider_id) REFERENCES auth_providers(provider_id)
);

-- Registration authorization code flow
CREATE TABLE IF NOT EXISTS auth_codes (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    created_by INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS code_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    used_at INTEGER NOT NULL,
    FOREIGN KEY (code_id) REFERENCES auth_codes(code_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Password reset flow
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    used_at INTEGER,
    is_valid INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Client and keyword management
CREATE TABLE IF NOT EXISTS client (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    updated_at INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS client_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    url TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_scraped_at INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER,
    FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    category TEXT,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS client_keywords (
    client_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    added_at INTEGER NOT NULL,
    added_by INTEGER NOT NULL,
    PRIMARY KEY (client_id, keyword_id),
    FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS user_client_favorites (
    user_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    favorited_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, client_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE
);

-- Scraper orchestration
CREATE TABLE IF NOT EXISTS scrape_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_url_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    created_by INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    completed_at INTEGER,
    error_message TEXT,
    FOREIGN KEY (client_url_id) REFERENCES client_urls(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS scrape_job_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL UNIQUE,
    date_range_start TEXT,
    date_range_end TEXT,
    max_scan_pages INTEGER,
    include_minutes INTEGER NOT NULL DEFAULT 1,
    include_packages INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (job_id) REFERENCES scrape_jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scrape_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    pdf_filename TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    snippet TEXT NOT NULL,
    entities_json TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (job_id) REFERENCES scrape_jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE RESTRICT
);

-- =====================================================
-- 005_add_scraper_orchestration.sql
-- Scraper Orchestration Tables for Minutes IQ
-- SQLite / Turso Compatible
-- =====================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Scrape Jobs
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS scrape_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (client_id) REFERENCES client(client_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Scrape Job Configuration
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS scrape_job_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL UNIQUE,
    date_range_start TEXT,
    date_range_end TEXT,
    max_scan_pages INTEGER,
    include_minutes INTEGER NOT NULL DEFAULT 1,
    include_packages INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (job_id) REFERENCES scrape_jobs(job_id)
        ON DELETE CASCADE ON UPDATE RESTRICT
);

-- -----------------------------------------------------
-- Scrape Results
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS scrape_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    pdf_filename TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    snippet TEXT NOT NULL,
    entities_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES scrape_jobs(job_id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- =====================================================
-- End of 005_add_scraper_orchestration.sql
-- =====================================================

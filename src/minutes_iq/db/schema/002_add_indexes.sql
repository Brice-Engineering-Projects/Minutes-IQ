-- =====================================================
-- 002_add_indexes.sql
-- Canonical indexes for Minutes IQ
-- =====================================================

PRAGMA foreign_keys = ON;

-- Users / auth
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_auth_credentials_user_id ON auth_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_credentials_provider_id ON auth_credentials(provider_id);
CREATE INDEX IF NOT EXISTS idx_auth_credentials_is_active ON auth_credentials(is_active);

-- Authorization codes
CREATE INDEX IF NOT EXISTS idx_auth_codes_code ON auth_codes(code);
CREATE INDEX IF NOT EXISTS idx_auth_codes_is_active ON auth_codes(is_active);
CREATE INDEX IF NOT EXISTS idx_auth_codes_expires_at ON auth_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_codes_created_by ON auth_codes(created_by);
CREATE INDEX IF NOT EXISTS idx_code_usage_code_id ON code_usage(code_id);
CREATE INDEX IF NOT EXISTS idx_code_usage_user_id ON code_usage(user_id);

-- Password reset
CREATE INDEX IF NOT EXISTS idx_password_reset_token_hash ON password_reset_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_expires_at ON password_reset_tokens(expires_at);

-- Client / URL / keyword management
CREATE INDEX IF NOT EXISTS idx_client_name ON client(name);
CREATE INDEX IF NOT EXISTS idx_client_is_active ON client(is_active);
CREATE INDEX IF NOT EXISTS idx_client_created_by ON client(created_by);
CREATE INDEX IF NOT EXISTS idx_client_urls_client_id ON client_urls(client_id);
CREATE INDEX IF NOT EXISTS idx_client_urls_is_active ON client_urls(is_active);
CREATE INDEX IF NOT EXISTS idx_client_urls_alias ON client_urls(alias);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
CREATE INDEX IF NOT EXISTS idx_keywords_is_active ON keywords(is_active);
CREATE INDEX IF NOT EXISTS idx_client_keywords_client_id ON client_keywords(client_id);
CREATE INDEX IF NOT EXISTS idx_client_keywords_keyword_id ON client_keywords(keyword_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_client_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_client_id ON user_client_favorites(client_id);

-- Scraper orchestration
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_client_url_id ON scrape_jobs(client_url_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_created_by ON scrape_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_scrape_results_job_id ON scrape_results(job_id);
CREATE INDEX IF NOT EXISTS idx_scrape_results_keyword_id ON scrape_results(keyword_id);
CREATE INDEX IF NOT EXISTS idx_scrape_results_created_at ON scrape_results(created_at);

# README: Database Setup

## Database Architecture

Minutes IQ uses Turso (libSQL/SQLite-compatible) as its primary database.

Schema design philosophy:

- Keep the schema explicit and versioned through canonical SQL files.
- Keep initialization idempotent with `IF NOT EXISTS` and `INSERT OR IGNORE`.
- Separate concerns: table creation, index creation, and seed data.
- Preserve migration history for auditability while providing a single clean setup path.

Canonical schema files:

- `src/minutes_iq/db/schema/001_create_tables.sql`
- `src/minutes_iq/db/schema/002_add_indexes.sql`
- `src/minutes_iq/db/schema/003_seed_auth_providers.sql`

Optional runner script:

- `src/minutes_iq/db/setup_database.py`

## Setup Instructions

1. Install dependencies.

```bash
uv sync
```

1. Configure Turso credentials in your `.env` (used by app settings).

Required environment variables:

- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

1. Run schema setup.

```bash
uv run python src/minutes_iq/db/setup_database.py
```

1. Verify tables exist.

```bash
sqlite3 database.db ".tables"
```

If you are targeting Turso directly, you can also verify with your Turso SQL shell.

## Alternative: SQL-Only Setup

You can apply SQL files directly in order:

```bash
sqlite3 database.db < src/minutes_iq/db/schema/001_create_tables.sql
sqlite3 database.db < src/minutes_iq/db/schema/002_add_indexes.sql
sqlite3 database.db < src/minutes_iq/db/schema/003_seed_auth_providers.sql
```

## Schema Overview

| Table | Description |
| ------ | ----------- |
| roles | System roles (`admin`, `user`) |
| users | User identity and account state |
| auth_providers | Authentication provider registry |
| auth_credentials | Password credential records |
| auth_codes | Admin-generated registration authorization codes |
| code_usage | Usage audit for authorization codes |
| password_reset_tokens | Password reset token lifecycle |
| client | Client organizations managed in the app |
| client_urls | Scraping URLs per client |
| keywords | Keyword catalog |
| client_keywords | Client-to-keyword associations |
| user_client_favorites | User favorite clients |
| scrape_jobs | Scraper orchestration jobs |
| scrape_job_config | Per-job scraper options |
| scrape_results | Extracted keyword matches from documents |

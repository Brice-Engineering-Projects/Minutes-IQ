# Scripts Directory

This directory contains utility scripts for database migrations and administrative tasks.

## Directory Structure

```
scripts/
├── migrations/          # Database migration scripts
├── admin/              # Administrative utility scripts
└── archive/            # Deprecated/one-off scripts (kept for reference)
```

## Migrations

Migration scripts are located in `scripts/migrations/` and should be run in order.

### Running Migrations

```bash
# From project root
uv run python scripts/migrations/run_client_urls_migration.py
```

### Available Migrations

- `run_client_keyword_migration.py` - Initial client/keyword management setup
- `run_client_urls_migration.py` - Refactor to multi-URL client architecture

## Admin Scripts

Administrative utilities are located in `scripts/admin/`.

```bash
# Check admin users
uv run python scripts/admin/check_admin.py
```

## Archive

The `archive/` directory contains one-off scripts and deprecated utilities kept for reference. These should not be used in production.

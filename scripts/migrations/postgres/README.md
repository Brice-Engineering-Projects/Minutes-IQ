# PostgreSQL Migration Scripts (SQLAlchemy)

This folder contains a SQLAlchemy Core-based bootstrap for creating the Minutes IQ schema in PostgreSQL.

## Files

- `sqlalchemy_schema.py` - Canonical table/index definitions and seed data logic.
- `create_postgres_db.py` - CLI runner to create database objects in PostgreSQL.
- `migrate_sqlite_to_postgres.py` - Data-only migration from SQLite/libSQL export into PostgreSQL.

## Workflow

1. Create schema objects (tables, constraints, indexes).
2. Migrate data with the dedicated data script.

Schema creation and data migration are intentionally separated.

## Prerequisites

Install dependencies if they are not already available:

```bash
uv pip install "sqlalchemy>=2.0" "psycopg[binary]>=3.1"
```

## Usage

Set your target DB URL:

```bash
export MINUTESIQ_POSTGRES_URL="postgresql+psycopg://user:password@host:5432/minutesiq"
```

Create tables/indexes and seed baseline data:

```bash
uv run python scripts/migrations/postgres/create_postgres_db.py
```

Optional flags:

```bash
# Create in non-public schema
uv run python scripts/migrations/postgres/create_postgres_db.py --schema minutesiq

# Drop and recreate all objects (dangerous)
uv run python scripts/migrations/postgres/create_postgres_db.py --drop-existing

# Skip seed rows (roles/auth_providers)
uv run python scripts/migrations/postgres/create_postgres_db.py --skip-seed

# Create DB first if missing (requires admin URL + DB name)
uv run python scripts/migrations/postgres/create_postgres_db.py \
  --database-url "$MINUTESIQ_POSTGRES_URL" \
  --create-db-if-missing \
  --admin-url "postgresql+psycopg://user:password@host:5432/postgres" \
  --db-name "minutesiq"
```

## Data Migration (SQLite/libSQL -> PostgreSQL)

Set source and target environment variables:

```bash
export MINUTESIQ_SOURCE_SQLITE_PATH="/path/to/minutesiq.sqlite"
export MINUTESIQ_POSTGRES_URL="postgresql+psycopg://user:password@host:5432/minutesiq"
```

Run migration:

```bash
uv run python scripts/migrations/postgres/migrate_sqlite_to_postgres.py
```

Optional flags:

```bash
# Truncate target tables before copy
uv run python scripts/migrations/postgres/migrate_sqlite_to_postgres.py --truncate-target

# Use custom schema and batch size
uv run python scripts/migrations/postgres/migrate_sqlite_to_postgres.py \
  --schema public \
  --batch-size 2000
```

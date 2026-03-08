# AI Assistant Task: Consolidate and Clean Database Schema

## Objective

The project has reached MVP stability, but the database schema evolved through multiple experimental scripts and migrations.

Your task is to audit the existing database-related files and produce a clean, reproducible schema setup so that a new developer can create the same database structure that currently exists in production.

The final result should allow a developer to run one clear setup process and obtain the correct database schema.

This project uses Turso (SQLite-compatible) as the database.

---

## Files and Directories to Review

## 1. Current Schema Folder

src/minutes_iq/db/schema/

This folder contains SQL files intended to represent the database schema.

Determine:

- Which files are actually needed
- Which are outdated or superseded
- Whether they accurately reflect the current database state

---

## 2. Archived Script Folder

root/scripts/archive/

This directory contains older scripts and experiments used during development.

These may include:

- one-off schema changes
- test migrations
- temporary scripts

Use these files only to understand how the schema evolved, not as the final schema.

---

## 3. Migration Scripts

root/scripts/migrations/

This directory may contain scripts that:

- added new columns
- modified tables
- added indexes
- altered constraints

Determine whether these migrations introduced schema changes that must now be incorporated into the canonical schema definition.

---

## Required Tasks

## 1. Reconstruct the Final Schema

Using all files above, determine the actual current database schema, including:

- Tables
- Columns
- Column types
- Constraints
- Foreign keys
- Indexes
- Default values

The final schema should match the current working database structure.

---

## 2. Create a Canonical Schema Setup

Create a clean database initialization system.

Preferred structure:

src/minutes_iq/db/schema/
    001_create_tables.sql
    002_add_indexes.sql
    003_seed_auth_providers.sql

Optionally create:

src/minutes_iq/db/setup_database.py

This script should execute schema SQL files in the correct order.

---

## 3. Remove Schema Drift

Ensure the final schema:

- contains all required tables
- includes all necessary indexes
- includes all foreign key constraints
- includes any seed data required for authentication or system operation

---

## 4. Archive Obsolete Files

Move any unnecessary or outdated files into:

root/scripts/archive/old_db_scripts/

Examples of files to archive:

- outdated migrations
- temporary schema changes
- one-time patch scripts
- experimental SQL files

After cleanup, only the canonical schema setup files should remain in:

src/minutes_iq/db/schema/

---

## 5. Ensure Idempotency

The schema setup should be safe to run on an empty database.

Example:

CREATE TABLE IF NOT EXISTS ...
CREATE INDEX IF NOT EXISTS ...

---

## Deliverables

## 1. Final Schema Files

Located in:

src/minutes_iq/db/schema/

These must represent the true database structure.

---

## 2. Database Setup Script (Optional)

src/minutes_iq/db/setup_database.py

This script should:

- connect to Turso
- execute schema SQL files
- initialize the database

---

## 3. README_db_setup.md

Create documentation at:

docs/08_database/README_db_setup.md

This file must explain:

### Database Architecture

- Turso usage
- schema design philosophy

### Setup Instructions

Example workflow:

1. Install dependencies
2. Configure Turso credentials
3. Run schema setup
4. Verify database creation

Example commands:

uv run python src/minutes_iq/db/setup_database.py

or

sqlite3 database.db < src/minutes_iq/db/schema/001_create_tables.sql

---

## 4. Schema Overview

The README should include a table overview similar to:

| Table | Description |
| ------ | ------------- |
| users | Authentication and account management |
| clients | Client organizations |
| keywords | Tracked keywords for minutes analysis |
| reports | Generated analysis reports |

---

## Important Constraints

You must:

- Preserve the current working database structure
- Avoid introducing schema changes unless necessary
- Ensure the schema is fully reproducible
- Keep the structure simple and developer-friendly

---

## Final Goal

After this task, a developer should be able to clone the repository and run one simple setup process to produce the exact database schema used by the application.

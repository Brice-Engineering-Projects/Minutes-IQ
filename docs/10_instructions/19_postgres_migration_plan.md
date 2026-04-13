# 📄 MinutesIQ – PostgreSQL Migration Plan

## 🎯 Objective

Migrate MinutesIQ from Turso/libSQL to PostgreSQL using SQLAlchemy Core as the canonical schema definition, ensuring a clean, reproducible, and production-ready backend setup.

---

## 🧠 Architectural Decisions

### 1. Schema Location

* Use PostgreSQL **`public` schema** for now
* Rationale:

  * Simplicity
  * Compatibility with tools
  * Avoid premature complexity

---

### 2. Source of Truth

* **SQLAlchemy Core schema (`sqlalchemy_schema.py`) is the single source of truth**
* Do NOT rely on:

  * Turso/libSQL schema
  * Ad hoc SQL scripts
  * Manual DB edits

---

### 3. Separation of Concerns

#### ✅ Schema Creation

Handled by:

```text
create_postgres_db.py
```

Purpose:

* Create tables, constraints, indexes
* Seed baseline data
* Safe to re-run (`checkfirst=True`)

---

#### ⚠️ Data Migration (Separate Script Required)

Create a new script:

```text
migrate_sqlite_to_postgres.py
```

Purpose:

* Extract data from existing database (Turso/libSQL/SQLite)
* Transform if needed
* Insert into PostgreSQL

**Important:**

* DO NOT combine schema creation and data migration
* Keep responsibilities isolated for clarity and debugging

---

### 4. Dependency Management

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    "sqlalchemy",
    "psycopg[binary]"
]
```

Rationale:

* Migration tooling should align with application stack
* Avoid maintaining separate dependency environments

---

## ⚙️ Execution Plan

### Step 1 — Bootstrap PostgreSQL Schema

Set environment variable:

```bash
export MINUTESIQ_POSTGRES_URL="postgresql+psycopg://user:password@localhost/dbname"
```

Run:

```bash
uv run python create_postgres_db.py
```

Validate:

* Tables exist
* Indexes created
* Seed data inserted:

  * `roles`: admin, user
  * `auth_providers`: password

---

### Step 2 — Validate Connection (Read-Only)

* Connect application to PostgreSQL
* Perform read queries only
* Confirm:

  * Schema alignment
  * No runtime errors

---

### Step 3 — Implement Data Migration Script

Create:

```text
migrate_sqlite_to_postgres.py
```

High-level flow:

```python
# Pseudocode

connect_to_source_db()
connect_to_postgres()

for table in tables:
    data = extract_data(table)
    transformed = transform_if_needed(data)
    insert_into_postgres(transformed)
```

Validation:

* Row counts match between source and target
* Key constraints are preserved

---

### Step 4 — Switch Application Write Path

* Update backend to write to PostgreSQL
* Ensure:

  * Inserts work
  * Updates work
  * Relationships are intact

---

### Step 5 — Decommission Turso/libSQL

* Remove dependency
* Remove connection logic
* Archive legacy data if needed

---

## ⚠️ Critical Guidelines

### Idempotency

* Keep `checkfirst=True` in schema creation
* Script must be safe to run multiple times

---

### Do NOT:

* Mix schema creation and data migration logic
* Hardcode credentials
* Manually modify database outside schema definition

---

### Validate Backups Before Migration

* Ensure existing data is backed up
* Confirm restore capability

---

## 🧩 Future Enhancements (Optional)

* Add schema versioning (Alembic)
* Introduce named schemas if multi-tenant needs arise
* Automate migration as part of CI/CD pipeline

---

## 🏁 Summary

This migration establishes:

* PostgreSQL as the primary data store
* SQLAlchemy Core as the schema authority
* A clean separation between:

  * schema creation
  * data migration
  * application runtime

The goal is not just migration, but a **stable, production-ready backend foundation**.

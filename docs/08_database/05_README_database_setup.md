# 🗄️ Database Setup & Seeding Guide (Turso / SQLite)

This document describes **how to create, initialize, and seed** the JEA Web Scraper
database using **Turso** and the SQL schema files in this repository.

This is the **authoritative operational guide** for database setup.

---

## 1. Prerequisites

Before starting, ensure you have:

- A Turso account
- Turso CLI installed
- Access to this repository
- The following directory structure:

```
db/schema/
├── 001_create_tables.sql
├── 002_add_indexes.sql
└── 003_seed_auth_providers.sql
```

Verify Turso installation:

```bash
turso --version
```

---

## 2. Create the Turso Database

Create a new database (example name shown):

```bash
turso db create jea-web-scraper
```

Confirm it exists:

```bash
turso db list
```

---

## 3. Connect to the Database Shell

Open an interactive SQLite shell:

```bash
turso db shell jea-scraper
```

Ensure foreign key enforcement is enabled:

```sql
PRAGMA foreign_keys;
```

Expected output:
```
1
```

If not:

```sql
PRAGMA foreign_keys = ON;
```

---

## 4. Create Database Tables

From the Turso shell, apply the schema:

```sql
.read db/schema/001_create_tables.sql
```

This will:
- Create all tables
- Define primary keys
- Define foreign keys with `RESTRICT`
- Apply UNIQUE constraints

Verify tables:

```sql
.tables
```

---

## 5. Create Initial Admin User (Manual Step)

Before seeding authentication providers, create **at least one admin user**.

Example (adjust values as needed):

```sql
INSERT INTO users (username, email, phone, role_id, provider_id)
VALUES ('admin', 'admin@example.com', '555-555-5555', NULL, NULL);
```

> 🔐 Passwords are **not** stored here.  
> Credentials are added in `auth_credentials`.

---

## 6. Seed Authentication Providers

Once an admin user exists, seed authentication providers.

Edit `003_seed_auth_providers.sql` if necessary to reference the correct `user_id`.

Then run:

```sql
.read db/schema/003_seed_auth_providers.sql
```

Typical providers:
- `local`
- (future) `google`, `github`, etc.

---

## 7. Seed Authentication Credentials (Optional)

Example for local auth:

```sql
INSERT INTO auth_credentials (provider_id, user_id, hashed_password)
VALUES (1, 1, '<bcrypt_hash>');
```

Example of how to hash a password:

```python
import bcrypt

password = b"YourStrongAdminPasswordHere"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())
```

> ⚠️ Passwords must already be hashed (bcrypt).

---

## 8. Apply Indexes

Indexes may be applied at any time **after tables exist**.

```sql
.read db/schema/002_add_indexes.sql
```

Indexes are safe to re-run due to `IF NOT EXISTS`.

---

## 9. Verify Database State

Recommended verification checks:

```sql
-- List users
SELECT * FROM user;

-- List auth providers
SELECT * FROM auth_provider;

-- Check foreign keys
PRAGMA foreign_key_check;
```

Expected:
- No foreign key violations
- Admin user present
- At least one auth provider

---

## 10. Resetting the Database (Development Only)

⚠️ **Destructive operation**

```bash
turso db destroy jea-web-scraper
```

Then repeat setup steps.

---

## 11. Design Principles Recap

- Schema is defined in SQL (source of truth)
- Foreign keys use `RESTRICT`
- Indexes are intentional and minimal
- Seeding is controlled and explicit
- No silent cascading deletes

---

## 12. Next Steps

Once the database is ready:

- Wire SQLAlchemy / SQLModel
- Implement admin bootstrap flow
- Add role & permission seeding
- Integrate auth into FastAPI

---

## Status

- **Schema:** v1 (locked)
- **Database:** Turso / SQLite
- **Operational maturity:** Production-ready foundation

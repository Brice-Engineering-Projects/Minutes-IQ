# 🗄️ Database Schema — JEA / Municipal Intelligence Dashboard

## Purpose
This document defines the database schema for the FastAPI-based municipal meeting intelligence platform.
The schema is intentionally **lean**, **secure**, and **admin-controlled**, designed for a small internal user base with a clean scaling path.

---

## Design Principles

- Email-based authentication
- JWT for sessions, bcrypt for passwords
- Admin-controlled data integrity
- Shared client pool + per-user favorites
- No scraper outputs stored in DB
- SQLite-compatible (Turso)

---

## Core Tables Overview

| Table | Purpose |
|-----|--------|
| users | Authentication & access control |
| profiles | User identity & metadata |
| auth_codes | Controlled registration |
| clients | Municipal agencies / entities |
| client_sources | Websites/endpoints per client |
| user_client_favorites | Per-user shortcuts |
| password_reset_tokens | Secure password recovery |

---

## 1. users

Handles authentication and authorization.

```sql
users
-----
id (uuid, pk)
email (text, unique, not null)
password_hash (text, not null)
is_active (boolean, default true)
is_admin (boolean, default false)
created_at (timestamp)
```

Notes:
- Email is the login identifier
- Passwords stored using bcrypt hash
- `is_admin` controls data mutation rights

---

## 2. profiles

Stores non-auth user information.

```sql
profiles
--------
user_id (uuid, pk, fk -> users.id)
first_name (text)
last_name (text)
job_title (text)
```

Notes:
- 1:1 relationship with users
- Keeps auth table clean

---

## 3. auth_codes

Controls who may register.

```sql
auth_codes
----------
code (char(6), pk)
is_active (boolean)
created_at (timestamp)
expires_at (timestamp, nullable)
```

Notes:
- 6-digit numeric codes
- Rotatable
- Can be single-use or reusable

---

## 4. clients

Represents agencies/entities (JEA, Tampa, Miami, etc.).

```sql
clients
-------
id (uuid, pk)
name (text, unique)
is_active (boolean, default true)
created_at (timestamp)
```

Example values:
- JEA
- City of Jacksonville
- Tampa
- Palm Coast
- SFWMD

---

## 5. client_sources

Defines where and how scraping occurs for each client.

```sql
client_sources
--------------
id (uuid, pk)
client_id (uuid, fk -> clients.id)
source_name (text)
base_url (text)
source_type (text) -- pdf, html, mixed
is_active (boolean)
```

Notes:
- One client can have multiple sources
- Allows testing without affecting production scrapes

---

## 6. user_client_favorites

User-specific shortcuts to clients.

```sql
user_client_favorites
---------------------
user_id (uuid, fk -> users.id)
client_id (uuid, fk -> clients.id)
PRIMARY KEY (user_id, client_id)
```

Notes:
- Does NOT affect global client pool
- Only affects UI filtering

---

## 7. password_reset_tokens

Secure password recovery.

```sql
password_reset_tokens
---------------------
id (uuid, pk)
user_id (uuid, fk -> users.id)
token_hash (text)
expires_at (timestamp)
used (boolean, default false)
```

Notes:
- Tokens are hashed
- Single-use
- Short-lived

---

## Admin-Only Data Mutation Policy

### Why Only Admins Can Add Clients

Allowing unrestricted client creation would:
- Break scraping logic
- Introduce malformed URLs
- Cause runtime failures
- Reduce trust in the tool

Scraping sources are **not generic inputs** — each requires:
- Structure validation
- Keyword coverage testing
- PDF handling checks
- Regression testing

### Policy Decision

| Action | Who |
|-----|----|
| Add / edit clients | Admin only |
| Add / edit sources | Admin only |
| Enable / disable client | Admin only |
| Select favorites | Any user |
| Submit scrape jobs | Any user |

### User Request Flow (Future)
1. User submits client request (name + URL)
2. Admin reviews & tests
3. Admin adds to DB
4. Client enabled for all users

---

## Scaling Forward

If adoption grows:
- Replace auth_codes with invite tokens
- Replace Turso with Postgres
- Add audit logs
- Add admin UI panel

---

**Guiding Rule:**  
> _If bad data can break the app, only admins can write it._

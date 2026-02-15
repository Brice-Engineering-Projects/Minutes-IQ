# Minutes IQ – Multi-URL Client Architecture Update

## 📌 Problem Statement

The current schema assumes each client has a single `website_url`.

Real-world use cases (e.g., JEA) require:
- One URL for current meetings
- One URL for archived meetings
- Potentially additional URLs for boards, committees, procurement, etc.

Therefore:

**A client must support multiple URLs, each with its own alias and lifecycle.**

---

# 🎯 Architectural Decision

Replace single `website_url` field with a dedicated `client_urls` table.

This introduces a proper 1-to-many relationship:

- One client → Many URLs

This supports:
- Multiple scrape targets per client
- URL-level tracking
- Future scheduling & analytics
- Cleaner relational design

---

# 🧱 Proposed Database Schema

## 1️⃣ `clients` Table

| Field | Type | Notes |
|-------|------|-------|
| id | PK | Primary key |
| name | string | Client name |
| description | string | Optional |
| is_active | boolean | Soft enable/disable |
| created_at | timestamp | |
| updated_at | timestamp | |

Remove:
- ❌ `website_url`

---

## 2️⃣ `client_urls` Table

| Field | Type | Notes |
|-------|------|-------|
| id | PK | Primary key |
| client_id | FK → clients.id | Relationship |
| alias | string | e.g. "current", "archive", "board meetings" |
| url | string | Actual URL |
| is_active | boolean | Enables/disables scraping |
| last_scraped_at | timestamp | Optional |
| created_at | timestamp | |
| updated_at | timestamp | |

This enables:
- Multiple URLs per client
- Named scrape targets
- URL-level lifecycle tracking

---

## 3️⃣ `scrape_jobs` Table (Update)

Instead of referencing `client_id`, reference `client_url_id`.

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| client_url_id | FK → client_urls.id | Specific URL scraped |
| status | string | pending / running / complete / failed |
| started_at | timestamp | |
| completed_at | timestamp | |
| result_path | string | Annotated PDF output |

This ensures:
- Exact traceability of what was scraped
- Proper job auditing
- URL-specific failure tracking

---

# 🖥️ UI Changes Required

## Client Management
- Client form must allow adding multiple URLs
- URL entries require:
  - alias
  - URL
  - active toggle
- Support edit/delete per URL

## Scraper Job Creation
- User selects:
  - Client
  - Specific Client URL (by alias)

---

# 🔄 Migration Plan

1. Create `client_urls` table
2. Migrate existing `website_url` values into `client_urls`
   - alias = "default"
   - is_active = true
3. Drop `website_url` column from `clients`
4. Update foreign key references in `scrape_jobs`
5. Update forms and API endpoints

---

# 🚀 Long-Term Benefits

This design supports:

- URL-specific scheduling
- Parallel scraping
- URL-level analytics
- Failure monitoring
- Retry logic per URL
- Cleaner scaling model

---

# 🧠 Design Principle

Do not keep `website_url` for backward compatibility.

This project is still in development.
Avoid carrying legacy schema forward.

Build it correctly now.

---

# ✅ Final Decision Summary

- ✔ Create `client_urls` table
- ✔ Remove `website_url` from clients
- ✔ Update scrape_jobs to reference client_url_id
- ✔ Update UI to manage multiple URLs
- ✔ Migrate existing data
